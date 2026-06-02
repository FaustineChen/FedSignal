# test data

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

db_url = os.getenv("DATABASE_URL")

if db_url is None:
    raise ValueError("DATABASE_URL is not set.")

engine = create_engine(db_url)

# begin() starts a transaction,
# commits changes if the block completes successfully,
# or rolls them back if an error occurs
with engine.begin() as conn:
    # delete table (create a new one every time)
    conn.execute(text("DROP TABLE IF EXISTS test_doc;"))
    # create table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS test_doc (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            source TEXT,
            doc_type TEXT,
            published_date DATE,
            event_date DATE,
            content TEXT,
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))

    conn.execute(text("DELETE FROM test_doc;"))

    # add data
    conn.execute(text("""
        INSERT INTO test_doc (title, source, doc_type, published_date, event_date, content, url)
        VALUES
        ('FOMC Statement', 'Federal Reserve', 'statement', '2026-04-29', '2026-04-29', 'Recent indicators suggest that economic activity has been expanding at a solid pace.', 'url1'),
        ('FOMC Minutes', 'Federal Reserve', 'minutes', '2026-05-20', '2026-04-29', 'Most participants remarked that the developments in the Middle East had contributed to the uncertainty surrounding the outlook for economic activity, and several of these participants also noted that business contacts had emphasized heightened uncertainty about the economic outlook.', 'url2');
    """))

print("Test data inserted.")

# connect and search
with engine.connect() as conn:
    # print data
    result = conn.execute(text("SELECT * FROM test_doc;"))

    for row in result:
        print(row)

