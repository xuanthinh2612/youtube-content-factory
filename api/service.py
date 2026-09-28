from core.schemas.job import Job,JobStatus,utcnow
from workflows.router import run_request,apply_request_defaults,director_request_context
from storage.jobs import job_store
from storage.files import file_store
from exporters.content import export_all
from observability.usage import usage_tracker
from observability.execution import execution_context
from observability.telemetry import telemetry
from storage.database import database


def normalize_project_name(value,topic):
    name=" ".join(str(value or "").split()).strip(" -–—:;,.\t\n")
    if not name:
        words=" ".join(str(topic or "").split()).split()
        name=" ".join(words[:8]) or "Untitled project"
    return name[:96]


async def execute(job:Job):
    try:
        entry_node="director"
        job.status=JobStatus.running
        job.stage=entry_node
        job.progress=2
        job.error=None
        job.started_at=utcnow()
        job.updated_at=utcnow()
        await job_store.put(job)
        await telemetry.emit(
            {"type":"project_start","node":entry_node,"status":"running","stage":job.stage},
            job.id
        )

        with execution_context(job.id):
            # Apply form defaults and send the request directly to the Director.
            context=director_request_context(job.request)
            apply_request_defaults(job.request,context)
            result=await run_request(job.request,context=context)
            job.name=normalize_project_name(result.canonical_title,job.request.topic)
            job.updated_at=utcnow()
            await job_store.put(job)
            await telemetry.emit({
                "type":"project_named","node":entry_node,"status":"success",
                "message":job.name,
            },job.id)

            job.stage="export"
            job.progress=90
            job.updated_at=utcnow()
            await job_store.put(job)
            await telemetry.node_start("export")

            file_store.write_json(job.id,"manifest.json",{
                "job_id":job.id,
                "project_name":job.name,
                "topic":job.request.topic,
                "niche":job.request.niche,
                "languages":job.request.languages,
                "duration_minutes":job.request.duration_minutes,
                "view_url":f"/view/{job.id}",
            })
            file_store.write_json(job.id,"shared/blueprint.json",result.blueprint)
            if result.research:
                file_store.write_json(job.id,"shared/research.json",result.research)
                claim_ledger=result.research.get("claim_ledger")
                if claim_ledger is None and job.request.niche=="fact":
                    claim_ledger=[]
                    for key in ("established_facts","probable_findings","scientific_hypotheses","disputed_claims","unknowns","unsupported_claims"):
                        claim_ledger.extend(result.research.get(key,[]))
                elif claim_ledger is None and job.request.niche=="news":
                    claim_ledger=result.research.get("top_developments",[])
                file_store.write_json(
                    job.id,"shared/claim_ledger.json",
                    claim_ledger or []
                )

            export_warnings=[]
            stems={
                "fact":"script",
                "story":"story",
                "news":"news_script",
                "music":"suno_prompt",
                "visual":"visual_narration",
            }
            for lang,out in result.outputs.items():
                folder=file_store.folder(job.id)/lang
                if out.final_text:
                    export_text=out.final_text
                    content_paths=export_all(
                        folder,stems[job.request.niche],out.title,lang,export_text,
                        {"outline":out.outline,"checks_summary":{"ready":(out.checks or {}).get("ready"),"quality_warning":(out.checks or {}).get("quality_warning")}},
                        tts_ready=job.request.niche in ("fact","story","news"),
                        include_title=job.request.niche!="music",
                    )
                    export_warnings.extend(f"{lang}: {w}" for w in content_paths.get("_warnings",[]))
                file_store.write_json(job.id,f"{lang}/outline.json",out.outline)
                if job.request.niche=="music":
                    file_store.write_json(job.id,f"{lang}/song_package.json",out.outline)
                elif job.request.niche=="visual":
                    file_store.write_json(job.id,f"{lang}/visual_plan.json",out.outline)
                for name,value in out.checks.items():
                    file_store.write_json(job.id,f"{lang}/checks/{name}.json",value)

            readiness={}
            warnings=[]
            editor_reviews={}
            for lang,out in result.outputs.items():
                checks=out.checks or {}
                ready=checks.get("ready")
                warning=checks.get("quality_warning")
                if ready is not None:readiness[lang]=bool(ready)
                if warning:warnings.append(f"{lang}: {warning}")
                if checks.get("editor_review"):
                    editor_reviews[lang]=checks["editor_review"]
            warnings.extend(export_warnings)
            job.result={
                "ready":all(readiness.values()) if readiness else True,
                "languages":readiness,
                "quality_warnings":warnings,
                "export_warnings":export_warnings,
                "editor_reviews":editor_reviews,
            }
            file_store.write_json(job.id,"quality_summary.json",job.result)
            file_store.write_json(
                job.id,"observability/usage.json",usage_tracker.snapshot(job.id)
            )
            await telemetry.node_success("export")
            await telemetry.edge("export","completed")

        job.stage="completed"
        job.progress=100
        job.status=JobStatus.completed
        job.completed_at=utcnow()
        job.updated_at=utcnow()
        await job_store.put(job)
        await telemetry.emit({
            "type":"project_completed","node":"completed","status":"success",
            "view_url":f"/view/{job.id}"
        },job.id)

    except Exception as exc:
        latest=await database.get_job(job.id)
        failed_node=(latest.stage if latest else job.stage) or "unknown"
        if latest:
            job.progress=latest.progress
            job.name=latest.name
        try:
            file_store.write_json(
                job.id,"observability/usage.json",usage_tracker.snapshot(job.id)
            )
        except Exception:
            pass

        await telemetry.emit({
            "type":"node_error","node":failed_node,"status":"failed",
            "message":f"{type(exc).__name__}: {exc}"
        },job.id)

        job.stage="failed"
        job.status=JobStatus.failed
        job.error=f"{type(exc).__name__}: {exc}"
        job.completed_at=utcnow()
        job.updated_at=utcnow()
        await job_store.put(job)
        await telemetry.emit({
            "type":"project_failed","node":failed_node,"status":"failed",
            "message":job.error
        },job.id)

    finally:
        usage_tracker.clear(job.id)
