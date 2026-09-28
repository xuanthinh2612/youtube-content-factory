from storage.database import database
from observability.telemetry import telemetry

class EventBus:
    async def emit(self,job_id,event):
        await telemetry.emit(event,job_id=job_id)
    async def since(self,job_id,cursor):
        return await database.events_after(job_id,cursor)
event_bus=EventBus()
