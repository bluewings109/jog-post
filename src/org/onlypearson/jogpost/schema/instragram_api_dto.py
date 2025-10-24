from pydantic import BaseModel



class InstagramShortLivedTokenResponse(BaseModel):
    access_token: str
    user_id: int
    permissions: list[str]

class InstagramLongLivedTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class InstagramCreateContainerResponse(BaseModel):
    id: str

class InstagramPublishContainerResponse(BaseModel):
    id: str

class InstagramContainerStatusResponse(BaseModel):
    status_code: str
    id: str
