# jobs API routes
from fastapi import APIRouter, HTTPException, status, Query
from typing import Literal

from app.db import engine
from queries.job_queries import get_jobs, get_job_by_id

router = APIRouter()

@router.get("")
def list_jobs(
    status: Literal["pending", "running", "completed", "failed"] | None = None,
    limit: int = Query(default=20, ge=1, le=100),
):
    with engine.begin() as conn:
        jobs = get_jobs(conn, job_status=status)

    return [dict(job) for job in jobs]


@router.get("/{job_id}")
def get_job(job_id: int):
    with engine.begin() as conn:
        job = get_job_by_id(conn, job_id)

    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return dict(job)