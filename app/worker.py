# async worker
# find pending job
# mark as processing
# process document
    # run generate chunks
    # run extract occurrences
# mark as completed

import time
import traceback
from pathlib import Path

from app.db import engine
from app.jobs import claim_next_job, mark_job_completed, mark_job_failed
from scripts.file_utils import save_text
from scripts.extract_pdf_text import extract_text_from_pdf
from scripts.clean_processed_text import clean_text
from scripts.process_document_chunks import generate_chunks_for_document
from scripts.process_keyword_occurrences import extract_occurrences_for_document
from queries.document_queries import get_document, update_document_content


def run_job(job):
    document_id = job["document_id"]
    job_type = job["job_type"]

    if job_type == "process_document":
        with engine.begin() as conn:
            document = get_document(conn, document_id)

            if document is None:
                raise ValueError(
                    f"Document {document_id} not found"
                )

            if not document["content"]:
                pdf_path = Path(document["raw_file_path"])
                processed_path = (Path("data/processed") / pdf_path.with_suffix(".txt").name)
                cleaned_file_path = (Path("data/cleaned") / pdf_path.with_suffix(".txt").name)

                # extract
                raw_text = extract_text_from_pdf(path=pdf_path)

                # save processed txt
                save_text(raw_text, processed_path)

                # clean
                cleaned_text = clean_text(raw_text)

                # save cleaned txt
                save_text(cleaned_text, cleaned_file_path)

                # update documents.content
                update_document_content(
                    conn,
                    document_id=document_id,
                    content=cleaned_text,
                    cleaned_file_path=str(cleaned_file_path),
                )

            generate_chunks_for_document(conn, document_id)
            extract_occurrences_for_document(conn, document_id)
    
    else:
        raise ValueError(f"Unsupported job_type: {job_type}")


def worker_loop(poll_seconds: int = 5):
    while True:
        # Transaction 1: claim job
        with engine.begin() as conn:
            job = claim_next_job(conn)
        
        if job is None:
            print("No pending jobs. Sleeping...")
            time.sleep(poll_seconds)
            continue
        
        job_id = job["id"]
        print(f"Claimed job {job_id}, type={job['job_type']}, document_id={job['document_id']}")

        try:
            # Transaction 2: process document
            run_job(job)

            # Transaction 3: mark completed/failed
            with engine.begin() as conn:
                mark_job_completed(conn, job_id)

            print(f"Completed job {job_id}")

        except Exception as e:
            error_msg = traceback.format_exc()

            # Transaction 3: mark completed/failed
            with engine.begin() as conn:
                mark_job_failed(conn, job_id, error_msg)

            print(f"Failed job {job_id}: {e}")

if __name__ == "__main__":
    try:
        worker_loop()
    except KeyboardInterrupt:
        print("\nWorker stopped.")