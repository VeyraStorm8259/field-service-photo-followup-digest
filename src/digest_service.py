"""HTTP entry points for digest generation and weekly schedule registration."""

from __future__ import annotations

from hashlib import sha256

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from . import infrai
from .field_service_digest import DigestRequest, DigestResult, build_weekly_digest
from .infrai import InfraiError

app = FastAPI(title="Field-service weekly digest")


class ScheduleRequest(BaseModel):
    task_url: HttpUrl


class ScheduleResult(BaseModel):
    job_id: str


@app.post("/digest/weekly", response_model=DigestResult)
def receive_weekly_digest(request: DigestRequest) -> DigestResult:
    return build_weekly_digest(request)


@app.post("/schedules/weekly", response_model=ScheduleResult)
def register_weekly_digest(request: ScheduleRequest) -> ScheduleResult:
    task_url = str(request.task_url)
    cron_expr = "0 14 * * 5"
    stable_key = sha256(f"field-service-weekly:{task_url}:{cron_expr}".encode()).hexdigest()
    try:
        data = infrai.cron.create(
            cron_expr=cron_expr,
            task=task_url,
            idempotency_key=stable_key,
        )
    except InfraiError as error:
        client_status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(status_code=client_status, detail=dict(error.details)) from error
    return ScheduleResult(job_id=str(data["job_id"]))
