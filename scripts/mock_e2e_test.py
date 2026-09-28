"""Token-free service/export smoke test intended to run inside the Docker image.

It patches Director context and generation with deterministic WorkflowResult objects, then
executes the same service layer used by queued projects for all five niches. This
checks database persistence, export files, readiness summaries and clean TTS output
without calling an LLM or the web.
"""
from __future__ import annotations
import asyncio,tempfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from unittest.mock import patch

from core.config import settings
from core.schemas.job import GenerateRequest,Job
from core.schemas.output import WorkflowResult,LanguageOutput
from storage.database import database
from storage.files import file_store
from storage.jobs import job_store
from api.service import execute


def fake_result(niche):
    stem_text={
        "fact":"# Fact title\n\nThis is a clear spoken factual narration with enough words for a smoke export.",
        "story":"# Story title\n\nA narrator tells a small complete story in a natural voice.",
        "news":"# News title\n\nHere is the verified update, stated calmly and with attribution.",
        "music":"# Song title\n\nVerse one\n\nChorus",
        "visual":"# Visual plan\n\nA deterministic visual plan.",
    }[niche]
    checks={"ready":True,"quality_warning":None}
    out=LanguageOutput(language="vi",title="Smoke",outline={"smoke":True},draft=stem_text,final_text=stem_text,checks=checks)
    return WorkflowResult(niche=niche,canonical_title="Smoke",blueprint={"title":"Smoke"},outputs={"vi":out})

async def main():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        old_db,old_base=settings.db_path,file_store.base
        settings.db_path=str(root/"factory.db")
        file_store.base=root/"outputs";file_store.base.mkdir(parents=True,exist_ok=True)
        try:
            await database.init()
            def fake_apply(req,context):return req
            async def fake_run(req,context=None):return fake_result(req.niche)
            with patch("api.service.apply_request_defaults",new=fake_apply),patch("api.service.run_request",new=fake_run):
                for niche in ("fact","story","news","music","visual"):
                    job=Job(id=f"smoke-{niche}",request=GenerateRequest(topic="Smoke topic",niche=niche,languages=["vi"],duration_minutes=1))
                    await job_store.put(job);await execute(job)
                    saved=await job_store.get(job.id)
                    assert saved and saved.status.value=="completed",saved
                    assert (file_store.path(job.id)/"quality_summary.json").exists()
                    if niche in ("fact","story","news"):
                        txt=list((file_store.path(job.id)/"vi").glob("*.txt"))
                        assert txt,"TTS .txt output missing"
            print("mock e2e: PASS")
        finally:
            settings.db_path=old_db;file_store.base=old_base

if __name__=="__main__":asyncio.run(main())
