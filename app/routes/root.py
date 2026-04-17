from fastapi import APIRouter

from app.logger import logger

router = APIRouter()


@router.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "Hello World"}