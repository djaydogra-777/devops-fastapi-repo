from fastapi import APIRouter

from app.logger import logger

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    logger.info("Health check called")
    return {"status": "ok"}
