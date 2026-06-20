import re
import sys
import argparse
from pathlib import Path
from sqlalchemy import text

# import prot project root
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from app.db import engine
from process_document_chunks import split_into_sentences

# convert keyword term into regex pattern
def compile_pattern(term: str, match_type: str):
    if match_type == "word":
        escaped = re.escape(term)       # adds a backslash (\) escape character before special characters in a text string
        pattern = rf"(?<!\w){escaped}(?!\w)"    # the character immediately preceding/following the term cannot be a word character
        return re.compile(pattern, flags=re.IGNORECASE)     # compiles a regular expression pattern string into a regex Pattern object
    
    elif match_type == "exact_phrase":
        escaped = re.escape(term)
        pattern = rf"(?<!\w){escaped}(?!\w)"
        return re.compile(pattern, flags=re.IGNORECASE)

    elif match_type == "regex":
        return re.compile(term, flags=re.IGNORECASE)

    else:
        raise ValueError(f"Unknown match_type: {match_type}")
    

# load keyword terms table to memory
# add pattern for each term
def load_key_word_terms(conn):
    result = conn.execute(
        text(
            """
            SELECT 
                kt.id AS keyword_term_id,
                kt.keyword_id,
                kt.term,
                kt.match_type
            FROM keyword_terms kt
            ORDER BY LENGTH(kt.term) DESC
            """
        )
    )

    terms = []

    for row in result.mappings():
        pattern = compile_pattern(row["term"], row["match_type"])

        terms.append(
            {
                "keyword_term_id": row["keyword_term_id"],
                "keyword_id": row["keyword_id"],
                "term": row["term"],
                "match_type": row["match_type"],
                "pattern": pattern,
            }
        )

    return terms

# can process one chunk, one doc, all doc
def fetch_chunks(conn, document_id=None, chunk_id=None):
    # fetch one chunk
    if chunk_id is not None:
        result = conn.execute(
            text(
                """
                SELECT
                    id AS chunk_id,
                    document_id,
                    chunk_index,
                    chunk_text
                FROM document_chunks
                WHERE id = :chunk_id
                ORDER BY document_id, chunk_index
                """
            ), {"chunk_id": chunk_id}
        )
    # fetch one document
    elif document_id is not None:
        result = conn.execute(
            text(
                """
                SELECT
                    id AS chunk_id,
                    document_id,
                    chunk_index,
                    chunk_text
                FROM document_chunks
                WHERE document_id = :document_id
                """
            ), {"document_id": document_id}
        )
    # fetch all documents
    else:
        result = conn.execute(
            text(
                """
                SELECT
                    id AS chunk_id,
                    document_id,
                    chunk_index,
                    chunk_text
                FROM document_chunks
                ORDER BY document_id, chunk_index
                """
            )
        )

    return result.mappings().all()

# find keyword occurrences in one chunk
    # get one chunk of chunks from fetch_chunks()
    # keyword_terms from load_key_word_terms()
# char is relative to sentence
# sentence index start from 0 within each chunk
def find_occurrences_in_chunk(chunk, keyword_terms):
    occurrences = []
    seen_occurrences = set()

    chunk_id = chunk["chunk_id"]
    document_id = chunk["document_id"]
    chunk_text = chunk["chunk_text"]

    sentences = split_into_sentences(chunk_text)

    # longer terms first
    keyword_terms = sorted(
        keyword_terms,
        key=lambda term: len(term["term"]),
        reverse=True,
    )

    for sentence_index, sentence in enumerate(sentences):
        for term in keyword_terms:
            pattern = term["pattern"]

            for match in pattern.finditer(sentence):
                dedup_key = (
                    term["keyword_id"],
                    sentence_index,
                )

                if dedup_key in seen_occurrences:
                    continue

                seen_occurrences.add(dedup_key)
                
                occurrences.append(
                    {
                        "keyword_id": term["keyword_id"],
                        "keyword_term_id": term["keyword_term_id"],
                        "document_id": document_id,
                        "chunk_id": chunk_id,
                        "sentence_index": sentence_index,
                        "char_start": match.start(),
                        "char_end": match.end(),
                        "matched_text": match.group(0),
                        "sentence": sentence,
                    }
                )

    return occurrences

# delete existing occurrences for chunks being processed
# safe to rerun script
# get chunks from fetch_chunks()
def delete_existing_occurrences(conn, chunks):
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]

    if not chunk_ids:
        return
    
    conn.execute(
        text(
            """
            DELETE FROM keyword_occurrences
            WHERE chunk_id = ANY(:chunk_ids)
            """
        ), {"chunk_ids": chunk_ids}
    )


# insert occurrences list to keyword_occurrences table
def insert_occurrences(conn, occurrences):
    if not occurrences:
        return
    
    conn.execute(
        text(
            """
            INSERT INTO keyword_occurrences (
                keyword_id,
                keyword_term_id,
                document_id,
                chunk_id,
                sentence_index,
                char_start,
                char_end,
                matched_text,
                sentence
            )
            VALUES (
                :keyword_id,
                :keyword_term_id,
                :document_id,
                :chunk_id,
                :sentence_index,
                :char_start,
                :char_end,
                :matched_text,
                :sentence
            )
            """
        ), occurrences
    )

def process_keyword_occurrences(dry_run=False, document_id=None, chunk_id=None):
    with engine.begin() as conn:
        keyword_terms = load_key_word_terms(conn)
        chunks = fetch_chunks(conn, document_id=document_id, chunk_id=chunk_id)

        print(f"Loaded keyword terms: {len(keyword_terms)}")
        print(f"Loaded chunks: {len(chunks)}")

        all_occurrences = []

        for chunk in chunks:
            occurrences = find_occurrences_in_chunk(chunk, keyword_terms)
            all_occurrences.extend(occurrences)

        print(f"Generated occurrences: {len(all_occurrences)}")

        if all_occurrences:
            print("\nPreview first 10 occurrences:")
            for occurrence in all_occurrences[:10]:
                print("=" * 20)
                print(f"document_id: {occurrence['document_id']}")
                print(f"chunk_id: {occurrence['chunk_id']}")
                print(f"keyword_id: {occurrence['keyword_id']}")
                print(f"keyword_term_id: {occurrence['keyword_term_id']}")
                print(f"matched_text: {occurrence['matched_text']}")
                print(f"sentence_index: {occurrence['sentence_index']}")
                print(f"char_start: {occurrence['char_start']}")
                print(f"char_end: {occurrence['char_end']}")
                print(f"sentence: {occurrence['sentence'][:300]}")

        if dry_run:
            print("\nDry run complete. No database changes were made.")
            return

        delete_existing_occurrences(conn, chunks)
        insert_occurrences(conn, all_occurrences)

        print("\nInserted keyword occurrences into database.")

    
def main():
    parser = argparse.ArgumentParser(
        description="Find keyword occurrences in document chunks."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview keyword occurrences without writing to database.",
    )

    parser.add_argument(
        "--document-id",
        type=int,
        default=None,
        help="Only process chunks for one document.",
    )

    parser.add_argument(
        "--chunk-id",
        type=int,
        default=None,
        help="Only process one chunk.",
    )

    args = parser.parse_args()

    process_keyword_occurrences(
        dry_run=args.dry_run,
        document_id=args.document_id,
        chunk_id=args.chunk_id,
    )


if __name__ == "__main__":
    main()