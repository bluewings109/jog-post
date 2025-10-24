from enum import Enum

class ErrorDetail:
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

class ErrorCode(Enum):
    STRAVA_COMMON_ERROR_1 = ErrorDetail("STRAVA_COMMON_ERROR_1", "Can not connect to Strava server")

    STRAVA_ATHLETE_ERROR_1 = ErrorDetail("STRAVA_ATHLETE_ERROR_1", "Athlete does not exist!")


    STRAVA_TOKEN_ERROR_1 = ErrorDetail("STRAVA_TOKEN_ERROR_1", "Can not refresh access_token!")

    STRAVA_ACTIVITY_ERROR_1 = ErrorDetail("STRAVA_ACTIVITY_ERROR_1", "Can not get an activity")
    STRAVA_ACTIVITY_ERROR_2 = ErrorDetail("STRAVA_ACTIVITY_ERROR_2", "The activity does not contain polyline!")
    STRAVA_ACTIVITY_ERROR_3 = ErrorDetail("STRAVA_ACTIVITY_ERROR_3", "Activity does not exist!")
    STRAVA_ACTIVITY_ERROR_4 = ErrorDetail("STRAVA_ACTIVITY_ERROR_4", "Can not get activities")

    GOOGLE_COMMON_ERROR_1 = ErrorDetail("GOOGLE_COMMON_ERROR_1", "Can not connect to Google API")

    GOOGLE_MAPS_ERROR_1 = ErrorDetail("GOOGLE_MAPS_ERROR_1", "Can not get static map image")

    INSTAGRAM_COMMON_ERROR_1 = ErrorDetail("INSTAGRAM_COMMON_ERROR_1", "Can not connect to Instagram Server")

    INSTAGRAM_TOKEN_ERROR_1 = ErrorDetail("INSTAGRAM_TOKEN_ERROR_1", "Can not get short lived access_token by code")
    INSTAGRAM_TOKEN_ERROR_2 = ErrorDetail("INSTAGRAM_TOKEN_ERROR_2", "Can not get long lived access_token by short lived access_token")
    INSTAGRAM_TOKEN_ERROR_3 = ErrorDetail("INSTAGRAM_TOKEN_ERROR_3", "Can not refresh long lived access_token")
    INSTAGRAM_TOKEN_ERROR_4 = ErrorDetail("INSTAGRAM_TOKEN_ERROR_4", "Can not create container")
    INSTAGRAM_TOKEN_ERROR_5= ErrorDetail("INSTAGRAM_TOKEN_ERROR_5", "Can not publish container")
    INSTAGRAM_TOKEN_ERROR_6= ErrorDetail("INSTAGRAM_TOKEN_ERROR_6", "Can not get container status")
    INSTAGRAM_TOKEN_ERROR_7= ErrorDetail("INSTAGRAM_TOKEN_ERROR_7", "Instagram container status error")
    INSTAGRAM_TOKEN_ERROR_8= ErrorDetail("INSTAGRAM_TOKEN_ERROR_8", "Instagram container status error. retry count exceeded")