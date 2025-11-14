"""FastAPI service exposing pipeline tasks as HTTP endpoints."""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.utils.config import load_settings
from src.pipelines import (
    run_active_pool_refresh,
    run_full_pool_refresh,
    run_indicator_batch,
    run_watchlist_pipeline,
    run_auto_pipeline,
    run_market_regime_detection,
)
from src.pipelines.backfill_daily import run_backfill_daily, run_incremental_daily

app = FastAPI(title="Quant Task API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = load_settings()

TaskFn = Callable[[], None]

def run_backfill_with_indicators() -> None:
    run_backfill_daily(settings)
    run_indicator_batch(settings)

def run_watchlist_tasks() -> None:
    run_watchlist_pipeline(settings)


def run_daily_routine() -> None:
    _set_task_message("daily_routine", "Incremental daily bars + indicators")
    run_incremental_daily(settings)
    _set_task_message("daily_routine", "Refreshing active universe + indicators")
    run_active_pool_refresh(settings)
    _set_task_message("daily_routine", "Updating market regime snapshot")
    run_market_regime_detection(settings)
    _set_task_message("daily_routine", "Generating latest watchlist")
    run_watchlist_pipeline(settings)

TASK_FUNCTIONS: Dict[str, TaskFn] = {
    "full_pool": lambda: run_full_pool_refresh(settings),
    "daily": lambda: run_incremental_daily(settings),
    "backfill_daily": run_backfill_with_indicators,
    "watchlist": run_watchlist_tasks,
    "daily_routine": run_daily_routine,
    "auto": lambda: run_auto_pipeline(settings),
}

class TaskStatus(BaseModel):
    task: str
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_seconds: float | None = None
    message: str | None = None

STATUS_FILE = Path("data/logs/task_status.json")


def _load_statuses() -> Dict[str, TaskStatus]:
    defaults = {name: TaskStatus(task=name, status="idle") for name in TASK_FUNCTIONS}
    if not STATUS_FILE.exists():
        return defaults
    try:
        raw = json.loads(STATUS_FILE.read_text())
    except Exception:
        return defaults
    for name in TASK_FUNCTIONS:
        entry = raw.get(name)
        if not entry:
            continue
        try:
            defaults[name] = TaskStatus(**entry)
        except Exception:
            continue
    return defaults


def _save_statuses() -> None:
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {name: _serialize_status(status) for name, status in STATUSES.items()}
    STATUS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2))


def _serialize_status(status: TaskStatus) -> Dict[str, Any]:
    data = status.dict()
    for field in ("started_at", "finished_at"):
        value = data.get(field)
        if hasattr(value, "isoformat"):
            data[field] = value.isoformat()
    return data


STATUSES: Dict[str, TaskStatus] = _load_statuses()

RUNNING_LOCK = threading.Lock()
RUNNING_FLAGS: Dict[str, bool] = {name: False for name in TASK_FUNCTIONS}


def _set_task_message(task_name: str, message: str) -> None:
    status = STATUSES.get(task_name)
    if not status:
        return
    status.message = message
    _save_statuses()

def _run_task(task_name: str):
    fn = TASK_FUNCTIONS[task_name]
    status = STATUSES[task_name]
    status.status = "running"
    status.started_at = datetime.utcnow()
    status.finished_at = None
    status.duration_seconds = None
    status.message = None
    _save_statuses()

    start = time.perf_counter()
    try:
        fn()
        status.status = "success"
    except Exception as exc:  # pragma: no cover
        status.status = "failed"
        status.message = str(exc)
    finally:
        status.finished_at = datetime.utcnow()
        status.duration_seconds = round(time.perf_counter() - start, 2)
        with RUNNING_LOCK:
            RUNNING_FLAGS[task_name] = False
        _save_statuses()

@app.post("/tasks/{task_name}")
async def trigger_task(task_name: str):
    if task_name not in TASK_FUNCTIONS:
        raise HTTPException(status_code=404, detail="task not found")
    with RUNNING_LOCK:
        if RUNNING_FLAGS[task_name]:
            raise HTTPException(status_code=409, detail="task already running")
        RUNNING_FLAGS[task_name] = True
    thread = threading.Thread(target=_run_task, args=(task_name,), daemon=True)
    thread.start()
    return {"message": f"task {task_name} started"}

@app.get("/tasks/status")
async def get_status():
    return {name: status.dict() for name, status in STATUSES.items()}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
