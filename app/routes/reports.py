# report API routes
from fastapi import APIRouter
from queries.report_queries import query_summary, query_matched_sentences

router = APIRouter()

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