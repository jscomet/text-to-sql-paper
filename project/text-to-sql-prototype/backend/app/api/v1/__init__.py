"""API v1 router configuration."""
from fastapi import APIRouter

from app.api.v1 import api_keys, auth, connections, evaluations, queries

# Create main API router
api_router = APIRouter()

# Include auth routes
api_router.include_router(auth.router)

# Include API key routes
api_router.include_router(api_keys.router)

# Include connections routes
api_router.include_router(connections.router)

# Include queries routes
api_router.include_router(queries.router)

# Include evaluations routes
api_router.include_router(evaluations.router)
