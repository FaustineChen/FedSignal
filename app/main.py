# FastAPI backend
    # POST /documents
    # GET /documents/{id}
    # GET /search?q=inflation
    # GET /jobs/{id}
# User / ingestion script -> Backend API
# user upload Fed speech，main.py accept request and call ingest.py

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes.reports import router as reports_router
from app.routes.jobs import router as jobs_router
from app.routes.documents import router as documents_router

app = FastAPI()

# frontend static files
app.mount(
    "/static",
    StaticFiles(directory="frontend"),
    name="static"
)

@app.get("/")
def home():
    return FileResponse("frontend/index.html")

app.include_router(
    reports_router,
    prefix="/api/reports"
)

app.include_router(
    jobs_router,
    prefix="/api/jobs"
)

app.include_router(
    documents_router,
    prefix="/api/documents"
)