# report API routes
from fastapi import APIRouter
from queries.report_queries import query_summary, query_matched_sentences
from app.csv_response import build_report_filename, make_csv_response


router = APIRouter()

@router.get("/matches")
def get_matches(
    keyword=None,
    category=None,
    document_type=None,
    document_id=None,
    start_date=None,
    end_date=None,
    date_field="published",
    limit=20,   
):
    rows = query_matched_sentences(
        keyword=keyword,
        category=category,
        document_type=document_type,
        document_id=document_id,
        start_date=start_date,
        end_date=end_date,
        date_field=date_field,
        limit=limit,
    )
    
    return rows


@router.get("/summary")
def get_summary(
    keyword: str = None,
    category: str = None,
    document_type: str = None,
    document_id: int = None,
    start_date: str = None,
    end_date: str = None,
    date_field: str = "published",
    summary_by: str = "document",
    limit: int = 20,
):
    rows = query_summary(
        keyword=keyword,
        category=category,
        document_type=document_type,
        document_id=document_id,
        start_date=start_date,
        end_date=end_date,
        date_field=date_field,
        summary_by=summary_by,
        limit=limit,
    )

    return rows


@router.get("/matches/export")
def export_matches(
    keyword: str | None = None,
    category: str | None = None,
    document_type: str | None = None,
    document_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    date_field: str = "published",
    limit: int | None = None
):
    rows = query_matched_sentences(
        keyword=keyword,
        category=category,
        document_type=document_type,
        document_id=document_id,
        start_date=start_date,
        end_date=end_date,
        date_field=date_field,
        limit=limit,
    )
    
    filename = build_report_filename(
        keyword=keyword,
        category=category,
        report_type="matches"
    )

    return make_csv_response(rows, filename)

@router.get("/summary/export")
def export_summary(
    keyword: str | None = None,
    category: str | None = None,
    document_type: str | None = None,
    document_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    date_field: str = "published",
    summary_by: str = "document",
    limit: int | None = None
):
    rows = query_summary(
        keyword=keyword,
        category=category,
        document_type=document_type,
        document_id=document_id,
        start_date=start_date,
        end_date=end_date,
        date_field=date_field,
        summary_by=summary_by,
        limit=limit,
    )

    filename = build_report_filename(
        keyword=keyword,
        category=category,
        report_type="summary"
    )

    return make_csv_response(rows, filename)
