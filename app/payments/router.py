from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.schemas import ApiResponse
from app.payments.schemas import PaymentResponse
from app.security.dependencies import get_current_user
from app.payments.service import get_payment_by_order_id, verify_mock_payment

router = APIRouter(prefix="/api/payments", tags=["Payment Transactions"])

@router.get("/order/{order_id}", response_model=ApiResponse[PaymentResponse])
async def get_payment(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch pending payment details for an order
    data = await get_payment_by_order_id(order_id, current_user["id"], db)
    return ApiResponse(success=True, message="Payment details retrieved", data=data)

@router.post("/{payment_id}/verify", response_model=ApiResponse[PaymentResponse])
async def verify_payment(
    payment_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify mock payment (Triggers order Confirmation state change)
    data = await verify_mock_payment(payment_id, current_user["id"], db)
    return ApiResponse(success=True, message="Payment verified successfully", data=data)
