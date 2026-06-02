from sqlalchemy import text
from db import engine


def check_tables():
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
        )

        tables = result.fetchall()

        print("Tables in database:")
        for table in tables:
            print("-", table[0])


if __name__ == "__main__":
    check_tables()