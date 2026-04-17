from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.logger import logger

router = APIRouter()


@router.get("/simulate-error")
def simulate_error() -> JSONResponse:
    try:
        raise RuntimeError("Simulated internal failure")
    except RuntimeError:
        logger.exception("Simulated internal failure")
        return JSONResponse(status_code=500, content={"error": "Internal error"})