import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/simulate-error")
def simulate_error() -> JSONResponse:
    try:
        raise RuntimeError("Simulated internal failure")
    except RuntimeError:
        logger.exception("Simulated internal failure")
        return JSONResponse(status_code=500, content={"error": "Internal error"})