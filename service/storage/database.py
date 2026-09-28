import json
import aiosqlite
from service.settings import app_settings
from service.models import ProjectJob, ProjectGenerationRequest, ProjectStatus, utc_timestamp


PROJECT_DATABASE_SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  request_json TEXT NOT NULL,
  user_promt TEXT NOT NULL,
  niche TEXT NOT NULL,
  languages_json TEXT NOT NULL,
  duration_minutes INTEGER NOT NULL,
  status TEXT NOT NULL,
  stage TEXT NOT NULL,
  progress INTEGER NOT NULL DEFAULT 0,
  trend_score REAL,
  error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  started_at TEXT,
  completed_at TEXT,
  name TEXT NOT NULL DEFAULT '',
  result_json TEXT,
  provider TEXT NOT NULL DEFAULT 'openai'
);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created ON projects(created_at DESC);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id TEXT NOT NULL,
  ts TEXT NOT NULL,
  type TEXT NOT NULL,
  node TEXT,
  status TEXT,
  message TEXT,
  payload_json TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);
CREATE INDEX IF NOT EXISTS idx_events_project_id ON events(project_id, id);
"""

# Keep legacy column indexes stable; new fields are appended at the end.
PROJECT_DATABASE_COLUMN_NAMES = """
id,request_json,user_promt,niche,languages_json,duration_minutes,status,stage,progress,
trend_score,error,created_at,updated_at,started_at,completed_at,name,result_json,provider
"""


class SQLiteProjectDatabase:
    def open_database_connection(self):
        return aiosqlite.connect(app_settings.sqlite_database_file(), timeout=30)

    async def _configure_database_connection(self,database_connection):
        await database_connection.execute("PRAGMA busy_timeout=30000")
        await database_connection.execute("PRAGMA foreign_keys=ON")

    async def initialize_database(self):
        async with self.open_database_connection() as database_connection:
            await self._configure_database_connection(database_connection)
            await database_connection.executescript(PROJECT_DATABASE_SCHEMA)
            # In-place migration for databases created before project names existed.
            database_cursor=await database_connection.execute("PRAGMA table_info(projects)")
            column_names={database_row[1] for database_row in await database_cursor.fetchall()}
            if "user_promt" not in column_names and "topic" in column_names:
                await database_connection.execute("ALTER TABLE projects RENAME COLUMN topic TO user_promt")
                column_names.remove("topic")
                column_names.add("user_promt")
            if "name" not in column_names:
                await database_connection.execute("ALTER TABLE projects ADD COLUMN name TEXT NOT NULL DEFAULT ''")
            if "result_json" not in column_names:
                await database_connection.execute("ALTER TABLE projects ADD COLUMN result_json TEXT")
            if "provider" not in column_names:
                await database_connection.execute("ALTER TABLE projects ADD COLUMN provider TEXT NOT NULL DEFAULT 'openai'")
            await database_connection.execute("UPDATE projects SET provider='openai' WHERE provider!='openai'")
            await database_connection.commit()

    async def save_job(self, job: ProjectJob):
        async with self.open_database_connection() as database_connection:
            await self._configure_database_connection(database_connection)
            await database_connection.execute("""
            INSERT INTO projects (
              id,request_json,user_promt,niche,languages_json,duration_minutes,status,stage,progress,
              trend_score,error,created_at,updated_at,started_at,completed_at,name,result_json,provider
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
              request_json=excluded.request_json,
              user_promt=excluded.user_promt,
              niche=excluded.niche,
              languages_json=excluded.languages_json,
              duration_minutes=excluded.duration_minutes,
              status=excluded.status,
              stage=excluded.stage,
              progress=excluded.progress,
              trend_score=excluded.trend_score,
              error=excluded.error,
              updated_at=excluded.updated_at,
              started_at=excluded.started_at,
              completed_at=excluded.completed_at,
              name=excluded.name,
              result_json=excluded.result_json,
              provider=excluded.provider
            """, (
                job.id,
                job.request.model_dump_json(),
                job.request.user_promt,
                job.request.niche,
                json.dumps(job.request.languages, ensure_ascii=False),
                job.request.duration_minutes,
                job.status.value,
                job.stage,
                job.progress,
                job.trend_score,
                job.error,
                job.created_at,
                job.updated_at,
                job.started_at,
                job.completed_at,
                job.name,
                json.dumps(job.result,ensure_ascii=False) if job.result is not None else None,
                job.provider,
            ))
            await database_connection.commit()

    def _database_row_to_job(self,database_row):
        if not database_row:return None
        serialized_request=json.loads(database_row[1])
        # Existing saved projects may still contain the retired Grok provider.
        serialized_request["provider"]="openai"
        generation_request=ProjectGenerationRequest.model_validate(serialized_request)
        return ProjectJob(
            id=database_row[0],
            request=generation_request,
            status=ProjectStatus(database_row[6]),
            stage=database_row[7],
            progress=database_row[8],
            trend_score=database_row[9],
            error=database_row[10],
            created_at=database_row[11],
            updated_at=database_row[12],
            started_at=database_row[13],
            completed_at=database_row[14],
            name=database_row[15] or "Untitled project",
            result=json.loads(database_row[16]) if len(database_row)>16 and database_row[16] else None,
            provider="openai",
        )

    async def get_job(self,id:str):
        async with self.open_database_connection() as database_connection:
            await self._configure_database_connection(database_connection)
            database_cursor=await database_connection.execute(
                f"SELECT {PROJECT_DATABASE_COLUMN_NAMES} FROM projects WHERE id=?",
                (id,)
            )
            return self._database_row_to_job(await database_cursor.fetchone())

    async def list_jobs(self,limit=200,status:str|None=None):
        limit=max(1,min(int(limit),1000))
        async with self.open_database_connection() as database_connection:
            await self._configure_database_connection(database_connection)
            if status:
                database_cursor=await database_connection.execute(
                    f"SELECT {PROJECT_DATABASE_COLUMN_NAMES} FROM projects WHERE status=? ORDER BY created_at DESC LIMIT ?",
                    (status,limit)
                )
            else:
                database_cursor=await database_connection.execute(
                    f"SELECT {PROJECT_DATABASE_COLUMN_NAMES} FROM projects ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )
            return [self._database_row_to_job(result_row) for result_row in await database_cursor.fetchall()]

    async def requeue_interrupted_jobs(self):
        async with self.open_database_connection() as database_connection:
            await self._configure_database_connection(database_connection)
            await database_connection.execute(
                "UPDATE projects SET status='queued',stage='recovered_queue',updated_at=? WHERE status='running'",
                (utc_timestamp(),)
            )
            await database_connection.commit()

    async def cancel_job(self,id:str)->bool:
        """Atomically move only queued/running work into the cancelled state."""
        current_timestamp=utc_timestamp()
        async with self.open_database_connection() as database_connection:
            await self._configure_database_connection(database_connection)
            database_cursor=await database_connection.execute(
                """UPDATE projects
                   SET status='cancelled',stage='cancelled',error=NULL,
                       updated_at=?,completed_at=?
                   WHERE id=? AND status IN ('queued','running')""",
                (current_timestamp,current_timestamp,id),
            )
            await database_connection.commit()
            return database_cursor.rowcount>0

    async def update_progress(self,id:str,*,stage=None,progress=None,trend_score=None,name=None):
        updated_columns=[]
        query_parameters=[]
        if stage is not None:
            updated_columns.append("stage=?");query_parameters.append(stage)
        if progress is not None:
            updated_columns.append("progress=?");query_parameters.append(int(progress))
        if trend_score is not None:
            updated_columns.append("trend_score=?");query_parameters.append(float(trend_score))
        if name is not None:
            updated_columns.append("name=?");query_parameters.append(str(name))
        if not updated_columns:
            return
        updated_columns.append("updated_at=?")
        query_parameters.extend((utc_timestamp(), id))
        async with self.open_database_connection() as database_connection:
            await self._configure_database_connection(database_connection)
            await database_connection.execute(
                f"UPDATE projects SET {', '.join(updated_columns)} WHERE id=?",
                query_parameters,
            )
            await database_connection.commit()

    async def save_event(self,id:str,activity_event:dict)->int:
        serialized_event=json.dumps(activity_event,ensure_ascii=False)
        async with self.open_database_connection() as database_connection:
            await self._configure_database_connection(database_connection)
            database_cursor=await database_connection.execute(
                "INSERT INTO events(project_id,ts,type,node,status,message,payload_json) VALUES(?,?,?,?,?,?,?)",
                (
                    id,activity_event.get("ts") or utc_timestamp(),activity_event.get("type","event"),
                    activity_event.get("node"),activity_event.get("status"),activity_event.get("message"),serialized_event
                )
            )
            await database_connection.commit()
            return database_cursor.lastrowid

    async def list_events_after(self,id:str,after_id:int=0,limit:int=500):
        limit=max(1,min(int(limit),5000))
        async with self.open_database_connection() as database_connection:
            await self._configure_database_connection(database_connection)
            database_cursor=await database_connection.execute(
                "SELECT id,payload_json FROM events WHERE project_id=? AND id>? ORDER BY id ASC LIMIT ?",
                (id,int(after_id),limit)
            )
            event_rows=await database_cursor.fetchall()
            return [{"id":result_row[0],**json.loads(result_row[1])} for result_row in event_rows]

    async def delete_record(self,id:str):
        """Delete project row and all DB-owned dependent rows atomically."""
        async with self.open_database_connection() as database_connection:
            await self._configure_database_connection(database_connection)
            await database_connection.execute("BEGIN IMMEDIATE")
            await database_connection.execute("DELETE FROM events WHERE project_id=?",(id,))
            database_cursor=await database_connection.execute("DELETE FROM projects WHERE id=?",(id,))
            await database_connection.commit()
            return database_cursor.rowcount>0


database=SQLiteProjectDatabase()
