from org.onlypearson.jogpost.exception.error_code import ErrorDetail


class StravaException(Exception):
    def __init__(self, error_detail: ErrorDetail, message: str | None = None):
        super().__init__(message or error_detail.message)
        self.code = error_detail.code

class InstagramException(Exception):
    def __init__(self, error_detail: ErrorDetail, message: str | None = None):
        super().__init__(message or error_detail.message)
        self.code = error_detail.code
