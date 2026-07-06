class AppException(Exception):
    def __init__(self, code: int = 500, message: str = "Internal error"):
        self.code = code
        self.message = message
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(code=404, message=f"{resource} not found")


class AuthError(AppException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(code=401, message=message)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(code=403, message=message)
