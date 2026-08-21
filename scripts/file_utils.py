import csv
import re
from pathlib import Path

def save_text(text: str, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


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