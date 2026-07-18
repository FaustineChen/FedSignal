from sqlalchemy import text
from app.db import engine

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

def get_report_date_expr(date_field):
    if date_field == "published":
        return "d.published_date"

    if date_field == "event":
        return "COALESCE(d.event_end_date, d.event_start_date)"

    raise ValueError(f"Unsupported date_field: {date_field}")

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
