"""
JWT Token 工具函数。
使用 python-jose 库签发和验证 JWT。
token payload 中 "sub" 字段存储用户 ID。
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    创建 JWT access token。
    参数:
        data:            token payload，通常为 {"sub": user_id}
        expires_delta:   自定义过期时间，默认使用 config 中的 jwt_expire_minutes
    返回:
        编码后的 JWT 字符串
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> dict | None:
    """
    验证并解码 JWT token。
    返回:
        解码后的 payload dict，验证失败返回 None（过期/签名错误等）。
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None
