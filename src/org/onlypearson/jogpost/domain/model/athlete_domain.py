class AthleteDomain:
    def __init__(
        self,
        athlete_id: int,
        username: str,
        access_token: str,
        refresh_token: str,
        expire_date: int,
        scopes: str,
        instagram_access_token: str,
        instagram_expire_date: int,
        instagram_user_id: int,
    ):
        self.athlete_id=athlete_id
        self.username=username
        self.access_token=access_token
        self.refresh_token=refresh_token
        self.expire_date=expire_date
        self.scopes=scopes
        self.instagram_access_token=instagram_access_token
        self.instagram_expire_date=instagram_expire_date
        self.instagram_user_id=instagram_user_id
