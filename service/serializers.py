"""Compatibility serializers for project API payloads."""


def serialize_details(job):
    data = job.model_dump(exclude={"result"}, by_alias=True)
    data["result"] = job.result or {}
    return data


def serialize_status(job):
    return {
        "id":job.id,
        "name":job.name,
        "status":job.status.value,
        "stage":job.stage,
        "progress":job.progress,
        "error":job.error,
    }
