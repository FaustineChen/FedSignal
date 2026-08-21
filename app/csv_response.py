import csv
import io
import re

from fastapi.responses import StreamingResponse


def safe_filename_part(value):
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")
    return value


def build_report_filename(
    report_type: str,
    keyword: str | None = None,
    category: str | None = None,
) -> str:
    if keyword:
        target = safe_filename_part(keyword)
        target_type = "keyword"
    else:
        target = safe_filename_part(category)
        target_type = "category"

    return f"{target}_{target_type}_{report_type}.csv"


def make_csv_response(rows, filename: str):
    output = io.StringIO()
    rows = [dict(row) for row in rows]

    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )