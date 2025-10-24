from fastapi import FastAPI

from org.onlypearson.jogpost.adapter.inbound.rest.routes.webhook_router import router as strava_webhook_router
from org.onlypearson.jogpost.adapter.inbound.rest.routes.instagram_webhook_router import router as instagram_webhook_router


def create_app() -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None)
    app.include_router(strava_webhook_router)
    app.include_router(instagram_webhook_router)
    return app

