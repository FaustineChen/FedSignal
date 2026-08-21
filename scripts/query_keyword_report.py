import argparse
import csv
import re
from pathlib import Path

from queries.report_queries import query_summary, query_matched_sentences
from scripts.file_utils import get_output_file, write_csv


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