import json
import aiosqlite
from core.config import settings
from core.schemas.job import Job, GenerateRequest, JobStatus, utcnow


SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  request_json TEXT NOT NULL,
  topic TEXT NOT NULL,
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
  result_json TEXT
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

# Keep legacy column indexes stable; name is appended at the end.
PROJECT_COLUMNS = """
id,request_json,topic,niche,languages_json,duration_minutes,status,stage,progress,
trend_score,error,created_at,updated_at,started_at,completed_at,name,result_json
"""


class Database:
    def connect(self):
        return aiosqlite.connect(settings.database_path(), timeout=30)

    async def _prepare(self,db):
        await db.execute("PRAGMA busy_timeout=30000")
        await db.execute("PRAGMA foreign_keys=ON")

    async def init(self):
        async with self.connect() as db:
            await self._prepare(db)
            await db.executescript(SCHEMA)
            # In-place migration for databases created before project names existed.
            cur=await db.execute("PRAGMA table_info(projects)")
            columns={row[1] for row in await cur.fetchall()}
            if "name" not in columns:
                await db.execute("ALTER TABLE projects ADD COLUMN name TEXT NOT NULL DEFAULT ''")
            if "result_json" not in columns:
                await db.execute("ALTER TABLE projects ADD COLUMN result_json TEXT")
            await db.commit()

    async def upsert_job(self, job: Job):
        async with self.connect() as db:
            await self._prepare(db)
            await db.execute("""
            INSERT INTO projects (
              id,request_json,topic,niche,languages_json,duration_minutes,status,stage,progress,
              trend_score,error,created_at,updated_at,started_at,completed_at,name,result_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
              request_json=excluded.request_json,
              topic=excluded.topic,
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
              result_json=excluded.result_json
            """, (
                job.id,
                job.request.model_dump_json(),
                job.request.topic,
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
            ))
            await db.commit()

    def _row_to_job(self,row):
        if not row:return None
        return Job(
            id=row[0],
            request=GenerateRequest.model_validate_json(row[1]),
            status=JobStatus(row[6]),
            stage=row[7],
            progress=row[8],
            trend_score=row[9],
            error=row[10],
            created_at=row[11],
            updated_at=row[12],
            started_at=row[13],
            completed_at=row[14],
            name=row[15] or "Untitled project",
            result=json.loads(row[16]) if len(row)>16 and row[16] else None,
        )

    async def get_job(self,project_id:str):
        async with self.connect() as db:
            await self._prepare(db)
            cur=await db.execute(
                f"SELECT {PROJECT_COLUMNS} FROM projects WHERE id=?",
                (project_id,)
            )
            return self._row_to_job(await cur.fetchone())

    async def list_jobs(self,limit=200,status:str|None=None):
        limit=max(1,min(int(limit),1000))
        async with self.connect() as db:
            await self._prepare(db)
            if status:
                cur=await db.execute(
                    f"SELECT {PROJECT_COLUMNS} FROM projects WHERE status=? ORDER BY created_at DESC LIMIT ?",
                    (status,limit)
                )
            else:
                cur=await db.execute(
                    f"SELECT {PROJECT_COLUMNS} FROM projects ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )
            return [self._row_to_job(r) for r in await cur.fetchall()]

    async def mark_running_as_queued(self):
        async with self.connect() as db:
            await self._prepare(db)
            await db.execute(
                "UPDATE projects SET status='queued',stage='recovered_queue',updated_at=? WHERE status='running'",
                (utcnow(),)
            )
            await db.commit()

    async def cancel_project(self,project_id:str)->bool:
        """Atomically move only queued/running work into the cancelled state."""
        now=utcnow()
        async with self.connect() as db:
            await self._prepare(db)
            cur=await db.execute(
                """UPDATE projects
                   SET status='cancelled',stage='cancelled',error=NULL,
                       updated_at=?,completed_at=?
                   WHERE id=? AND status IN ('queued','running')""",
                (now,now,project_id),
            )
            await db.commit()
            return cur.rowcount>0

    async def update_runtime(self,project_id:str,*,stage=None,progress=None,trend_score=None,name=None):
        sets=[];values=[]
        if stage is not None:
            sets.append("stage=?");values.append(stage)
        if progress is not None:
            sets.append("progress=?");values.append(int(progress))
        if trend_score is not None:
            sets.append("trend_score=?");values.append(float(trend_score))
        if name is not None:
            sets.append("name=?");values.append(str(name))
        if not sets:return
        sets.append("updated_at=?");values.append(utcnow());values.append(project_id)
        async with self.connect() as db:
            await self._prepare(db)
            await db.execute(f"UPDATE projects SET {', '.join(sets)} WHERE id=?",values)
            await db.commit()

    async def add_event(self,project_id:str,event:dict)->int:
        payload=json.dumps(event,ensure_ascii=False)
        async with self.connect() as db:
            await self._prepare(db)
            cur=await db.execute(
                "INSERT INTO events(project_id,ts,type,node,status,message,payload_json) VALUES(?,?,?,?,?,?,?)",
                (
                    project_id,event.get("ts") or utcnow(),event.get("type","event"),
                    event.get("node"),event.get("status"),event.get("message"),payload
                )
            )
            await db.commit()
            return cur.lastrowid

    async def events_after(self,project_id:str,after_id:int=0,limit:int=500):
        limit=max(1,min(int(limit),5000))
        async with self.connect() as db:
            await self._prepare(db)
            cur=await db.execute(
                "SELECT id,payload_json FROM events WHERE project_id=? AND id>? ORDER BY id ASC LIMIT ?",
                (project_id,int(after_id),limit)
            )
            rows=await cur.fetchall()
            return [{"id":r[0],**json.loads(r[1])} for r in rows]

    async def event_history(self,project_id:str):
        out=[];cursor=0
        while True:
            batch=await self.events_after(project_id,cursor,5000)
            if not batch:break
            out.extend(batch)
            cursor=batch[-1]["id"]
            if len(batch)<5000:break
        return out

    async def delete_project(self,project_id:str):
        """Delete project row and all DB-owned dependent rows atomically."""
        async with self.connect() as db:
            await self._prepare(db)
            await db.execute("BEGIN IMMEDIATE")
            await db.execute("DELETE FROM events WHERE project_id=?",(project_id,))
            cur=await db.execute("DELETE FROM projects WHERE id=?",(project_id,))
            await db.commit()
            return cur.rowcount>0


database=Database()
