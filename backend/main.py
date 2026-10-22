"""
backend/main.py
Main entrypoint for Codebase Architecture & Risk Auditor FastAPI Server.
Includes CORS middleware, health checks, and audit API routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas import HealthResponse
from backend.routers.audit import router as audit_router

app = FastAPI(
    title="Codebase Architecture & Risk Auditor API",
    description="Automated AI code review combining CodeBERT, FAISS Vector RAG, NetworkX AST Graphs, and LangGraph",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(audit_router)


@app.get("/api/health", response_model=HealthResponse, tags=["System Health"])
async def health_check():
    """Health check endpoint to verify backend server status."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        service="Codebase Architecture & Risk Auditor API"
    )


# Mount static frontend
from pathlib import Path
from fastapi.staticfiles import StaticFiles

frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
elif frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
