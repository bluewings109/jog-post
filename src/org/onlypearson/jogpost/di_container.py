from dependency_injector import containers
from dependency_injector import providers

from org.onlypearson.jogpost.adapter.outbound.cloudinary.cloudinary_client import CloudinaryClient
from org.onlypearson.jogpost.adapter.outbound.repository.activity_repository import ActivityRepository
from org.onlypearson.jogpost.adapter.outbound.repository.athlete_repository import AthleteRepository
from org.onlypearson.jogpost.adapter.outbound.rest.google_client import GoogleClient
from org.onlypearson.jogpost.adapter.outbound.rest.instagram_client import InstagramClient
from org.onlypearson.jogpost.adapter.outbound.rest.strava_client import StravaClient
from org.onlypearson.jogpost.application.services.instagram_service import InstagramService
from org.onlypearson.jogpost.application.services.strava_service import StravaService
from org.onlypearson.jogpost.common.settings import settings

class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        # wiring 대상
        modules=[
            "org.onlypearson.jogpost.adapter.inbound.rest.routes.webhook_router",
            "org.onlypearson.jogpost.adapter.inbound.rest.routes.instagram_webhook_router"
        ]
    )

    athlete_repository: AthleteRepository = providers.Singleton(AthleteRepository)
    activity_repository: ActivityRepository = providers.Singleton(ActivityRepository)
    strava_client:StravaClient = providers.Singleton(StravaClient)
    google_client:GoogleClient = providers.Singleton(GoogleClient)
    instagram_client:InstagramClient = providers.Singleton(InstagramClient)
    cloudinary_client:CloudinaryClient = providers.Singleton(
        CloudinaryClient,
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
    )


    instagram_service: InstagramService = providers.Singleton(
        InstagramService,
        athlete_repository=athlete_repository,
        instagram_client=instagram_client,
    )

    strava_service: StravaService = providers.Singleton(
        StravaService,
        athlete_repository=athlete_repository,
        activity_repository=activity_repository,
        strava_client=strava_client,
        google_client=google_client,
        cloudinary_client=cloudinary_client,
        instagram_service=instagram_service,
    )

