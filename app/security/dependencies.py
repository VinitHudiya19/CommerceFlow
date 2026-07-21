from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.security.jwt import verify_access_token
from app.common.exceptions import ForbiddenException

# Standard HTTP Bearer scheme
security = HTTPBearer(auto_error=True)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    # Extracts bearer token, verifies it, and returns user dict details
    token = credentials.credentials
    return verify_access_token(token)

def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    # Restricts endpoint access to Admin users only
    if current_user["role"] != "ADMIN":
        raise ForbiddenException("Admin privileges required")
    return current_user
