# read metadata.csv
# insert cleaned text into documents table

import csv
from pathlib import Path
from datetime import datetime
from typing import Optional

from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import insert

from app.db import SessionLocal
from app.models import Document
from app.jobs import create_processing_job

BASE_DIR = Path(__file__).resolve().parents[1]

METADATA_CSV = BASE_DIR / "data" / "metadata" / "fed_documents.csv"
CLEANED_TEXT_DIR = BASE_DIR / "data" / "cleaned"

def parse_date(value: Optional[str]):
    if value is None:
        return None
    
    value = value.strip()
    if value == "":
        return None
    
    return datetime.strptime(value, "%Y/%m/%d").date()

def optional_str(value: Optional[str]):
    if value is None:
        return None

    value = value.strip()
    return value if value else None

def read_cleaned_text(filename: str) -> str:
    file_path = CLEANED_TEXT_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Missing cleaned text file: {file_path}")
  
    return file_path.read_text(encoding="utf-8").strip()

def load_rows_from_csv() -> list[dict]:
    rows = []

    with METADATA_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):
            try:
                filename = row["filename"].strip()
                content = read_cleaned_text(filename)

                rows.append({
                    "title": row["title"].strip(),
                    "document_type": row["document_type"].strip(),
                    "published_date": parse_date(row["published_date"]),
                    "event_start_date": parse_date(row.get("event_start_date")),
                    "event_end_date": parse_date(row.get("event_end_date")),
                    "source": row["source"].strip(),
                    "speaker": optional_str(row.get("speaker")),
                    "speaker_position": optional_str(row.get("speaker_position")),
                    "chair": optional_str(row.get("chair")),
                    "source_url": row["source_url"].strip(),
                    "raw_file_path": optional_str(row.get("raw_file_path")),
                    "cleaned_file_path": optional_str(row.get("cleaned_file_path")),
                    "content": content,
                })
            except Exception as e:
                raise RuntimeError(f"Error processing CSV row {row_num}: {row}") from e
        
    return rows

def upsert_documents(rows: list[dict]) -> None:
    if not rows:
        print("No documents found.")
        return
    
    session = SessionLocal()

    try:
        stmt = insert(Document).values(rows)
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
                "cleaned_file_path": stmt.excluded.cleaned_file_path,
                "content": stmt.excluded.content,
                "updated_at": func.now(),
            },
            where=(     # at least one of the data is different
                (Document.title.is_distinct_from(stmt.excluded.title)) |
                (Document.document_type.is_distinct_from(stmt.excluded.document_type)) |
                (Document.published_date.is_distinct_from(stmt.excluded.published_date)) |
                (Document.event_start_date.is_distinct_from(stmt.excluded.event_start_date)) |
                (Document.event_end_date.is_distinct_from(stmt.excluded.event_end_date)) |
                (Document.source.is_distinct_from(stmt.excluded.source)) |
                (Document.speaker.is_distinct_from(stmt.excluded.speaker)) |
                (Document.speaker_position.is_distinct_from(stmt.excluded.speaker_position)) |
                (Document.chair.is_distinct_from(stmt.excluded.chair)) |
                (Document.raw_file_path.is_distinct_from(stmt.excluded.raw_file_path)) |
                (Document.cleaned_file_path.is_distinct_from(stmt.excluded.cleaned_file_path)) |
                (Document.content.is_distinct_from(stmt.excluded.content))
            ),
        ).returning(Document.id)        # only return doc_id need to insert or update

        result = session.execute(stmt)
        changed_document_ids = result.scalars().all()
        created_job_count = 0

        for document_id in changed_document_ids:
            job_id = create_processing_job(
                conn=session,
                document_id=document_id,
                job_type="process_document"
            )
            created_job_count += 1
            print(f"Created job {job_id} for document {document_id}.")

        session.commit()
        
        print(f"Read {len(rows)} documents from CSV.")
        print(f"Upserted {len(changed_document_ids)} documents.")
        print(f"Created {created_job_count} processing jobs.")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()

def main():
    rows = load_rows_from_csv()
    upsert_documents(rows)

if __name__ == "__main__":
    main()

