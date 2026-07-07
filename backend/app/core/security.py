"""
密码哈希工具。
使用 bcrypt 算法（通过 passlib 封装），单向哈希，不可逆。
"""

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """将明文密码哈希为 bcrypt 字符串，用于注册时存储。"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否匹配哈希值，用于登录时校验。"""
    return pwd_context.verify(plain_password, hashed_password)
