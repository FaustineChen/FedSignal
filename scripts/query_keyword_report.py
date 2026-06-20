import argparse
import sys
from pathlib import Path
from sqlalchemy import text

# import prot project root
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))
from app.db import engine


def parse_args():
    parser = argparse.ArgumentParser(
        description="Query keyword occurrences from FedSignal database."
    )

    parser.add_argument(
        "--keyword",
        required=True,
        help="Canonical keyword to search, e.g. inflation expectations"
    )

    parser.add_argument(
        "--document-type",
        choices=["fomc_statement", "fomc_minutes", "press_conference"],
        help="Filter by document type"
    )

    parser.add_argument(
        "--start-date",
        help="Start date, format YYYY-MM-DD"
    )

    parser.add_argument(
        "--end-date",
        help="End date, format YYYY-MM-DD"
    )

    parser.add_argument(
        "--date-field",
        choices=["published", "event"],
        default="published",
        help="Use published_date or event date range for filtering"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of results to show"
    )

    return parser.parse_args()


def query_keyword_report(
    keyword,
    document_type=None,
    start_date=None,
    end_date=None,
    date_field="published",
    limit=20,
):
    # store query WHERE conditions
    conditions = [
        "LOWER(kc.keyword) = LOWER(:keyword)"
    ]

    params = {
        "keyword": keyword,
        "limit": limit,
    }

    if document_type is not None:
        conditions.append("d.document_type = :document_type")
        params["document_type"] = document_type

    # filter by date range
    if start_date is not None and end_date is not None:
        if date_field == "published":
            conditions.append(
                "d.published_date BETWEEN :start_date AND :end_date"
            )
        else:
            conditions.append(
                """
                d.event_start_date IS NOT NULL
                AND d.event_end_date IS NOT NULL
                AND d.event_start_date <= :end_date
                AND d.event_end_date >= :start_date
                """
            )

        params["start_date"] = start_date
        params["end_date"] = end_date

    elif start_date is not None:
        if date_field == "published":
            conditions.append("d.published_date >= :start_date")
        else:
            conditions.append(
                """
                d.event_end_date IS NOT NULL
                AND d.event_end_date >= :start_date
                """
            )

        params["start_date"] = start_date

    elif end_date is not None:
        if date_field == "published":
            conditions.append("d.published_date <= :end_date")
        else:
            conditions.append(
                """
                d.event_start_date IS NOT NULL
                AND d.event_start_date <= :end_date
                """
            )

        params["end_date"] = end_date

    where_clause = " AND ".join(conditions)

    sql = text(f"""
        SELECT
            d.id AS document_id,
            d.title,
            d.document_type,
            d.published_date,
            d.event_start_date,
            d.event_end_date,
            d.speaker,
            d.chair,
            dc.chunk_index,
            kc.keyword,
            ko.sentence_index,
            ko.sentence,
            ko.char_start,
            ko.char_end
        FROM keyword_occurrences ko
        JOIN keyword_catalog kc
            ON ko.keyword_id = kc.id
        JOIN documents d
            ON ko.document_id = d.id
        LEFT JOIN document_chunks dc
            ON ko.chunk_id = dc.id
        WHERE {where_clause}
        ORDER BY
            d.published_date DESC,
            d.id,
            dc.chunk_index,
            ko.sentence_index
        LIMIT :limit
    """)

    with engine.connect() as conn:
        result = conn.execute(sql, params)
        return result.mappings().all()


def print_report(rows):
    if not rows:
        print("No results found.")
        return

    current_document_id = None

    for row in rows:
        if row["document_id"] != current_document_id:
            current_document_id = row["document_id"]

            print("\n" + "=" * 20)
            print(f"{row['published_date']} | {row['document_type']}")
            print(f"{row['title']}")
            print(f"Document ID: {row['document_id']}")

            if row["event_start_date"] or row["event_end_date"]:
                print(
                    f"Event: {row['event_start_date']} to {row['event_end_date']}"
                )

            if row["speaker"]:
                print(f"Speaker: {row['speaker']}")

            if row["chair"]:
                print(f"Chair: {row['chair']}")

            print("=" * 20)

        print(f"\nChunk: {row['chunk_index']} | Sentence: {row['sentence_index']}")
        print(row["sentence"])


def main():
    args = parse_args()

    rows = query_keyword_report(
        keyword=args.keyword,
        document_type=args.document_type,
        start_date=args.start_date,
        end_date=args.end_date,
        date_field=args.date_field,
        limit=args.limit,
    )

    print_report(rows)


if __name__ == "__main__":
    main()