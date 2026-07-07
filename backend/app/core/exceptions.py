"""
应用级自定义异常。
在 main.py 的 exception_handler 中统一捕获，返回标准 ApiResponse 格式。
"""

class AppException(Exception):
    """应用异常基类，code 为 HTTP 状态码，message 为前端显示的错误信息。"""
    def __init__(self, code: int = 500, message: str = "Internal error"):
        self.code = code
        self.message = message
        super().__init__(message)


class NotFoundError(AppException):
    """资源不存在（404）。"""
    def __init__(self, resource: str = "Resource"):
        super().__init__(code=404, message=f"{resource} not found")


class AuthError(AppException):
    """认证失败（401）。"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(code=401, message=message)


class ForbiddenError(AppException):
    """权限不足（403）。"""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(code=403, message=message)
