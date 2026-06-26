# input: documents table, contect
# outpiut: document_chunks table
import re
import sys
import argparse
from pathlib import Path
from sqlalchemy import text

# import prot project root
# project_root = Path(__file__).resolve().parents[1]
# sys.path.append(str(project_root))

from app.db import engine


def protect_abbreviation(text : str) -> str:
    replacements = {
        "U.S.": "US_ABBR",
        "Mr.": "MR_ABBR",
        "Ms.": "MS_ABBR",
        "Dr.": "DR_ABBR",
        "p.m.": "PM_ABBR",
        "a.m.": "AM_ABBR",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def restore_abbreviation(text: str) -> str:
    replacements = {
        "US_ABBR": "U.S.",
        "MR_ABBR": "Mr.",
        "MS_ABBR": "Ms.",
        "DR_ABBR": "Dr.",
        "PM_ABBR": "p.m.",
        "AM_ABBR": "a.m.",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def split_into_sentences(text: str) -> list[str]:
    # whitespace normalize to " "
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []
    
    protected = protect_abbreviation(text)

    # sentence ends with ., ?, ! followed by whitespace
    protected_sentences = re.split(r"(?<=[.!?])\s+", protected)
    sentences = []
    for s in protected_sentences:
        s = s.strip()
        if s:
            sentences.append(restore_abbreviation(s))
    
    return sentences

# split by speaker
# return[{"speaker": "CHAIR POWELL", "content": "..."},
#        {"speaker": "NICK TIMIRAOS", "content": "..."}]
def split_speaker_truns(content: str) -> list[dict]:
    text = content.strip()

    # find from the begining of each sentence that all the letters are uppercase and ends with '.'
    pattern = re.compile(r"(?m)^([A-Z][A-Z\s.'-]+?)\.\s+")

    # [CHAIR POWELL, NICK TIMIRAOS, ...]
    matches = list(pattern.finditer(text))
    turns = []

    for i, match in enumerate(matches):
        speaker = match.group(1).strip()
        content_start = match.end()

        # not the last speaker
        if i + 1 < len(matches):
            content_end = matches[i + 1].start()
        else:
            content_end = len(text)
        
        turn_content = text[content_start:content_end].strip()
        # whitespace normalize to " "
        turn_content = re.sub(r"\s+", " ", turn_content).strip()

        if turn_content:
            turns.append({"speaker": speaker, "content": turn_content})

    return turns

def remove_statement_boilerplate(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()

    # Remove media inquiry boilerplate at the end of a paragraph
    text = re.sub(
        r"\s*Attachment\s+For media inquiries, please email .*?@.*? or call \d{3}-\d{3}-\d{4}\.?\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*For media inquiries, please email .*?@.*? or call \d{3}-\d{3}-\d{4}\.?\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # If only "Attachment" remains as a paragraph
    text = re.sub(
        r"^\s*Attachment\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    return text.strip()

# minutes
# sentence-based chunking
def chunk_by_sentences(
    content: str,
    max_chars: int = 1200,
    chunk_type: str = "body",
    speaker: str | None = None,
) -> list[dict]:
    # whitespace normalize to " "
    sentences = split_into_sentences(content)

    chunks = []
    current = []
    curr_len = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        # one sentence is longer than 1200 chars
        if sentence_len > max_chars:
            # if there are sentences in current, store into one chunk
            if current:
                chunk_text = " ".join(current).strip()
                chunks.append({
                    "chunk_type": chunk_type,
                    "speaker": speaker,
                    "content": chunk_text,
                })
                current = []
                curr_len = 0

            # then store current sentence to another chunk
            chunks.append({
                "chunk_type": chunk_type,
                "speaker": speaker,
                "content": sentence,
            })
            continue
        
        # count the length if add the new sentence
        chunk_len = curr_len + sentence_len + (1 if current else 0)

        # <= max chars
        # add the new sentence
        if chunk_len <= max_chars:
            current.append(sentence)
            curr_len = chunk_len
        # > max chars
        # store sentences in current into one chunk
        # then store current sentence to another chunk
        else:
            chunk_text = " ".join(current).strip()
            chunks.append({
                "chunk_type": chunk_type,
                "speaker": speaker,
                "content": chunk_text,
            })
            current = [sentence]
            curr_len = sentence_len
    if current:
        chunk_text = " ".join(current).strip()
        chunks.append({
            "chunk_type": chunk_type,
            "speaker": speaker,
            "content": chunk_text,
        })
    
    return chunks

# chunk by speaker
def chunk_press_conference(content: str, max_chars: int = 1200) -> list[dict]:
    # split to speaker truns
    turns = split_speaker_truns(content)

    chunks = []
    for turn in turns:
        speaker = turn["speaker"]
        turn_content = turn["content"]

        if len(turn_content) <= max_chars:
            chunks.append({
                "speaker": speaker,
                "chunk_type": "speaker_turn",
                "content": turn_content
            })
        # content is linger then max_chars
        # split it but keep the same speaker
        else:
            sub_chunks = chunk_by_sentences(
                turn_content,
                max_chars=max_chars,
                chunk_type="speaker_turn",
                speaker=speaker
            )
            for sub_chunk in sub_chunks:
                chunks.append({
                    "speaker": speaker,
                    "chunk_type": "speaker_turn",
                    "content": sub_chunk["content"]
                })

    return chunks


# chunk by paragraph
def chunk_statement(
    content: str,
    max_chars: int = 1200,
    chunk_type: str = "paragraph",
    speaker: str | None = None,
) -> list[dict]:
    raw_paragraphs = re.split(r"\n\s*\n+", content.strip())
    chunks = []

    # content already remove header/footer
    # remove statement boilerplate
    for paragraph in raw_paragraphs:
        paragraph = paragraph.strip()

        # whitespace normalize to " "
        paragraph = re.sub(r"\s+", " ", paragraph).strip()

        # remove boilerplate
        paragraph = remove_statement_boilerplate(paragraph)

        if not paragraph:
            continue

        # split if the paragraph is too long
        if len(paragraph) <= max_chars:
            chunks.append({
                "speaker": speaker,
                "chunk_type": chunk_type,
                "content": paragraph
            })
        else:
            sub_chunks = chunk_by_sentences(
                paragraph,
                max_chars=max_chars,
                chunk_type=chunk_type,
                speaker=speaker
            )
            chunks.extend(sub_chunks)
    return chunks
    

def chunk_document(content: str, document_type: str, max_chars: int = 1200) -> list[dict]:
    if document_type == "fomc_statement":
        return chunk_statement(content, max_chars=max_chars)
    elif document_type == "press_conference":
        return chunk_press_conference(content, max_chars=max_chars)
    elif document_type == "fomc_minutes":
        return chunk_by_sentences(content, max_chars=max_chars)
    else:
        return chunk_by_sentences(content, max_chars=max_chars)
    

# fetch documents from documents table
# if document_id is provided, fetch one document
def fetch_documents(conn, document_id: int | None = None):
    # one doc
    if document_id is not None:
        result = conn.execute(
            text(
                """
                SELECT id, title, document_type, content
                FROM documents
                WHERE id = :document_id
                """
            ), {"document_id": document_id}
        )
    # all doc
    else:
        result = conn.execute(
            text(
                """
                SELECT id, title, document_type, content
                FROM documents
                """
            )
        )
    # fetch query results as a collection of dictionary-like mapping objects
    return result.mappings().all()

# replace all chunks for one doc
# delete old chunks then generate new one
def replace_document_chunks(conn, document_id: int, chunks: list[dict]) -> None:
    conn.execute(
        text(
            """
            DELETE FROM document_chunks
            WHERE document_id = :document_id
            """
        ), {"document_id": document_id}
    )

    # this doc has no (newly processed) chunks
    if not chunks:
        return
    
    rows = []   # store the data need to insert to document_chunks table
    for i, chunk in enumerate(chunks):
        chunk_text = chunk["content"].strip()

        if not chunk_text:
            continue

        rows.append(
            {
                "document_id": document_id,
                "chunk_index": i,
                "chunk_text": chunk_text,
                "chunk_type": chunk.get("chunk_type", "body"),   # get chunk type, ow return "body as default"
                "speaker": chunk.get("speaker"),
                "char_start": None,
                "char_end": None,
            }
        )
    
    if not rows:
        return
    
    conn.execute(
        text(
            """
            INSERT INTO document_chunks(
                document_id,
                chunk_index,
                chunk_text,
                chunk_type,
                speaker,
                char_start,
                char_end
            )
            VALUES(
                :document_id,
                :chunk_index,
                :chunk_text,
                :chunk_type,
                :speaker,
                :char_start,
                :char_end
            )
            """
        ), rows
    )

# core logic
# process one or all documents
def generate_chunks_for_documents(
    conn,
    dry_run: bool = False,
    document_id: int | None = None,
    max_chars: int = 1200,
) -> None:
    documents = fetch_documents(conn, document_id=document_id)
    
    if not documents:
        print("No documents found.")
        return
    
    total_chunks = 0

    for doc in documents:
        doc_id = doc["id"]
        title = doc["title"]
        document_type = doc["document_type"]
        content = doc["content"]

        chunks = chunk_document(
            content=content,
            document_type=document_type,
            max_chars=max_chars
        )

        # print doc metadata
        print("=" * 20)
        print(f"Document ID: {doc_id}")
        print(f"Title: {title}")
        print(f"Type: {document_type}")
        print(f"Generated chunks: {len(chunks)}")

        # print preview
        if chunks:
            first_chunk = chunks[0]
            print("--- First chunk preview ---")
            print(f"chunk_type: {first_chunk.get('chunk_type')}")
            print(f"speaker: {first_chunk.get('speaker')}")
            print(first_chunk.get("content", "")[:500])

        if dry_run:
            print("Dry run: not writting chunks to database.")
        else:
            replace_document_chunks(
                conn=conn,
                document_id=doc_id,
                chunks=chunks
            )
            print("Inserted chunks into document_chunks.")
        
        total_chunks += len(chunks)
    
    print("=" * 20)
    print(f"Processed documents: {len(documents)}")
    print(f"Total generated chunks: {total_chunks}")

    if dry_run:
        print("Dry run complete. No database changes were made.")
    else:
        print("Done. document_chunks table has been updated.")

# CLI wrapper
# open engine.begin() itself
def process_documents(
    dry_run: bool = False,
    document_id: int | None = None,
    max_chars: int = 1200,
) -> None:
    with engine.begin() as conn:
        generate_chunks_for_documents(
            conn,
            dry_run=dry_run,
            document_id=document_id,
            max_chars=max_chars,
        )

# worker wrapper
# process one document
def generate_chunks_for_document(
    conn,
    document_id: int,
    max_chars: int = 1200   
) -> None:
    generate_chunks_for_documents(
        conn=conn,
        dry_run=False,
        document_id=document_id,
        max_chars=max_chars
    )


def main():
    # create command line parser
    parser = argparse.ArgumentParser(
        description="Process documents into chunks and write them to document_chunks."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate chunks and print preview, but do not write to database."
    )

    parser.add_argument(
    "--document-id",
    type=int,
    default=None,
    help="Only process one document by id.",
    )

    parser.add_argument(
        "--max-chars",
        type=int,
        default=1200,
        help="Maximum characters per chunk.",
    )

    args = parser.parse_args()

    process_documents(
        dry_run=args.dry_run,
        document_id=args.document_id,
        max_chars=args.max_chars,
    )

if __name__ == "__main__":
    main()