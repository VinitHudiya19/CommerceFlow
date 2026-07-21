from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.schemas import ApiResponse
from app.users.schemas import ProfileResponse, AddressRequest, AddressResponse
from app.security.dependencies import get_current_user
from app.users.service import get_user_profile, get_user_addresses, add_user_address, delete_user_address

router = APIRouter(prefix="/api/profile", tags=["User Profile"])

@router.get("", response_model=ApiResponse[ProfileResponse])
async def get_profile(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Retrieve authenticated user profile
    data = await get_user_profile(current_user["id"], db)
    return ApiResponse(success=True, message="Profile retrieved", data=data)

@router.get("/addresses", response_model=ApiResponse[list[AddressResponse]])
async def get_addresses(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # List addresses registered to authenticated user
    data = await get_user_addresses(current_user["id"], db)
    return ApiResponse(success=True, message="Addresses retrieved", data=data)

@router.post("/addresses", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[AddressResponse])
async def create_address(
    request: AddressRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Add a new address to authenticated user profile
    data = await add_user_address(current_user["id"], request, db)
    return ApiResponse(success=True, message="Address created successfully", data=data)

@router.delete("/addresses/{address_id}", response_model=ApiResponse[None])
async def remove_address(
    address_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Delete address by ID
    await delete_user_address(current_user["id"], address_id, db)
    return ApiResponse(success=True, message="Address deleted successfully", data=None)
