from fastapi import APIRouter

from app.api.v1 import activities, advice, auth, webhook

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(webhook.router)
api_router.include_router(activities.router)
api_router.include_router(advice.router)
