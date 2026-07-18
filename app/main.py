# FastAPI backend
    # POST /documents
    # GET /documents/{id}
    # GET /search?q=inflation
    # GET /jobs/{id}
# User / ingestion script -> Backend API
# user upload Fed speech，main.py accept request and call ingest.py

from fastapi import FastAPI
from app.routes.reports import router

app = FastAPI()

app.include_router(
    router,
    prefix="/api/reports"
)