import logging
import traceback

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/simulate-error", include_in_schema=True)
def simulate_error() -> JSONResponse:
    """Intentionally raises an exception to verify error logging and Loki ingestion."""
    try:
        raise RuntimeError("Simulated internal failure")
    except RuntimeError as exc:
        logger.error(
            "internal_error",
            extra={"stack": traceback.format_exc(), "error": str(exc)},
        )
        return JSONResponse(status_code=500, content={"error": "Internal error"})
