import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database.session import init_db
from backend.scheduler.jobs import start_scheduler
from backend.routes.chat_routes import router as chat_router
from backend.routes.watchlist_routes import router as watchlist_router
from backend.routes.integration_routes import router as integration_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for DB setup and background scheduler."""
    logger.info("Initializing Atlas Financial Assistant DB...")
    await init_db()
    logger.info("Starting background scheduler...")
    start_scheduler()
    yield
    logger.info("Shutting down Atlas Financial Assistant...")

app = FastAPI(
    title="Atlas AI Financial Assistant API",
    description="Production-grade Financial Intelligence Engine & Telegram Assistant API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(chat_router)
app.include_router(watchlist_router)
app.include_router(integration_router)

# Mount web simulator static files
web_sim_path = os.path.join(os.path.dirname(__file__), "..", "web_simulator")
if os.path.exists(web_sim_path):
    @app.get("/")
    async def serve_simulator():
        return FileResponse(os.path.join(web_sim_path, "index.html"))

@app.get("/health")
async def health_check():
    return {"status": "online", "system": "Atlas AI Financial Assistant", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
