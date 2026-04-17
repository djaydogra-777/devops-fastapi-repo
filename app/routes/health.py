import logging

from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check() -> dict:
    logger.info("Health check called")
    return {"status": "ok"}
