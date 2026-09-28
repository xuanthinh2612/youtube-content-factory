from observability.execution import current_job_id


class UsageTracker:
    """Per-job token accounting split by model and workflow node/agent."""
    def __init__(self):
        self.by_job={}

    def add(self,model,prompt_tokens,completion_tokens,node="llm",context_chars=0,
            retry_count=0,language="",unit=""):
        job_id=current_job_id() or "__unscoped__"
        job=self.by_job.setdefault(job_id,{"models":{},"nodes":{},"calls":[]})
        for bucket,key in ((job["models"],model),(job["nodes"],node or "llm")):
            row=bucket.setdefault(key,{"prompt_tokens":0,"completion_tokens":0,"calls":0})
            row["prompt_tokens"]+=int(prompt_tokens or 0)
            row["completion_tokens"]+=int(completion_tokens or 0)
            row["calls"]+=1
        job["calls"].append({"agent":node or "llm","language":language or "",
            "unit":unit or "","input_tokens":int(prompt_tokens or 0),
            "output_tokens":int(completion_tokens or 0),"retry_count":int(retry_count or 0),
            "context_chars":int(context_chars or 0)})

    def snapshot(self,job_id=None):
        job_id=job_id or current_job_id() or "__unscoped__"
        job=self.by_job.get(job_id,{"models":{},"nodes":{},"calls":[]})
        models=job.get("models",{})
        nodes=job.get("nodes",{})
        total_prompt=sum(x["prompt_tokens"] for x in models.values())
        total_completion=sum(x["completion_tokens"] for x in models.values())
        total_calls=sum(x["calls"] for x in models.values())
        ranked_nodes=dict(sorted(
            ((k,{**v,"total_tokens":v["prompt_tokens"]+v["completion_tokens"]}) for k,v in nodes.items()),
            key=lambda kv:kv[1]["total_tokens"],reverse=True
        ))
        return {
            "models":{k:dict(v) for k,v in models.items()},
            "nodes":ranked_nodes,
            "calls":list(job.get("calls",[])),
            "total_prompt_tokens":total_prompt,
            "total_completion_tokens":total_completion,
            "total_tokens":total_prompt+total_completion,
            "total_calls":total_calls,
        }

    def clear(self,job_id=None):
        job_id=job_id or current_job_id() or "__unscoped__"
        self.by_job.pop(job_id,None)


usage_tracker=UsageTracker()
