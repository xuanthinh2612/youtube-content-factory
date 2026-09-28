"""Record project and agent activity against the currently running project."""

from contextlib import contextmanager
from contextvars import ContextVar

from service.models import utc_timestamp
from service.storage.database import database


_current_id: ContextVar[str | None] = ContextVar("current_project_id", default=None)


@contextmanager
def activity_context(id: str):
    context_token = _current_id.set(id)
    try:
        yield
    finally:
        _current_id.reset(context_token)


def get_current_id():
    return _current_id.get()


class ProjectActivityLogger:
    async def record_activity_event(self, activity_event: dict, id: str | None = None):
        id = id or get_current_id()
        if not id:
            return
        database_event = {"ts": utc_timestamp(), **activity_event}
        await database.save_event(id, database_event)

    async def record_agent_started(self, agent_role, response_text=""):
        id = get_current_id()
        if not id:
            return

        progress_by_agent_role = {
            "director": 10,
            "writer": 35,
            "reviewer": 60,
            "editor": 75,
            "export": 90,
        }
        progress = progress_by_agent_role.get(agent_role)
        if progress is not None:
            await database.update_progress(
                id, stage=agent_role, progress=progress
            )

    async def record_agent_succeeded(self, agent_role, response_text="", **event_metadata):
        await self.record_activity_event({
            "type": "node_success",
            "node": agent_role,
            "status": "success",
            "message": response_text,
            **event_metadata,
        })

    async def record_agent_failed(self, agent_role, error):
        await self.record_activity_event({
            "type": "node_error",
            "node": agent_role,
            "status": "failed",
            "message": str(error),
        })


activity_logger = ProjectActivityLogger()
