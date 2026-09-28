from core.schemas.job import utcnow
from storage.database import database
from observability.execution import current_job_id


class Telemetry:
    async def emit(self, event: dict, job_id: str | None = None):
        job_id=job_id or current_job_id()
        if not job_id:
            return
        payload={"ts":utcnow(), **event}
        await database.add_event(job_id, payload)

    async def node_start(self,node,message=""):
        job_id=current_job_id()
        if job_id:
            try:
                from core.workflow.graphs import graph_for
                job=await database.get_job(job_id)
                if job:
                    nodes=graph_for(job.request.niche)["nodes"]
                    ids=[n["id"] for n in nodes]
                    if node in ids:
                        idx=ids.index(node)
                        candidate=min(88,max(3,3+int((idx/max(1,len(ids)-1))*82)))
                        progress=max(int(job.progress or 0),candidate)
                    else:
                        # Unknown/auxiliary nodes may update the stage but must
                        # never make progress jump backwards.
                        progress=int(job.progress or 0)
                    await database.update_runtime(job_id,stage=node,progress=progress)
            except Exception:
                pass
        await self.emit({"type":"node_start","node":node,"status":"running","message":message})

    async def node_success(self,node,message=""):
        await self.emit({"type":"node_success","node":node,"status":"success","message":message})

    async def node_error(self,node,error):
        await self.emit({"type":"node_error","node":node,"status":"failed","message":str(error)})

    async def retry(self,node,round_no,max_rounds,reason=""):
        await self.emit({"type":"retry","node":node,"status":"retrying",
                         "message":reason,"round":round_no,"max_rounds":max_rounds})

    async def fallback(self,node,from_target,to_target,reason=""):
        await self.emit({"type":"fallback","node":node,"status":"fallback",
                         "from":from_target,"to":to_target,"message":reason})

    async def edge(self,source,target,kind="normal",message=""):
        await self.emit({"type":"edge_taken","source":source,"target":target,"kind":kind,"message":message})

    async def step(self,node,status,message="",**extra):
        await self.emit({"type":"step","node":node,"status":status,"message":message,**extra})


telemetry=Telemetry()
