from fastapi import APIRouter
from app.core.config import settings
from datetime import datetime

router = APIRouter()

@router.get("/health", tags=["System"])
def health_check():
    """
    Health check endpoint verifying backend service availability and configuration.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "ai_advisor_enabled": bool(settings.GROQ_API_KEY)
    }
