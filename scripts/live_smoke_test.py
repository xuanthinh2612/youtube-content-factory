"""Optional live smoke test for a running local v7.9 server.

Usage:
  python scripts/live_smoke_test.py
  LIVE_SMOKE_GENERATE=1 python scripts/live_smoke_test.py
The second form creates one tiny Fact project and polls it; it is intentionally opt-in because it spends API tokens.
"""
import json,os,time,urllib.request
BASE=os.getenv("FACTORY_URL","http://127.0.0.1:8090").rstrip("/")

def req(path,method="GET",payload=None):
    data=json.dumps(payload).encode() if payload is not None else None
    r=urllib.request.Request(BASE+path,data=data,method=method,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=10) as f:return json.loads(f.read().decode())

health=req("/health")
assert health.get("ok") and health.get("version")=="7.9.0",health
print("health: ok",health)
if os.getenv("LIVE_SMOKE_GENERATE")!="1":
    print("generation: skipped (set LIVE_SMOKE_GENERATE=1 to spend tokens)")
    raise SystemExit(0)
job=req("/api/generate","POST",{"topic":"Why does Earth have day and night?","niche":"fact","languages":["vi"],"duration_minutes":1,"timezone":"Asia/Tokyo"})
job_id=job["job_id"];print("job",job_id)
for _ in range(120):
    p=req(f"/api/projects/{job_id}")
    if p["status"] in ("completed","failed","cancelled"):
        print(json.dumps(p,ensure_ascii=False,indent=2));assert p["status"]=="completed";break
    time.sleep(2)
else:raise TimeoutError("smoke project did not finish")
