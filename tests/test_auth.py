import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from app.auth.service import register_user, login_user, rotate_refresh_token
from app.auth.schemas import RegisterRequest, LoginRequest
from app.users.models import User, Role, RefreshToken
from app.common.exceptions import BadRequestException, UnauthorizedException

@pytest.mark.asyncio
async def test_register_user_already_exists():
    # Arrange
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = User(id=1, email="test@example.com")
    db.execute.return_value = mock_result

    request = RegisterRequest(fullName="Test User", email="test@example.com", password="password123")

    # Act & Assert
    with pytest.raises(BadRequestException) as exc:
        await register_user(request, db)
    assert "already registered" in str(exc.value.message)

@pytest.mark.asyncio
async def test_login_user_locked():
    # Arrange
    db = AsyncMock()
    user = User(
        id=1,
        email="test@example.com",
        passwordHash="hashed",
        failedAttempts=5,
        lockTime=datetime.utcnow() + timedelta(minutes=10) # Locked
    )
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = user
    db.execute.return_value = mock_result

    request = LoginRequest(email="test@example.com", password="password123")

    # Act & Assert
    with pytest.raises(BadRequestException) as exc:
        await login_user(request, db)
    assert "temporarily locked" in str(exc.value.message)

@pytest.mark.asyncio
async def test_login_user_failed_attempts_trigger_lock():
    # Arrange
    db = AsyncMock()
    user = User(
        id=1,
        email="test@example.com",
        passwordHash="hashed",
        failedAttempts=4, # Next failure locks
        lockTime=None
    )
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = user
    db.execute.return_value = mock_result

    request = LoginRequest(email="test@example.com", password="wrongpassword")

    with patch("app.auth.service.verify_password", return_value=False):
        # Act & Assert
        with pytest.raises(BadRequestException) as exc:
            await login_user(request, db)
        assert "locked" in str(exc.value.message)
        assert user.failedAttempts == 5
        assert user.lockTime is not None
