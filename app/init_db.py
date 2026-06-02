# execute schema.sql

from pathlib import Path
from sqlalchemy import text
from db import engine

def init_db():
    # reaf file
    curr_dir = Path(__file__).parent
    schema_path = curr_dir / "schema.sql"
    with open(schema_path, "r", encoding = "utf-8") as file:
        schema_sql = file.read()

    # split & store SQL statements
    statements = []
    for stmt in schema_sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            statements.append(stmt)
    
    with engine.begin() as conn:
        for stmt in statements:
            print("Executing SQL:")
            print(stmt)
            print("-----")
            conn.execute(text(stmt))

if __name__ == "__main__":
    init_db()
    print("Database Initialized.")