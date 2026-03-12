"""API v1 router configuration."""
from fastapi import APIRouter

from app.api.v1 import auth

# Create main API router
api_router = APIRouter()

# Include auth routes
api_router.include_router(auth.router)
