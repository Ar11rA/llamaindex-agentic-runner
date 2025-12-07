import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import router as api_router
from config.database import db_manager
from config.observability import setup_observability

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# Initialize observability FIRST (before any LlamaIndex imports/operations)
# This ensures all LlamaIndex operations are traced
setup_observability()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    # Startup
    logger.info("Starting application...")
    await db_manager.connect()
    logger.info("Application started")

    yield  # App runs here

    # Shutdown
    logger.info("Shutting down application...")
    await db_manager.disconnect()
    logger.info("Application stopped")


app = FastAPI(
    title="LlamaIndex Agent API",
    description="API for interacting with LlamaIndex agents",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=6001, reload=True)
