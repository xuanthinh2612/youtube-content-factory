import asyncio
import json
import re

import httpx

from core.config import settings
from observability.telemetry import telemetry
from observability.usage import usage_tracker


class LLMClient:
    def __init__(self):
        self._client=None
        self._sem=None

    def _semaphore(self):
        if self._sem is None:
            self._sem=asyncio.Semaphore(max(1,int(settings.max_concurrent_llm_calls)))
        return self._sem

    def _http(self):
        if self._client is None or self._client.is_closed:
            limits=httpx.Limits(max_connections=max(8,int(settings.max_concurrent_llm_calls)*2),
                max_keepalive_connections=max(4,int(settings.max_concurrent_llm_calls)))
            self._client=httpx.AsyncClient(timeout=300,limits=limits,http2=False)
        return self._client

    async def close(self):
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    @staticmethod
    def _usage_labels(user):
        match=re.search(r"(?im)^(?:LANG|LANGUAGE|TARGET_LANGUAGE):\s*([^\n(]+)",user or "")
        return match.group(1).strip() if match else ""

    async def _one_call(self,model,system,user,temperature,max_tokens,node,retry_count):
        payload={"model":model,"messages":[{"role":"system","content":system},
            {"role":"user","content":user}],"temperature":temperature,"max_tokens":max_tokens}
        headers={"Authorization":f"Bearer {settings.llm_api_key}","Content-Type":"application/json"}
        async with self._semaphore():
            endpoint=settings.llm_url().rstrip("/")+"/chat/completions"
            try:
                response=await self._http().post(endpoint,headers=headers,json=payload)
            except httpx.ConnectError as exc:
                raise RuntimeError(f"Cannot connect to the configured LLM gateway at {endpoint}") from exc
            response.raise_for_status()
            try:
                data=response.json()
            except json.JSONDecodeError as exc:
                raise RuntimeError("LLM gateway returned an invalid JSON HTTP response") from exc
        usage=data.get("usage") or {}
        usage_tracker.add(model,usage.get("prompt_tokens",0),usage.get("completion_tokens",0),
            node=node,context_chars=len(system or "")+len(user or ""),retry_count=retry_count,
            language=self._usage_labels(user))
        choices=data.get("choices")
        message=(choices[0].get("message") if choices and isinstance(choices[0],dict) else None)
        if not isinstance(message,dict):
            raise RuntimeError("LLM gateway response is missing choices[0].message")
        content=message.get("content","")
        if isinstance(content,str):
            return content
        if isinstance(content,list):
            return "".join(item if isinstance(item,str) else item.get("text","")
                for item in content if isinstance(item,str) or isinstance(item,dict))
        if isinstance(content,dict):
            return str(content.get("text") or content.get("content") or "")
        return str(content or "")

    async def chat(self,tier,system,user,temperature=.2,max_tokens=7000,node="llm"):
        models=[]
        for current_tier in settings.fallback_tiers(tier):
            model=settings.model_for_tier(current_tier)
            if model not in models:
                models.append(model)
        last_error=None
        retry_count=0
        for model_index,model in enumerate(models):
            if model_index:
                await telemetry.fallback(node,models[model_index-1],model,reason=str(last_error))
            for attempt in range(1,settings.cap_rounds(settings.llm_retry_attempts)+1):
                try:
                    return await self._one_call(model,system,user,temperature,max_tokens,node,retry_count)
                except Exception as exc:
                    last_error=exc
                    await telemetry.retry(node,attempt,settings.cap_rounds(settings.llm_retry_attempts),
                        reason=f"model={model}: {type(exc).__name__}: {exc}")
                    retry_count+=1
                    if attempt<settings.cap_rounds(settings.llm_retry_attempts):
                        await asyncio.sleep(min(2**(attempt-1),8))
        raise last_error or RuntimeError("LLM request failed")


llm=LLMClient()
