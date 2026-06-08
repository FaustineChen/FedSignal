# database connection
# other files that need to read/write db, need to import db.py。

# support all steps relate to storage
    # Store raw document
    # Store processing job
    # Store structured results
    # Search stored results


import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

db_url = os.getenv("DATABASE_URL")
if db_url is None:
    raise ValueError("DATABASE_URL is not set.")

# connect to database
engine = create_engine(db_url)

# ORM
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

# parent class of ORM table model
Base = declarative_base()


def test_connection():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        return result.scalar()          #  returns the very first column of the very first row from a database query, or None if no rows are found. 

if __name__ == "__main__":
    print(test_connection()) 