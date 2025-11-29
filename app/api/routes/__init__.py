"""
API Routes
"""

from app.api.routes.grid import router as grid_router
from app.api.routes.data_centers import router as data_centers_router
from app.api.routes.ai_impact import router as ai_impact_router
from app.api.routes.health import router as health_router

__all__ = [
    "grid_router",
    "data_centers_router",
    "ai_impact_router",
    "health_router",
]
