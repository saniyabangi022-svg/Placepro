"""Password hashing (bcrypt) and JWT tokens."""
import time
import bcrypt
import jwt
from ..exception.errors import AuthenticationError
from .config import settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:      # e.g. the sample file's placeholder hashes
        return False


def create_token(user: dict) -> str:
    if len(settings.JWT_SECRET) < 16:
        raise AuthenticationError("Server is missing a strong JWT_SECRET in .env")
    now = int(time.time())
    return jwt.encode({"sub": str(user["user_id"]), "name": user["full_name"], "role": user["role_code"],
                       "iat": now, "exp": now + settings.JWT_EXPIRE_MINUTES * 60}, settings.JWT_SECRET, "HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise AuthenticationError("Session expired or invalid. Please log in again.")
