import logging
import traceback

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/simulate-error")
def simulate_error() -> JSONResponse:
    try:
        raise RuntimeError("Simulated internal failure")
    except RuntimeError:
        logger.exception(
            "internal_error",
            extra={
                "event": "simulate_error",
                "status": 500
            }
        )
        return JSONResponse(status_code=500, content={"error": "Internal error"})