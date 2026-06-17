import csv
import sys
from pathlib import Path
from sqlalchemy import text

project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from app.db import engine




def upsert_keyword_catalog(conn, keyword, category, description):
    result = conn.execute(
        text(
            """
            INSERT INTO keyword_catalog (keyword, category, description)
            VALUES (:keyword, :category, :description)
            ON CONFLICT (keyword)
            DO UPDATE SET
                category = EXCLUDED.category,
                description = EXCLUDED.description
            RETURNING id
            """
        ), {
            "keyword": keyword,
            "category": category,
            "description": description
        }
    )

    return result.scalar_one()

def upsert_keyword_term(conn, keyword_id, term, match_type):
    conn.execute(
        text(
            """
            INSERT INTO keyword_terms (keyword_id, term, match_type)
            VALUES (:keyword_id, :term, :match_type)
            ON CONFLICT (keyword_id, term)
            DO UPDATE SET
                match_type = EXCLUDED.match_type
            """
        ), {
            "keyword_id": keyword_id,
            "term": term,
            "match_type": match_type
        }
    )

def seed_keywords():
    curr_dir = Path(__file__).parent
    project_root = curr_dir.parent
    csv_path = project_root / "data" / "metadata" / "fed_keyword_terms.csv"

    with engine.begin() as conn:
        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            count = 0

            for row in reader:
                keyword = row["keyword"].strip()
                category = row["category"].strip()
                description = row["description"].strip()
                term = row["term"].strip()
                match_type = row["match_type"].strip()
                
                keyword_id = upsert_keyword_catalog(
                    conn,
                    keyword=keyword,
                    category=category,
                    description=description
                )

                upsert_keyword_term(
                    conn,
                    keyword_id=keyword_id,
                    term=term,
                    match_type=match_type
                )

                count += 1
    
    print(f"Seeded {count} keyword terms.")

if __name__ == "__main__":
    seed_keywords()