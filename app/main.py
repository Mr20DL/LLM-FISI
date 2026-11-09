from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router as assistant_router

ROOT_DIR = Path(__file__).resolve().parent
STATIC_DIR = ROOT_DIR / "static"

app = FastAPI(
    title="Asistente Académico Inteligente FISI",
    description="PoC local de asistencia académica mediante un LLM local.",
    version="0.1.0",
)

app.include_router(assistant_router, prefix="/api/v1")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "fisi-assistant-api"}
