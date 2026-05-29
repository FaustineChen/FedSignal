import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if database_url is None:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(database_url)

with engine.connect() as conn:
    result = conn.execute(text("SELECT NOW();"))
    print("Connected with SQLAlchemy.")
    print(result.fetchone())