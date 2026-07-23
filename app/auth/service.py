import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.schemas import RegisterRequest, LoginRequest, AuthResponse
from app.users.models import User, Role, RefreshToken
from app.common.exceptions import BadRequestException, UnauthorizedException, ResourceNotFoundException
from app.security.passwd import hash_password, verify_password
from app.security.jwt import create_access_token
from app.config import settings

async def register_user(request: RegisterRequest, db: AsyncSession) -> AuthResponse:
    # Check if email exists
    stmt = select(User).where(User.email == request.email)
    res = await db.execute(stmt)
    if res.scalars().first():
        raise BadRequestException("Email is already registered")

    # Generate verification token
    verification_token = str(uuid.uuid4())
    expiry = datetime.utcnow() + timedelta(hours=settings.email_verification_expiry_hours)

    user = User(
        fullName=request.fullName,
        email=request.email,
        passwordHash=hash_password(request.password),
        phone=request.phone,
        role=Role.CUSTOMER,
        verified=False,
        verificationToken=verification_token,
        verificationTokenExpiry=expiry
    )
    db.add(user)
    await db.flush()

    print(f"New user registered: {user.email}. Verification token: {verification_token}")
    print(f"[EMAIL MOCK] Verification link: http://localhost:8080/api/auth/verify?token={verification_token}")

    return await generate_auth_response(user, db)

async def login_user(request: LoginRequest, db: AsyncSession) -> AuthResponse:
    stmt = select(User).where(User.email == request.email)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        raise BadRequestException("Invalid email or password")

    # Check if locked
    if user.lockTime and user.lockTime > datetime.utcnow():
        raise BadRequestException("Account is temporarily locked due to multiple failed logins. Please try again later.")

    # Verify password
    if not verify_password(request.password, user.passwordHash):
        attempts = user.failedAttempts + 1
        user.failedAttempts = attempts
        if attempts >= settings.failed_login_attempts_limit:
            user.lockTime = datetime.utcnow() + timedelta(minutes=settings.account_lock_minutes)
            await db.commit()
            raise BadRequestException("Too many failed attempts. Account has been locked for 30 minutes.")
        await db.commit()
        raise BadRequestException("Invalid email or password")

    # Reset lock state on successful login
    user.failedAttempts = 0
    user.lockTime = None
    await db.flush()

    return await generate_auth_response(user, db)

async def rotate_refresh_token(refresh_token_str: str, db: AsyncSession) -> AuthResponse:
    stmt = select(RefreshToken).where(RefreshToken.token == refresh_token_str)
    res = await db.execute(stmt)
    token_record = res.scalars().first()
    
    if not token_record:
        raise UnauthorizedException("Invalid refresh token")

    # Check if token is expired
    if token_record.expiryDate < datetime.utcnow():
        await db.delete(token_record)
        await db.commit()
        raise UnauthorizedException("Refresh token has expired. Please log in again.")

    # Fetch User
    user_stmt = select(User).where(User.id == token_record.userId)
    user_res = await db.execute(user_stmt)
    user = user_res.scalars().first()
    
    if not user:
        raise UnauthorizedException("User not found")

    # Rotate refresh token (Generate auth response deletes old and saves new)
    return await generate_auth_response(user, db)

async def verify_email_token(token: str, db: AsyncSession):
    stmt = select(User).where(User.verificationToken == token)
    res = await db.execute(stmt)
    user = res.scalars().first()
    
    if not user:
        raise BadRequestException("Invalid or expired email verification token")

    if user.verificationTokenExpiry < datetime.utcnow():
        raise BadRequestException("Verification token has expired")

    user.verified = True
    user.verificationToken = None
    user.verificationTokenExpiry = None
    await db.commit()

# -- Helpers --

async def generate_auth_response(user: User, db: AsyncSession) -> AuthResponse:
    # 1. Create new JWT access token
    access_token = create_access_token(user.id, user.role.name, user.email)

    # 2. Create new refresh token (Delete any existing token for this user first - RTR)
    tok_stmt = select(RefreshToken).where(RefreshToken.userId == user.id)
    tok_res = await db.execute(tok_stmt)
    existing_token = tok_res.scalars().first()
    if existing_token:
        await db.delete(existing_token)
        await db.flush()

    new_refresh_token_str = str(uuid.uuid4())
    expiry = datetime.utcnow() + timedelta(days=settings.jwt_refresh_expiration_days)
    
    refresh_token = RefreshToken(
        userId=user.id,
        token=new_refresh_token_str,
        expiryDate=expiry
    )
    db.add(refresh_token)
    await db.commit()

    return AuthResponse(
        accessToken=access_token,
        refreshToken=new_refresh_token_str,
        email=user.email,
        fullName=user.fullName,
        role=user.role.name
    )
