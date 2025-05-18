from fastapi import APIRouter
from app.api.endpoints import container, user, auth

api_router = APIRouter()
api_router.include_router(container.router, prefix="/containers", tags=["containers"])
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])