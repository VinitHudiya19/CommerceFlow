from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.schemas import RegisterRequest, LoginRequest, RefreshTokenRequest, AuthResponse
from app.common.schemas import ApiResponse
from app.auth.service import register_user, login_user, rotate_refresh_token, verify_email_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[AuthResponse])
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Register customer account and output JWTs
    data = await register_user(request, db)
    return ApiResponse(success=True, message="Registration successful", data=data)

@router.post("/login", response_model=ApiResponse[AuthResponse])
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Authenticate credentials and return JWTs
    data = await login_user(request, db)
    return ApiResponse(success=True, message="Login successful", data=data)

@router.post("/refresh", response_model=ApiResponse[AuthResponse])
async def refresh(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    # Rotate refresh token (RTR) and return new access token
    data = await rotate_refresh_token(request.refreshToken, db)
    return ApiResponse(success=True, message="Token refreshed", data=data)

@router.get("/verify", response_model=ApiResponse[None])
async def verify(token: str = Query(...), db: AsyncSession = Depends(get_db)):
    # Verify new user's email using token
    await verify_email_token(token, db)
    return ApiResponse(success=True, message="Email verified successfully", data=None)
