from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import insert

from app.models import Document

# Upsert metadata and raw file information for an uploaded document.
# On conflict, preserve existing processed content (and cleande file path)
# because the new upload has not been processed yet.
# Reprocessing will update those fields later.
# Always update on the same source URL because the underlying PDF may have changed
# even when its metadata and file path remain the same.
def upsert_document(conn, row:dict) -> int:
    stmt = insert(Document).values(row)
    stmt = stmt.on_conflict_do_update(
        index_elements=["source_url"],

        # stmt.excluded -> url exists, update
        set_={
            "title": stmt.excluded.title,
            "document_type": stmt.excluded.document_type,
            "published_date": stmt.excluded.published_date,
            "event_start_date": stmt.excluded.event_start_date,
            "event_end_date": stmt.excluded.event_end_date,
            "source": stmt.excluded.source,
            "speaker": stmt.excluded.speaker,
            "speaker_position": stmt.excluded.speaker_position,
            "chair": stmt.excluded.chair,
            "raw_file_path": stmt.excluded.raw_file_path,
            "updated_at": func.now(),
        },
    ).returning(Document.id)

    result = conn.execute(stmt)

    document_id = result.scalar_one()

    return document_id

"""
scripts/ingest_documents.py
    def upsert_documents(rows: list[dict]) -> None:
"""