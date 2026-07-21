from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.schemas import ApiResponse
from app.orders.schemas import OrderRequest, OrderResponse
from app.security.dependencies import get_current_user
from app.orders.service import place_order, list_user_orders, cancel_user_order

router = APIRouter(prefix="/api/orders", tags=["Order Placement"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[OrderResponse])
async def create_order(
    request: OrderRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Place a new order from current cart items (Triggers stock deduction Celery background task)
    data = await place_order(current_user["id"], request, db)
    return ApiResponse(success=True, message="Order placed successfully", data=data)

@router.get("", response_model=ApiResponse[list[OrderResponse]])
async def get_orders(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Retrieve purchase history for authenticated customer
    data = await list_user_orders(current_user["id"], db)
    return ApiResponse(success=True, message="Orders retrieved", data=data)

@router.patch("/{order_id}/cancel", response_model=ApiResponse[OrderResponse])
async def cancel_order(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Cancel order (Triggers stock restoration Celery background task)
    data = await cancel_user_order(current_user["id"], order_id, db)
    return ApiResponse(success=True, message="Order cancelled successfully", data=data)
