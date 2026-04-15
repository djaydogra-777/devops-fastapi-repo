from fastapi import FastAPI

from app.logger import get_logger, setup_logging
from app.routes import health, root, simulate_error

setup_logging()
logger = get_logger(__name__)

app = FastAPI(title="DevOps FastAPI", version="1.0.0")

app.include_router(root.router)
app.include_router(health.router)
app.include_router(simulate_error.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
