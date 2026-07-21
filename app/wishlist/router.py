from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.schemas import ApiResponse
from app.wishlist.schemas import WishlistResponse
from app.security.dependencies import get_current_user
from app.wishlist.service import get_user_wishlist, add_item_to_wishlist, remove_item_from_wishlist

router = APIRouter(prefix="/api/wishlist", tags=["Wishlist"])

@router.get("", response_model=ApiResponse[list[WishlistResponse]])
async def get_wishlist(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Get all saved products in authenticated user's wishlist
    data = await get_user_wishlist(current_user["id"], db)
    return ApiResponse(success=True, message="Wishlist retrieved", data=data)

@router.post("/{product_id}", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[WishlistResponse])
async def save_item(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Bookmark product to user wishlist
    data = await add_item_to_wishlist(current_user["id"], product_id, db)
    return ApiResponse(success=True, message="Product added to wishlist", data=data)

@router.delete("/{product_id}", response_model=ApiResponse[None])
async def unsave_item(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Remove product bookmark from wishlist
    await remove_item_from_wishlist(current_user["id"], product_id, db)
    return ApiResponse(success=True, message="Product removed from wishlist", data=None)
