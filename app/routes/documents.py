# upload or insert document API
from fastapi import APIRouter, File, Form, UploadFile
from datetime import date
from pathlib import Path
from typing import Literal

from app.db import engine
from app.jobs import create_processing_job
from queries.document_queries import upsert_document

router = APIRouter()

DocumentType = Literal[
    "fomc_statement",
    "fomc_minutes",
    "press_conference",
]

@router.post("")
async def upload_document(
    file: UploadFile = File(...),

    title: str = Form(...),
    document_type: DocumentType = Form(...),

    published_date: date = Form(...),
    event_start_date: date | None = Form(None),
    event_end_date: date | None = Form(None),

    source: str = Form("Federal Reserve"),

    speaker: str | None = Form(None),
    speaker_position: str | None = Form(None),
    chair: str | None = Form(None),

    source_url: str = Form(...),
):
    # save uploaded PDF
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / file.filename

    contents = await file.read()

    with open(raw_path, "wb") as f:
        f.write(contents)

    # prepare document row
    row = {
        "title": title,
        "document_type": document_type,
        "published_date": published_date,
        "event_start_date": event_start_date,
        "event_end_date": event_end_date,
        "source": source,
        "speaker": speaker,
        "speaker_position": speaker_position,
        "chair": chair,
        "source_url": source_url,
        "raw_file_path": str(raw_path),
        "cleaned_file_path": None,
        "content": None,
    }
    

    # insert/upsert document + create pending job
    with engine.begin() as conn:
        document_id = upsert_document(conn, row)

        job_id = create_processing_job(
            conn=conn,
            document_id=document_id,
            job_type="process_document"
        )

    # API response
    return {
        "document_id": document_id,
        "job_id": job_id,
        "job_status": "pending",
    }