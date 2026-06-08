# SQLAlchemy models
# database schema

from sqlalchemy import Column, Integer, Text, Date, DateTime, func
from app.db import Base

# documents table in Python
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)

    title = Column(Text, nullable=False)
    document_type = Column(Text, nullable=False)

    published_date = Column(Date, nullable=False)
    event_start_date = Column(Date, nullable=True)
    event_end_date = Column(Date, nullable=True)

    source = Column(Text, nullable=False)
    speaker = Column(Text, nullable=True)
    speaker_position = Column(Text, nullable=True)
    chair = Column(Text, nullable=True)

    source_url = Column(Text, nullable=False, unique=True)

    raw_file_path = Column(Text, nullable=True)
    cleaned_file_path = Column(Text, nullable=True)

    content = Column(Text, nullable=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())