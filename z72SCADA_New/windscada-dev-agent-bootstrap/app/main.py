from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from datetime import datetime

app = FastAPI(title="WindSCADA Dev Agent API", version="0.1.0")

class LogItem(BaseModel):
    ts: str | None = None
    level: str = "INFO"
    message: str

LOGS: list[LogItem] = []

@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "WindSCADA Dev Agent API",
        "version": app.version,
        "time": datetime.now().isoformat(timespec="seconds")
    }

@app.post("/logs")
def add_log(item: LogItem):
    if item.ts is None:
        item.ts = datetime.now().isoformat(timespec="seconds")
    LOGS.append(item)
    return {"ok": True, "count": len(LOGS)}

@app.get("/logs", response_model=List[LogItem])
def list_logs():
    return LOGS
