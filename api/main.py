import asyncio,html,json,uuid
from pathlib import Path

import bleach
import markdown as md
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import HTMLResponse,StreamingResponse,FileResponse
from fastapi.staticfiles import StaticFiles

from core.schemas.job import GenerateRequest,Job,BulkDeleteRequest
from core.config import settings
from core.workflow.graphs import graph_for
from core.workflow.graph_state import reduce_graph
from core.runtime import project_queue
from storage.database import database
from storage.jobs import job_store
from storage.files import file_store
from api.service import execute
from api.serializers import project_payload
from observability.logging import configure_logging
from observability.telemetry import telemetry
from observability.usage import usage_tracker
from core.llm.client import llm

configure_logging()
BASE=Path(__file__).resolve().parent.parent
UI=BASE/"ui"

app=FastAPI(title="YouTube Content Factory",version="7.9.0")
app.mount("/assets",StaticFiles(directory=UI/"assets",check_dir=False),name="assets")


@app.on_event("startup")
async def startup():
    await database.init()
    await project_queue.start(execute)


@app.on_event("shutdown")
async def shutdown():
    await llm.close()


@app.get("/health")
async def health():
    return {"ok":True,"version":"7.9.0","queue":project_queue.snapshot()}




@app.post("/api/generate")
async def generate(req:GenerateRequest):
    job=Job(id=str(uuid.uuid4()),request=req)
    await job_store.put(job)
    await telemetry.emit({"type":"project_created","status":"queued","stage":"queued"},job.id)
    await project_queue.submit(job.id)
    return {"job_id":job.id,"view_url":f"/view/{job.id}","monitor_url":f"/projects/{job.id}"}


@app.get("/api/projects")
async def projects(limit:int=200,status:str|None=None):
    jobs=await job_store.list(limit=limit,status=status)
    return {"items":[project_payload(j) for j in jobs],"queue":project_queue.snapshot()}


@app.get("/api/projects/{job_id}")
async def project(job_id:str):
    j=await job_store.get(job_id)
    if not j:raise HTTPException(404,"Project not found")
    return project_payload(j)


@app.post("/api/projects/{job_id}/cancel")
async def cancel_project(job_id:str):
    j=await job_store.get(job_id)
    if not j:raise HTTPException(404,"Project not found")
    if j.status.value=="cancelled":
        return {"ok":True,"project_id":job_id,"status":"cancelled","already_cancelled":True}
    if j.status.value not in ("queued","running"):
        raise HTTPException(409,f"Project is already {j.status.value} and cannot be stopped")

    # Preserve usage accumulated before cancellation, then stop the coroutine.
    # Waiting for ProjectQueue.cancel first prevents the executor from racing a
    # final completed/failed write over the cancelled database state.
    live_usage=usage_tracker.snapshot(job_id)
    await project_queue.cancel(job_id)
    changed=await job_store.cancel(job_id)
    if not changed:
        latest=await job_store.get(job_id)
        if latest and latest.status.value=="cancelled":
            return {"ok":True,"project_id":job_id,"status":"cancelled","already_cancelled":True}
        state=latest.status.value if latest else "missing"
        raise HTTPException(409,f"Project became {state} before it could be stopped")
    if live_usage.get("total_calls",0):
        try:
            file_store.write_json(job_id,"observability/usage.json",live_usage)
        except Exception:
            # Cancellation itself has already succeeded. A secondary artifact
            # write failure must not turn the force-stop response into an error.
            pass
    await telemetry.emit({
        "type":"project_cancelled","node":"cancelled","status":"cancelled",
        "stage":"cancelled","message":"Project force-stopped by user",
    },job_id)
    return {"ok":True,"project_id":job_id,"status":"cancelled"}


async def _delete_single_project(job_id:str)->bool:
    j=await job_store.get(job_id)
    if not j:
        return False
    # Stop queued/running work first so a deleted job cannot recreate DB/files.
    await project_queue.cancel(job_id)
    file_store.delete_project(job_id)
    return await job_store.delete(job_id)


@app.delete("/api/projects/{job_id}")
async def delete_project(job_id:str,confirm:str=""):
    if confirm != "Delete":
        raise HTTPException(400,"Type Delete exactly to confirm project deletion")
    deleted=await _delete_single_project(job_id)
    if not deleted:
        raise HTTPException(404,"Project not found")
    return {"ok":True,"deleted_project_id":job_id}


@app.delete("/api/projects")
async def delete_projects_bulk(payload:BulkDeleteRequest):
    if payload.confirm != "Delete":
        raise HTTPException(400,"Type Delete exactly to confirm project deletion")
    ids=list(dict.fromkeys(i.strip() for i in payload.project_ids if i and i.strip()))
    if not ids:
        raise HTTPException(400,"No project ids provided")

    deleted_ids=[]
    missing_ids=[]
    for job_id in ids:
        if await _delete_single_project(job_id):
            deleted_ids.append(job_id)
        else:
            missing_ids.append(job_id)
    return {"ok":True,"deleted_project_ids":deleted_ids,"missing_project_ids":missing_ids}


@app.get("/api/projects/{job_id}/graph")
async def graph(job_id:str):
    j=await job_store.get(job_id)
    if not j:raise HTTPException(404,"Project not found")
    spec=graph_for(j.request.niche)
    history=await database.event_history(job_id)
    state=reduce_graph(spec,history,j.status.value)
    return {
        **state,
        "project":{
            "status":j.status.value,
            "stage":j.stage,
            "progress":j.progress,
            "error":j.error,
        },
    }


@app.get("/api/projects/{job_id}/events")
async def project_events(job_id:str,after:int=0):
    if not await job_store.get(job_id):raise HTTPException(404,"Project not found")
    return {"items":await database.events_after(job_id,after,1000)}


@app.get("/api/projects/{job_id}/events/stream")
async def event_stream(job_id:str,request:Request,after:int=0):
    if not await job_store.get(job_id):raise HTTPException(404,"Project not found")
    last_header=request.headers.get("last-event-id")
    try:
        cursor=max(int(last_header or 0),int(after or 0))
    except ValueError:
        cursor=0

    async def stream():
        nonlocal cursor
        while True:
            events=await database.events_after(job_id,cursor,200)
            for e in events:
                cursor=e["id"]
                yield f"id: {cursor}\ndata: {json.dumps(e,ensure_ascii=False)}\n\n"
            j=await job_store.get(job_id)
            if not events and (not j or j.status.value in ("completed","failed","cancelled")):
                break
            # Keep reverse proxies from considering the stream completely idle.
            if not events:
                yield ": keepalive\n\n"
            await asyncio.sleep(.75)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"},
    )


@app.get("/api/projects/{job_id}/usage")
async def project_usage(job_id:str):
    j=await job_store.get(job_id)
    if not j:raise HTTPException(404,"Project not found")
    live=usage_tracker.snapshot(job_id)
    if live.get("total_calls",0):
        return live
    return file_store.read_json(job_id,"observability/usage.json",{
        "models":{},"nodes":{},"total_prompt_tokens":0,"total_completion_tokens":0,"total_tokens":0,"total_calls":0
    })


@app.get("/api/projects/{job_id}/files")
async def files(job_id:str):
    if not await job_store.get(job_id):raise HTTPException(404,"Project not found")
    root=file_store.existing_folder(job_id)
    if root is None:
        return {"files":[]}
    return {"files":[str(p.relative_to(root)).replace("\\","/")
                     for p in sorted(root.rglob("*")) if p.is_file()]}


@app.get("/api/system/queue")
async def queue_state():
    return project_queue.snapshot()


@app.get("/api/jobs/{job_id}/download/{file_path:path}")
async def download(job_id,file_path):
    if not await job_store.get(job_id):
        raise HTTPException(404,"Project not found")
    p=file_store.resolve_read(job_id,file_path)
    if p is None:
        raise HTTPException(404,"File not found")
    return FileResponse(p,filename=p.name)


VIEW_CSS="""
:root{color-scheme:light dark}
body{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
max-width:860px;margin:48px auto;padding:0 24px;line-height:1.78;color:#171717;background:#fff}
a{color:#4f46e5;text-decoration:none}a:hover{text-decoration:underline}
.card{border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:10px 0}
h1{font-size:2rem;line-height:1.2;margin:1.6rem 0 1rem}
h2{font-size:1.38rem;line-height:1.3;margin:2.3rem 0 .75rem;border-bottom:1px solid #e5e7eb;padding-bottom:.4rem}
h3{margin-top:1.7rem}p{margin:.8rem 0 1.05rem}li{margin:.35rem 0}
blockquote{border-left:3px solid #a5b4fc;margin:1.2rem 0;padding:.35rem 1rem;color:#52525b;background:#fafafa}
code{background:#f4f4f5;padding:.1rem .25rem;border-radius:4px}
@media(prefers-color-scheme:dark){
body{color:#e7e7e7;background:#111}
.card{border-color:#2d2d2d}
h2{border-color:#2d2d2d}
blockquote{background:#181818;color:#b7b7b7}
code{background:#222}
a{color:#9aa8ff}
}
"""

ALLOWED_TAGS=set(bleach.sanitizer.ALLOWED_TAGS)|{
    "p","h1","h2","h3","h4","h5","h6","pre","code","blockquote",
    "ul","ol","li","hr","br","table","thead","tbody","tr","th","td"
}
ALLOWED_ATTRS={"a":["href","title","rel"],"code":["class"],"pre":["class"]}


@app.get("/view/{job_id}",response_class=HTMLResponse)
async def view_job(job_id):
    j=await job_store.get(job_id)
    if not j:raise HTTPException(404,"Job not found")
    root=file_store.existing_folder(job_id);cards=[]
    if root is None:
        root=file_store.path(job_id)
    for lang in j.request.languages:
        d=root/lang
        if not d.exists():continue
        for p in sorted(d.glob("*.md")):
            cards.append(
                f'<div class="card"><b>{html.escape(lang.upper())} · {html.escape(p.stem)}</b><br>'
                f'<a href="/view/{job_id}/{lang}/{p.stem}">View</a> · '
                f'<a href="/api/jobs/{job_id}/download/{lang}/{p.name}">Download</a></div>'
            )
    return HTMLResponse(
        f"<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<style>{VIEW_CSS}</style></head><body><a href='/projects/{job_id}'>← Project</a>"
        f"<h1>{html.escape(j.name)}</h1>{''.join(cards) or '<p>Not ready.</p>'}</body></html>"
    )


@app.get("/view/{job_id}/{language}/{kind}",response_class=HTMLResponse)
async def view_text(job_id,language,kind):
    if not await job_store.get(job_id):
        raise HTTPException(404,"Project not found")
    p=file_store.resolve_read(job_id,f"{language}/{kind}.md")
    if p is None:
        raise HTTPException(404,"Output not found")

    rendered=md.markdown(
        p.read_text(encoding="utf-8"),
        extensions=["tables","fenced_code","sane_lists"],
    )
    body=bleach.clean(
        rendered,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols={"http","https","mailto"},
        strip=True,
    )
    return HTMLResponse(
        f"<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<style>{VIEW_CSS}</style></head><body><a href='/view/{job_id}'>← Outputs</a>{body}</body></html>"
    )


# Vue SPA history fallback. Keep API/view routes above this.
@app.get("/",response_class=HTMLResponse)
@app.get("/projects",response_class=HTMLResponse)
@app.get("/projects/{path:path}",response_class=HTMLResponse)
async def spa(path:str=""):
    index=UI/"index.html"
    if not index.exists():
        return HTMLResponse(
            "<h1>Frontend is not built.</h1>"
            "<p>Run <code>cd frontend && npm install && npm run build</code>, or use Docker.</p>"
        )
    return HTMLResponse(index.read_text(encoding="utf-8"))
