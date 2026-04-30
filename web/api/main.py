"""FastAPI app for the WTF Zoom Pipeline web demo."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .jobs import create_job, get_job, start_job
from .schemas import CreateJobRequest, CreateJobResponse, JobDTO

load_dotenv()

app = FastAPI(title="WTF Zoom Pipeline", version="0.1.0")

# Local development: Vite dev server runs on :5173, FastAPI on :8000.
# In production both are served from the same origin so CORS isn't needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/jobs", response_model=CreateJobResponse)
def create_job_endpoint(req: CreateJobRequest) -> CreateJobResponse:
    job = create_job(audio_filename=req.filename)
    start_job(job.id, req.audio_url)
    return CreateJobResponse(id=job.id)


@app.get("/api/jobs/{job_id}", response_model=JobDTO)
def get_job_endpoint(job_id: str) -> JobDTO:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dto()


# --- Static frontend serving (production) ---------------------------------
# When the React build exists at web/app/dist, serve it. Vite outputs index.html
# + an /assets/* directory; we mount /assets and fall through everything else
# to index.html so the SPA router can handle deep links.

_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "app" / "dist"
if _FRONTEND_DIST.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=_FRONTEND_DIST / "assets"),
        name="assets",
    )

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        target = _FRONTEND_DIST / full_path
        if target.is_file():
            return FileResponse(target)
        return FileResponse(_FRONTEND_DIST / "index.html")
