from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime,timezone
from urllib.parse import urlsplit,urlunsplit

import httpx

from core.config import settings
from core.llm.client import llm
from core.llm.structured import STRICT_JSON_CONTRACT,StructuredOutputError,parse_json_object
from observability.telemetry import telemetry
from observability.usage import usage_tracker


@dataclass
class NativeSearchResponse:
    data: dict
    citations: list[dict]
    model: str
    provider_mode: str


def _content_text(value):
    """Extract text blocks from OpenAI-compatible multipart message content."""
    if isinstance(value,str):
        return value
    if isinstance(value,list):
        parts=[part for item in value if (part:=_content_text(item)) is not None]
        return "".join(part for part in parts if part)
    if isinstance(value,dict):
        for key in ("text","content","output_text"):
            part=value.get(key)
            if isinstance(part,str):
                return part
            if isinstance(part,(dict,list)):
                extracted=_content_text(part)
                if extracted is not None:
                    return extracted
    return None


def canonical_url(value:str)->str:
    try:
        p=urlsplit(str(value or "").strip())
        if p.scheme not in ("http","https") or not p.netloc:
            return ""
        return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip("/") or "/",p.query,""))
    except Exception:
        return ""


def citation_rows(payload:dict,message:dict,mode:str)->list[dict]:
    raw=[]
    raw.extend(payload.get("citations") or [])
    raw.extend(message.get("citations") or [])
    for item in message.get("annotations") or []:
        if isinstance(item,dict):
            raw.append(item.get("url_citation") or item)
    rows=[];seen=set()
    for index,item in enumerate(raw,1):
        if isinstance(item,str):
            item={"url":item}
        if not isinstance(item,dict):
            continue
        nested=item.get("url_citation") if isinstance(item.get("url_citation"),dict) else item
        url=canonical_url(nested.get("url") or nested.get("link") or "")
        if not url or url in seen:
            continue
        seen.add(url)
        rows.append({
            "source_id":f"S{len(rows)+1}","title":str(nested.get("title") or ""),
            "url":url,"provider":mode,
            "publisher":str(nested.get("publisher") or nested.get("source") or ""),
            "published_at":nested.get("published_at") or nested.get("publication_time"),
            "updated_at":nested.get("updated_at"),"event_time":nested.get("event_time"),
            "provider_citation_id":str(nested.get("id") or item.get("id") or f"citation_{index}"),
            "snippet":str(nested.get("snippet") or nested.get("text") or "")[:1600],
            "retrieved_at":datetime.now(timezone.utc).isoformat(),
        })
    return rows


class NativeWebSearch:
    def mode(self)->str:
        mode=(settings.native_web_search_mode or "").strip().lower()
        if mode in {"xai_chat","openai_chat"}:
            return mode
        if mode in {"off","disabled","none",""}:
            return "disabled"
        if mode=="auto":
            host=(urlsplit(settings.native_web_search_url()).hostname or "").lower()
            if host.endswith("api.openai.com"):
                return "openai_chat"
            if host.endswith("api.x.ai"):
                return "xai_chat"
            if host in {"127.0.0.1","localhost","host.docker.internal"}:
                return "xai_chat"
        return "disabled"

    async def _call(self,model,system,user,max_tokens,node,mode,retry_count=0):
        payload={
            "model":model,
            "messages":[{"role":"system","content":system+STRICT_JSON_CONTRACT},{"role":"user","content":user}],
            "temperature":.1,"max_tokens":max_tokens,"response_format":{"type":"json_object"},
        }
        if mode=="xai_chat":
            payload["search_parameters"]={"mode":"on","return_citations":True,
                "max_search_results":int(settings.native_web_search_max_results)}
        elif mode=="openai_chat":
            payload["web_search_options"]={"search_context_size":settings.native_web_search_context_size}
        else:
            raise RuntimeError("NATIVE_WEB_SEARCH_DISABLED")
        headers={"Authorization":f"Bearer {settings.native_web_search_key()}","Content-Type":"application/json"}
        endpoint=settings.native_web_search_url().rstrip("/")+"/chat/completions"
        async with llm._semaphore():
            response=await llm._http().post(endpoint,headers=headers,json=payload)
            response.raise_for_status()
            body=response.json()
        choices=body.get("choices") if isinstance(body,dict) else None
        message=(choices[0].get("message") or {}) if choices and isinstance(choices[0],dict) else {}
        content=message.get("content","")
        if not isinstance(content,str):
            content=_content_text(content)
            if content is None:
                content=json.dumps(message.get("content"),ensure_ascii=False)
        usage=body.get("usage") or {}
        language,unit=llm._usage_labels(user)
        usage_tracker.add(model,usage.get("prompt_tokens",0),usage.get("completion_tokens",0),node=node,
            context_chars=len(system or "")+len(user or ""),retry_count=retry_count,
            language=language,unit=unit)
        return content,citation_rows(body,message,mode)

    async def search_json(self,*,tier,system,user,node,error_code,required_keys=(),schema=None,
                          model_type=None,invalid_output_code="NATIVE_WEB_SEARCH_OUTPUT_INVALID",
                          root_list_field="",root_list_defaults=None,max_tokens=12000):
        mode=self.mode()
        if mode=="disabled":
            raise RuntimeError(f"{error_code}: configure a search-capable native web-search endpoint/model")
        primary_model=settings.native_web_search_model or settings.model_for_tier(tier)
        models=list(dict.fromkeys(x for x in (primary_model,settings.native_web_search_fallback_model) if x))
        if schema is None and model_type is not None:
            schema=model_type.model_json_schema()
        schema_contract=""
        if schema:
            schema_contract=(
                "\n\nMANDATORY RESPONSE JSON SCHEMA:\n"+json.dumps(schema,ensure_ascii=False,separators=(",",":"))+
                "\nThe response root MUST be one object matching this schema. NEVER return the root as an array. "
                "Do not rename keys, add wrapper keys, or substitute aliases."
            )
        search_system=system+schema_contract
        last_error=None
        retries=settings.cap_rounds(settings.llm_retry_attempts)
        total_retries=0
        await telemetry.node_start(node,f"model={primary_model}; native-web-search={mode}")
        for model_index,model in enumerate(models):
            for attempt in range(1,retries+1):
                try:
                    retry_instruction=""
                    if last_error is not None:
                        retry_instruction=(
                            "\n\nCORRECTION REQUIRED: Your previous response failed validation: "
                            f"{type(last_error).__name__}: {last_error}. Return the COMPLETE corrected root object, "
                            "not an array and not a partial fragment."
                        )
                    text,citations=await self._call(model,search_system,user+retry_instruction,max_tokens,node,mode,total_retries)
                    if settings.native_web_search_require_citations and not citations:
                        raise RuntimeError("provider returned no traceable native-search citations")
                    data=parse_json_object(text,required_keys,schema,
                        list_field=root_list_field,list_defaults=root_list_defaults)
                    if model_type is not None:
                        data=model_type.model_validate(data).model_dump()
                    await telemetry.node_success(node,f"{len(citations)} native citations")
                    return NativeSearchResponse(data=data,citations=citations,model=model,provider_mode=mode)
                except (httpx.HTTPError,StructuredOutputError,RuntimeError,ValueError) as exc:
                    last_error=exc
                    total_retries+=1
                    await telemetry.retry(node,attempt,retries,reason=f"native web search ({model}): {type(exc).__name__}: {exc}")
            if model_index+1<len(models):
                await telemetry.step(node,"fallback",f"Switching to configured search-capable model {models[model_index+1]}")
        await telemetry.node_error(node,last_error or RuntimeError(error_code))
        code=invalid_output_code if isinstance(last_error,(StructuredOutputError,ValueError)) else error_code
        raise RuntimeError(f"{code}: {last_error}") from last_error


native_web_search=NativeWebSearch()
