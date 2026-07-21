import jwt
from datetime import datetime, timedelta, timezone
from app.config import settings
from app.common.exceptions import UnauthorizedException

def create_access_token(user_id: int, role: str, email: str) -> str:
    # Generate JWT Access Token with claims and expiry
    expiry = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_expiration_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": expiry
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def verify_access_token(token: str) -> dict:
    # Decode and validate JWT Access Token, raising HTTP 401 if invalid or expired
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return {
            "id": int(payload["sub"]),
            "email": payload["email"],
            "role": payload["role"]
        }
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Access token has expired")
    except jwt.InvalidTokenError:
        raise UnauthorizedException("Invalid access token")
