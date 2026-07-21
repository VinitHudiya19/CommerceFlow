from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.users.models import User, Address
from app.users.schemas import ProfileResponse, AddressRequest, AddressResponse
from app.common.exceptions import ResourceNotFoundException, BadRequestException

async def get_user_profile(user_id: int, db: AsyncSession) -> ProfileResponse:
    # Retrieve user model or throw HTTP 404
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        raise ResourceNotFoundException("User", "id", user_id)
    
    return ProfileResponse(
        id=user.id,
        fullName=user.fullName,
        email=user.email,
        phone=user.phone,
        role=user.role.name,
        verified=user.verified,
        createdAt=user.createdAt
    )

async def get_user_addresses(user_id: int, db: AsyncSession) -> list[AddressResponse]:
    # Query all addresses for a given user
    stmt = select(Address).where(Address.userId == user_id)
    res = await db.execute(stmt)
    addresses = res.scalars().all()
    return [AddressResponse.model_validate(addr) for addr in addresses]

async def add_user_address(user_id: int, request: AddressRequest, db: AsyncSession) -> AddressResponse:
    address = Address(
        userId=user_id,
        label=request.label,
        addressLine1=request.addressLine1,
        addressLine2=request.addressLine2,
        city=request.city,
        state=request.state,
        pincode=request.pincode
    )
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return AddressResponse.model_validate(address)

async def delete_user_address(user_id: int, address_id: int, db: AsyncSession):
    # Verify address exists and belongs to the user
    stmt = select(Address).where(Address.id == address_id)
    res = await db.execute(stmt)
    address = res.scalars().first()
    
    if not address:
        raise ResourceNotFoundException("Address", "id", address_id)
    if address.userId != user_id:
        raise BadRequestException("This address does not belong to you")

    await db.delete(address)
    await db.commit()
