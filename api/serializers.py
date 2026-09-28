def project_payload(job):
    """Lightweight SPA payload with compact readiness only; generated content stays file-backed."""
    data=job.model_dump(exclude={"result"})
    data["quality"]=job.result or {}
    return data
