import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from process_document_chunks import chunk_by_sentences

load_dotenv()

def main():
    document_id = 1
    max_chars = 1200

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is not set in .env")
    
    engine = create_engine(db_url)

    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT id, title, document_type, content
                FROM documents
                WHERE id = :document_id
                """
            ),
            {"document_id": document_id},
        )

        row = result.fetchone()
    
    if row is None:
        print(f"No document found with id = {document_id}")
    
    doc_id = row.id
    title = row.title
    document_type = row.document_type
    content = row.content

    print("=" * 20)
    print(f"Document ID: {doc_id}")
    print(f"Title: {title}")
    print(f"Type: {document_type}")
    print(f"Content length: {len(content)}")
    print("=" * 20)

    chunks = chunk_by_sentences(content, max_chars=max_chars, chunk_type="body")

    for i, chunk in enumerate(chunks[:10]):
        print(f"\n--- Chunk {i} | length={len(chunk['content'])} ---")
        print(f"chunk_type: {chunk['chunk_type']}")
        print(f"speaker: {chunk['speaker']}")
        print(chunk["content"])

    print("\nDone. This script only reads from DB and does not write anything.")


if __name__ == "__main__":
    main()