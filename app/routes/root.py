from fastapi import APIRouter
from app.logger import get_logger

router = APIRouter()

logger = get_logger(__name__)

@router.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "Hello World"}


@router.get("/error")
def simulate_error():
    try:
        1 / 0
    except Exception:
        logger.exception("Simulated error occurred")
    return {"status": "error logged"}