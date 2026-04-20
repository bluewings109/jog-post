from fastapi import APIRouter

from app.api.v1 import activities, advice, auth, public, statistics, webhook

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(webhook.router)
api_router.include_router(activities.router)
api_router.include_router(advice.router)
api_router.include_router(statistics.router)
api_router.include_router(public.router)
