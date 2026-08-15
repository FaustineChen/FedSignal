from app.db import engine
from app.jobs import create_processing_job

document_ids = [1, 4, 7, 64, 3, 6, 9, 67]

with engine.begin() as conn:
    for document_id in document_ids:
        job_id = create_processing_job(
            conn,
            document_id=document_id,
            job_type="process_document"
        )
        print(f"Created job {job_id} for document {document_id}")