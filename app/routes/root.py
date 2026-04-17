import logging

from fastapi import APIRouter

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "Hello World"}