# test Python connect to PostgreSQL
    # read .env
    # connect to PostgreSQL
    # exec SELECT NOW()
    # print

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host = os.getenv("POSTGRES_HOST"),
    port = os.getenv("POSTGRES_PORT"),
    dbname = os.getenv("POSTGRES_DB"),
    user = os.getenv("POSTGRES_USER"),
    password = os.getenv("POSTGRES_PASSWORD"),
)

cur = conn.cursor()
cur.execute("SELECT version();")
version = cur.fetchone()

print("Connected.")
print(version)

cur.close()
conn.close()