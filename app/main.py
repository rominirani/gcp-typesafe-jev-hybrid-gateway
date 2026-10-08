"""FastAPI Application Entry Point for Google Cloud Hybrid AI Gateway."""

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.config import settings
from app.models import TriageRequest, GatewayResponse
from app.router import HybridAIRouter

app = FastAPI(
    title="Google Cloud Hybrid AI Gateway (TypeSafe Jev + Gemini Enterprise Agent Platform)",
    description="High-throughput System 1 / System 2 AI routing service.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = HybridAIRouter()
STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
async def root_dashboard():
    """Serve the interactive visualization web dashboard."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "GCP Hybrid AI Gateway running. Access /docs for API documentation."}


@app.get("/health")
async def health_check():
    """Liveness probe."""
    if not settings.typesafe_api_key:
        raise HTTPException(status_code=500, detail="TYPESAFE_API_KEY is not configured.")
    return {
        "status": "healthy",
        "typesafe_model": settings.typesafe_model,
        "gemini_model": settings.gemini_model,
        "gcp_project": settings.google_cloud_project,
        "confidence_threshold": settings.confidence_threshold
    }


@app.post("/api/v1/triage", response_model=GatewayResponse)
async def triage_inquiry(request: TriageRequest):
    """Primary routing endpoint: dispatches between TypeSafe Jev and Gemini on Google Cloud Agent Platform."""
    try:
        response = await router.process_request(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing failure: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
