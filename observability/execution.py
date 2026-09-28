from contextlib import contextmanager
from contextvars import ContextVar

_current_job: ContextVar[str | None] = ContextVar("current_job_id", default=None)

@contextmanager
def execution_context(job_id: str):
    token=_current_job.set(job_id)
    try:
        yield
    finally:
        _current_job.reset(token)

def current_job_id():
    return _current_job.get()
