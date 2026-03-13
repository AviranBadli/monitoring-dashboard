"""API v1 router"""

from fastapi import APIRouter

from app.api.v1 import resources, inventory, allocations, metrics, costs, analytics

api_router = APIRouter()

# Include sub-routers
api_router.include_router(resources.router, prefix="/resources", tags=["resources"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(allocations.router, prefix="/allocations", tags=["allocations"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(costs.router, prefix="/costs", tags=["costs"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
