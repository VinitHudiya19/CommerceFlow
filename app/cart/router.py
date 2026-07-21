from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.schemas import ApiResponse
from app.cart.schemas import CartResponse, CartItemRequest
from app.security.dependencies import get_current_user
from app.cart.service import (
    get_user_cart_response, add_item_to_cart, update_cart_item_qty, remove_item_from_cart
)

router = APIRouter(prefix="/api/cart", tags=["Shopping Cart"])

@router.get("", response_model=ApiResponse[CartResponse])
async def get_cart(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Retrieve active cart for authenticated user
    data = await get_user_cart_response(current_user["id"], db)
    return ApiResponse(success=True, message="Cart retrieved", data=data)

@router.post("/items", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[CartResponse])
async def add_item(
    request: CartItemRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Add product item to user's cart (Snapshots current product price)
    data = await add_item_to_cart(current_user["id"], request, db)
    return ApiResponse(success=True, message="Item added to cart", data=data)

@router.put("/items/{item_id}", response_model=ApiResponse[CartResponse])
async def update_item_qty(
    item_id: int,
    quantity: int = Query(..., gt=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Update item quantity in shopping bag
    data = await update_cart_item_qty(current_user["id"], item_id, quantity, db)
    return ApiResponse(success=True, message="Item quantity updated", data=data)

@router.delete("/items/{item_id}", response_model=ApiResponse[CartResponse])
async def remove_item(
    item_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Remove item from cart
    data = await remove_item_from_cart(current_user["id"], item_id, db)
    return ApiResponse(success=True, message="Item removed from cart", data=data)
