"""Read-only runtime preflight for local/Docker configuration dependencies."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from core.config import settings
from core.llm.web_search import native_web_search


async def main():
    failures=[]
    configured_models={settings.model_fast,settings.model_middle,settings.model_hard}
    placeholders={"fast-model","middle-model","hard-model","your-fast-model","your-middle-model","your-hard-model"}
    if not settings.llm_api_key or settings.llm_api_key=="change-me":
        failures.append("LLM_API_KEY is not configured")
    if configured_models & placeholders:
        failures.append("one or more MODEL_* values are still placeholders")

    base=settings.llm_url().rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response=await client.get(
                base+"/models",
                headers={"Authorization":f"Bearer {settings.llm_api_key}"},
            )
            response.raise_for_status()
            payload=response.json()
        available={str(x.get("id")) for x in payload.get("data",[]) if isinstance(x,dict) and x.get("id")}
        missing=sorted(configured_models-available) if available else []
        if missing:
            failures.append("configured model IDs are absent from /models: "+", ".join(missing))
        print(f"LLM gateway: OK ({base}; {len(available)} model(s) reported)")
    except Exception as exc:
        failures.append(f"LLM gateway unavailable at {base}: {type(exc).__name__}: {exc}")

    native_mode=native_web_search.mode()
    native_model=settings.native_web_search_model or settings.model_hard
    if native_mode=="disabled":
        failures.append("native Fact/News web search is disabled or endpoint mode cannot be inferred")
    else:
        native_base=settings.native_web_search_url().rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response=await client.get(native_base+"/models",headers={"Authorization":f"Bearer {settings.native_web_search_key()}"})
                response.raise_for_status();native_payload=response.json()
            native_models={str(x.get("id")) for x in native_payload.get("data",[]) if isinstance(x,dict) and x.get("id")}
            required={native_model}
            if settings.native_web_search_fallback_model:required.add(settings.native_web_search_fallback_model)
            missing=sorted(required-native_models) if native_models else []
            if missing:failures.append("native-search model IDs are absent from /models: "+", ".join(missing))
            print(f"Native Fact/News search: configured ({native_mode}; model={native_model})")
        except Exception as exc:
            failures.append(f"native-search gateway unavailable at {native_base}: {type(exc).__name__}: {exc}")

    # Importing the service used to fail on Windows when optional native PDF
    # libraries were missing; keep that boundary in the preflight.
    try:
        import api.service  # noqa: F401
        print("Backend imports: OK")
    except Exception as exc:
        failures.append(f"backend import failed: {type(exc).__name__}: {exc}")

    if failures:
        for item in failures:
            print(f"ERROR: {item}",file=sys.stderr)
        raise SystemExit(1)
    print("Preflight: PASS")


if __name__=="__main__":
    asyncio.run(main())
