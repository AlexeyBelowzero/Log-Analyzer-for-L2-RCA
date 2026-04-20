from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.analyzer.engine import LogAnalyzer
from backend.app.models import AnalyzeRequest, AnalyzeResponse


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = PROJECT_ROOT / "web"

app = FastAPI(title="Log Analyzer for L2 RCA", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if (WEB_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")

analyzer = LogAnalyzer()


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_logs(request: AnalyzeRequest) -> AnalyzeResponse:
    return analyzer.analyze(
        text=request.text,
        source_type=request.source_type,
        max_groups=request.max_groups,
    )
