from fastapi import FastAPI

from app.routes import health, root

app = FastAPI(title="DevOps FastAPI", version="1.0.0")

app.include_router(root.router)
app.include_router(health.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
