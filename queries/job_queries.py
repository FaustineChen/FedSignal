from sqlalchemy import text


def get_jobs(
    conn,
    job_type=None,
    job_status=None,
    limit=20,
):
    query = """
        SELECT
            id,
            document_id,
            job_type,
            job_status,
            created_at,
            updated_at,
            started_at,
            completed_at,
            retry_count,
            max_retries,
            error_msg
        FROM processing_jobs
        WHERE 1 = 1
    """

    params = {"limit": limit}

    if job_type is not None:
        query += " AND job_type = :job_type"
        params["job_type"] = job_type

    if job_status is not None:
        query += " AND job_status = :job_status"
        params["job_status"] = job_status

    query += " ORDER BY created_at DESC"
    query += " LIMIT :limit"

    result = conn.execute(text(query), params)

    return result.mappings().all()


def get_job_by_id(conn, job_id: int):
    result = conn.execute(
        text("""
            SELECT
                id,
                document_id,
                job_type,
                job_status,
                created_at,
                updated_at,
                started_at,
                completed_at,
                retry_count,
                max_retries,
                error_msg
            FROM processing_jobs
            WHERE id = :job_id
        """),
        {"job_id": job_id},
    )

    return result.mappings().first()