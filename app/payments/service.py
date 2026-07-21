import uuid
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.payments.models import Payment, PaymentStatus
from app.orders.models import Order, OrderStatus
from app.payments.schemas import PaymentResponse
from app.common.exceptions import ResourceNotFoundException, BadRequestException
from app.orders.tasks import send_payment_confirmation_task

async def get_payment_by_order_id(order_id: int, user_id: int, db: AsyncSession) -> PaymentResponse:
    # 1. Fetch Order and verify owner
    order_stmt = select(Order).where(and_(Order.id == order_id, Order.userId == user_id))
    order_res = await db.execute(order_stmt)
    order = order_res.scalars().first()
    if not order:
        raise ResourceNotFoundException("Order", "id", order_id)

    # 2. Fetch Payment for that order
    pay_stmt = select(Payment).where(Payment.orderId == order_id)
    pay_res = await db.execute(pay_stmt)
    payment = pay_res.scalars().first()
    if not payment:
        raise ResourceNotFoundException("Payment", "orderId", order_id)

    return map_payment_response(payment)

async def verify_mock_payment(payment_id: int, user_id: int, db: AsyncSession) -> PaymentResponse:
    # 1. Fetch Payment
    pay_stmt = select(Payment).where(Payment.id == payment_id)
    pay_res = await db.execute(pay_stmt)
    payment = pay_res.scalars().first()
    if not payment:
        raise ResourceNotFoundException("Payment", "id", payment_id)

    # 2. Fetch Order and verify owner
    order_stmt = select(Order).where(and_(Order.id == payment.orderId, Order.userId == user_id))
    order_res = await db.execute(order_stmt)
    order = order_res.scalars().first()
    if not order:
        raise BadRequestException("You do not own this order transaction")

    if payment.status == PaymentStatus.COMPLETED:
        raise BadRequestException("Payment is already completed")

    # 3. Simulate payment confirmation (Placed -> Confirmed status transition)
    payment.status = PaymentStatus.COMPLETED
    payment.transactionId = f"TXN-{uuid.uuid4().hex[:12].upper()}"
    
    order.status = OrderStatus.CONFIRMED
    
    await db.commit()
    await db.refresh(payment)

    # 4. Trigger background mail notification task
    send_payment_confirmation_task.delay(order.id)

    return map_payment_response(payment)

# -- Helpers --

def map_payment_response(payment: Payment) -> PaymentResponse:
    return PaymentResponse(
        id=payment.id,
        orderId=payment.orderId,
        amount=payment.amount,
        transactionId=payment.transactionId,
        status=payment.status.name
    )
