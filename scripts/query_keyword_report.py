import argparse
import csv
import re
from pathlib import Path
from sqlalchemy import text

from app.db import engine


def parse_args():
    parser = argparse.ArgumentParser(
        description="Query keyword occurrences from FedSignal database."
    )

    parser.add_argument(
        "--keyword",
        help="Canonical keyword to search, e.g. inflation expectations"
    )

    parser.add_argument(
        "--category",
        help="Keyword category to search, e.g. inflation_prices"
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

    # boolean, no parameter
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show aggregated occurrence counts instead of matched sentences"
    )

    parser.add_argument(
        "--summary-by",
        choices=["document", "date", "document_type", "keyword"],
        default="document",
        help="Aggregation level for summary mode"
    )

    parser.add_argument(
        "--document-id",
        type=int,
        help="Filter by document ID"
    )

    parser.add_argument(
        "--output",
        choices=["text", "csv"],
        default="test",
        help="Output format"
    )

    parser.add_argument(
        "--output-file",
        help="CSV output file path"
    )
    
    args = parser.parse_args()

    # need to be one of keyword or category
    if not args.keyword and not args.category:
        parser.error("Please provide either --keyword or --category.")

    if args.keyword and args.category:
        parser.error("Please provide only one of --keyword or --category, not both.")

    # summary-by only in summary mode
    if args.summary_by != "document" and not args.summary:
        parser.error("--summary-by can only be used with --summary.")
    
    return args

# build shared WHERE clause
def build_base_conditions(
    keyword=None,
    category=None,
    document_type=None,
    document_id=None,
    start_date=None,
    end_date=None,
    date_field="published",
):
    conditions = []
    params = {}

    if keyword is not None:
        conditions.append("LOWER(kc.keyword) = LOWER(:keyword)")
        params["keyword"] = keyword

    if category is not None:
        conditions.append("LOWER(kc.category) = LOWER(:category)")
        params["category"] = category

    if document_type is not None:
        conditions.append("d.document_type = :document_type")
        params["document_type"] = document_type

    if document_id is not None:
        conditions.append("d.id = :document_id")
        params["document_id"] = document_id

    # filter by date range
    if start_date is not None and end_date is not None:
        if date_field == "published":
            conditions.append(
                "d.published_date BETWEEN :start_date AND :end_date"
            )
        elif date_field == "event":
            conditions.append(
                """
                d.event_start_date IS NOT NULL
                AND d.event_end_date IS NOT NULL
                AND d.event_start_date <= :end_date
                AND d.event_end_date >= :start_date
                """
            )
        else:
            raise ValueError(f"Unsupported date_field: {date_field}")

        params["start_date"] = start_date
        params["end_date"] = end_date

    elif start_date is not None:
        if date_field == "published":
            conditions.append("d.published_date >= :start_date")
        elif date_field == "event":
            conditions.append(
                """
                d.event_end_date IS NOT NULL
                AND d.event_end_date >= :start_date
                """
            )
        else:
            raise ValueError(f"Unsupported date_field: {date_field}")

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


    return conditions, params


def query_matched_sentences(
    keyword=None,
    category=None,
    document_type=None,
    document_id=None,
    start_date=None,
    end_date=None,
    date_field="published",
    limit=20,
):
    conditions, params = build_base_conditions(
        keyword=keyword,
        category=category,
        document_type=document_type,
        document_id=document_id,
        start_date=start_date,
        end_date=end_date,
        date_field=date_field
    )

    where_clause = " AND ".join(conditions)

    params["limit"] = limit

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
            kc.category,
            ko.matched_text,
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

def get_report_date_expr(date_field):
    if date_field == "published":
        return "d.published_date"

    if date_field == "event":
        return "COALESCE(d.event_end_date, d.event_start_date)"

    raise ValueError(f"Unsupported date_field: {date_field}")

def query_summary(
    keyword=None,
    category=None,
    document_type=None,
    document_id=None,
    start_date=None,
    end_date=None,
    date_field="published",
    summary_by="document",
    limit=20
):
    conditions, params = build_base_conditions(
        keyword=keyword,
        category=category,
        document_type=document_type,
        document_id=document_id,
        start_date=start_date,
        end_date=end_date,
        date_field=date_field,
    )

    if summary_by == "document":
        select_clause = """
            d.id AS document_id,
            d.published_date,
            d.document_type,
            d.title,
            COUNT(*) AS occurrence_count
        """
        group_by_clause = """
            d.id,
            d.published_date,
            d.document_type,
            d.title
        """
        order_by_clause = """
            d.published_date DESC,
            occurrence_count DESC
        """

    elif summary_by == "date":
        date_expr = get_report_date_expr(date_field)

        # if grouping by event date, exclude documents with no event date.
        if date_field == "event":
            conditions.append(
                f"{date_expr} IS NOT NULL"
            )

        select_clause = f"""
            {date_expr} AS report_date,
            COUNT(*) AS occurrence_count
        """
        group_by_clause = date_expr
        order_by_clause = "report_date DESC"

    elif summary_by == "document_type":
        select_clause = """
            d.document_type,
            COUNT(*) AS occurrence_count
        """
        group_by_clause = "d.document_type"
        order_by_clause = "occurrence_count DESC"

    elif summary_by == "keyword":
        select_clause = """
            kc.keyword,
            kc.category,
            COUNT(*) AS occurrence_count
        """
        group_by_clause = """
            kc.keyword,
            kc.category
        """
        order_by_clause = "occurrence_count DESC"

    else:
        raise ValueError(f"Unsupported summary_by: {summary_by}")

    params["limit"] = limit
    where_clause = " AND ".join(conditions)

    sql = text(f"""
        SELECT
            {select_clause}
        FROM keyword_occurrences ko
        JOIN keyword_catalog kc
            ON ko.keyword_id = kc.id
        JOIN documents d
            ON ko.document_id = d.id
        WHERE {where_clause}
        GROUP BY
            {group_by_clause}
        ORDER BY
            {order_by_clause}
        LIMIT :limit
    """)

    with engine.connect() as conn:
        result = conn.execute(sql, params)
        return result.mappings().all()

def print_matched_sentences(rows):
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

        print(
            f"\nKeyword: {row['keyword']} | "
            f"Matched: {row['matched_text']} | "
            f"Chunk: {row['chunk_index']} | "
            f"Sentence: {row['sentence_index']}"
        )
        print(row["sentence"])

def print_summary(rows, summary_by):
    if not rows:
        print("No results found.")
        return

    print("\n" + "=" * 20)
    print(f"Summary by {summary_by}")
    print("=" * 20)

    for row in rows:
        if summary_by == "document":
            print(
                f"{row['published_date']} | "
                f"{row['document_type']} | "
                f"{row['occurrence_count']} | "
                f"{row['title']}"
            )

        elif summary_by == "date":
            print(
                f"{row['report_date']} | "
                f"{row['occurrence_count']}"
            )

        elif summary_by == "document_type":
            print(
                f"{row['document_type']} | "
                f"{row['occurrence_count']}"
            )

        elif summary_by == "keyword":
            print(
                f"{row['keyword']} | "
                f"{row['category']} | "
                f"{row['occurrence_count']}"
            )

def safe_filename_part(value):
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")
    return value

# create file name if not provide
# reports/<keyword_or_category name>_<keyword_or_category type>_<summary/matches>.csv
def get_output_file(args):
    if args.output_file:
        return args.output_file

    if args.keyword:
        target = safe_filename_part(args.keyword)
        target_type = "keyword"
    else:
        target = safe_filename_part(args.category)
        target_type = "category"

    if args.summary:
        report_type = "summary"
    else:
        report_type = "matches"

    return f"reports/{target}_{target_type}_{report_type}.csv"

def write_csv(rows, output_file):
    if not rows:
        print("No results found.")
        return
    
    output_path = Path(output_file)

    if output_path.parent != Path("."):
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # header
    fieldnames = list(rows[0].keys())

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows([dict(row) for row in rows])

    print(f"Wrote {len(rows)} rows to {output_path}")

def main():
    args = parse_args()

    if args.summary:
        rows = query_summary(
            keyword=args.keyword,
            category=args.category,
            document_type=args.document_type,
            document_id=args.document_id,
            start_date=args.start_date,
            end_date=args.end_date,
            date_field=args.date_field,
            summary_by=args.summary_by,
            limit=args.limit,
        )

        if args.output == "csv":
            if args.output_file:
                output_file = args.output_file
            else:
                output_file = get_output_file(args)
            write_csv(rows, output_file)
        else:
            print_summary(rows, args.summary_by)

    else:
        rows = query_matched_sentences(
            keyword=args.keyword,
            category=args.category,
            document_type=args.document_type,
            document_id=args.document_id,
            start_date=args.start_date,
            end_date=args.end_date,
            date_field=args.date_field,
            limit=args.limit,
        )

        if args.output == "csv":
            if args.output_file:
                output_file = args.output_file
            else:
                output_file = get_output_file(args)
            write_csv(rows, output_file)
        else:
            print_matched_sentences(rows)


if __name__ == "__main__":
    main()