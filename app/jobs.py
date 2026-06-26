# create, claim, mark jobs
from sqlalchemy import text

def create_processing_job(conn, document_id: int, job_type: str = "process_document"):
    result = conn.execute(
        text(
            """
            INSERT INTO processing_jobs (
                document_id,
                job_type,
                job_status
            )
            VALUES (
                :documentt_id,
                :job_type,
                'pending'
            )
            RETURNING id
            """
        ), {
            "document_id": document_id,
            "job_type": job_type
        }
    )

    return result.scalar_one()


def claim_next_job(conn):
    result = conn.execute(
        text(
            """
                SELECT id
                FROM processing_jobs
                WHERE job_status = 'pending'
                ORDER BY created_at
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            """
        )
    )

    row = result.mappings().first()

    if row is None:
        return None
    
    job_id = row["id"]

    result = conn.execute(
        text(
            """
            UPDATE processing_jobs
            SET job_status = 'running',
                started_at = NOW(),
                updated_at = NOW()
            WHERE id = :job_id
            RETURNING
                id,
                document_id,
                job_type,
                job_status,
                retry_count,
                max_retries
            """
        ), {"job_id": job_id}
    )

    return result.mappings().one()      # exactly one row to be returned


def mark_job_completed(conn, job_id: int):
    conn.execute(
        text(
            """
                UPDATE processing_jobs
                SET job_status = 'completed',
                    completed_at = NOW(),
                    updated_at = NOW(),
                    error_msg = NULL
                WHERE id = :job_id
            """
        ), {"job_id": job_id}
    )


def mark_job_failed(conn, job_id: int, error_msg: str):
    conn.execute(
        text(
            """
                UPDATE processing_jobs
                SET job_status = 'failed',
                    completed_at = NOW(),
                    updated_at = NOW(),
                    error_msg = :error_msg
                WHERE id = :job_id
            """
        ), {
            "job_id": job_id,
            "error_msg": error_msg[:2000]
        }
    )