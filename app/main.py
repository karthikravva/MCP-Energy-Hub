"""
MCP Energy Hub - Main Application Entry Point
FastAPI application with Gradio UI for MCP's 1st Birthday Hackathon
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app import __version__
from app.config import get_settings
from app.db.session import init_db
from app.api.routes.health import router as health_router
from app.api.routes.grid import router as grid_router
from app.api.routes.data_centers import router as data_centers_router
from app.api.routes.ai_impact import router as ai_impact_router
from app.api.routes.ingest import router as ingest_router
from app.mcp.routes import router as mcp_router
from app.ingestion.scheduler import ingestion_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info(f"Starting MCP Energy Hub v{__version__}")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Start ingestion scheduler (optional - can be disabled)
    # ingestion_scheduler.start()

    yield

    # Shutdown
    logger.info("Shutting down MCP Energy Hub")
    ingestion_scheduler.stop()


# Create FastAPI application
app = FastAPI(
    title="MCP Energy Hub",
    description="""
    ## Monitoring • Control • Prediction for AI + Energy Real-time Intelligence
    
    This API provides real-time grid monitoring, data center energy tracking,
    and AI compute impact analytics.
    
    ### Features
    - **Grid Monitoring**: Real-time load, generation, carbon intensity by region
    - **Data Centers**: Track data center energy consumption and efficiency
    - **AI Impact**: KPIs for AI compute impact on the grid
    - **Forecasting**: Load and carbon intensity predictions
    
    ### Data Sources
    - EIA (Energy Information Administration)
    - ISO/RTO feeds (ERCOT, CAISO, PJM, etc.)
    - DOE/LBNL efficiency benchmarks
    """,
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(grid_router)
app.include_router(data_centers_router)
app.include_router(ai_impact_router)
app.include_router(ingest_router)
app.include_router(mcp_router)


@app.get("/")
async def root():
    """
    Root endpoint - Redirect to Gradio UI or show API info
    """
    # Check if Gradio is mounted
    if hasattr(app, 'gradio_app'):
        return RedirectResponse(url="/ui")

    return {
        "name": "MCP Energy Hub",
        "version": __version__,
        "description": "Monitoring • Control • Prediction for AI + Energy",
        "hackathon": "MCP's 1st Birthday - Track 1: Building MCP (Enterprise)",
        "ui": "/ui",
        "docs": "/docs",
        "mcp_tools": "/mcp/tools",
        "health": "/health",
    }


# Mount Gradio app
try:
    import gradio as gr
    logger.info(f"Gradio version: {gr.__version__}")
    from gradio_app import demo as gradio_demo
    app.gradio_app = gr.mount_gradio_app(app, gradio_demo, path="/ui")
    logger.info("Gradio UI mounted at /ui")
except ImportError as e:
    logger.warning(f"Gradio not installed, UI not available: {e}")
except Exception as e:
    logger.warning(f"Could not mount Gradio: {e}")
    import traceback
    logger.warning(traceback.format_exc())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
