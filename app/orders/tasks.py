import asyncio
import uuid
from decimal import Decimal
from sqlalchemy import select
from app.celery_app import celery_app
from app.database import async_session
from app.orders.models import Order, OrderItem, OrderStatus
from app.inventory.models import Inventory
from app.payments.models import Payment, PaymentStatus
from app.users.models import User

# Helper to run async code synchronously in Celery worker thread
def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

@celery_app.task
def process_order_placement_task(order_id: int):
    async def run():
        async with async_session() as db:
            # 1. Fetch Order and items
            stmt = select(Order).where(Order.id == order_id)
            res = await db.execute(stmt)
            order = res.scalars().first()
            if not order:
                print(f"[CELERY ERROR] Order {order_id} not found.")
                return

            # Fetch User for notification email
            user_stmt = select(User).where(User.id == order.userId)
            user_res = await db.execute(user_stmt)
            user = user_res.scalars().first()
            user_email = user.email if user else "customer@commerceflow.com"

            # 2. Deduct Inventory Stock
            for item in order.items:
                inv_stmt = select(Inventory).where(Inventory.productId == item.productId)
                inv_res = await db.execute(inv_stmt)
                inv = inv_res.scalars().first()
                if inv:
                    inv.quantity = max(0, inv.quantity - item.quantity)
                    print(f"[CELERY] Deducted stock for product {item.productId}. New quantity: {inv.quantity}")
                    # Check low stock limit
                    if inv.quantity <= inv.lowStockThreshold:
                        print(f"[ADMIN ALERT - LOW STOCK] Product ID {item.productId} has low stock: {inv.quantity} left.")

            # 3. Create Pending Payment Record
            payment = Payment(
                orderId=order_id,
                amount=order.totalAmount,
                status=PaymentStatus.PENDING
            )
            db.add(payment)
            
            # Save all changes
            await db.commit()
            print(f"[CELERY] Stock allocated and pending payment record created for Order ID: {order_id}")

            # 4. Log confirmation email mockup
            print(f"[EMAIL MOCK] Sending Order Confirmation to {user_email}")
            print(f"Subject: Order Placed Successfully - #{order_id}")
            print(f"Body: Hello, your order of ${order.totalAmount:.2f} is placed. Payment is pending.")
    
    # Run the async logic in loop
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Celery running inside async loop context (if any)
        asyncio.ensure_future(run())
    else:
        loop.run_until_complete(run())

@celery_app.task
def process_order_cancellation_task(order_id: int):
    async def run():
        async with async_session() as db:
            stmt = select(Order).where(Order.id == order_id)
            res = await db.execute(stmt)
            order = res.scalars().first()
            if not order:
                return

            # Fetch User
            user_stmt = select(User).where(User.id == order.userId)
            user_res = await db.execute(user_stmt)
            user = user_res.scalars().first()
            user_email = user.email if user else "customer@commerceflow.com"

            # 1. Restore Inventory Stock
            for item in order.items:
                inv_stmt = select(Inventory).where(Inventory.productId == item.productId)
                inv_res = await db.execute(inv_stmt)
                inv = inv_res.scalars().first()
                if inv:
                    inv.quantity += item.quantity
                    print(f"[CELERY] Restored stock for product {item.productId}. New quantity: {inv.quantity}")

            # 2. Update Payment status to FAILED/CANCELLED if exists
            pay_stmt = select(Payment).where(Payment.orderId == order_id)
            pay_res = await db.execute(pay_stmt)
            payment = pay_res.scalars().first()
            if payment:
                payment.status = PaymentStatus.FAILED
            
            await db.commit()
            print(f"[CELERY] Stock restored and payment cancelled for Order ID: {order_id}")

            # 3. Log cancellation email mock
            print(f"[EMAIL MOCK] Sending Order Cancellation to {user_email}")
            print(f"Subject: Order Cancelled - #{order_id}")
            print(f"Body: Hello, your order #{order_id} has been cancelled successfully.")
            
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.ensure_future(run())
    else:
        loop.run_until_complete(run())

@celery_app.task
def send_payment_confirmation_task(order_id: int):
    async def run():
        async with async_session() as db:
            stmt = select(Order).where(Order.id == order_id)
            res = await db.execute(stmt)
            order = res.scalars().first()
            if not order:
                return

            user_stmt = select(User).where(User.id == order.userId)
            user_res = await db.execute(user_stmt)
            user = user_res.scalars().first()
            user_email = user.email if user else "customer@commerceflow.com"

            print(f"[EMAIL MOCK] Sending Payment Confirmation to {user_email}")
            print(f"Subject: Payment Received - Order #{order_id}")
            print(f"Body: Hello, we have received payment of ${order.totalAmount:.2f}. Your order has been CONFIRMED.")
            
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.ensure_future(run())
    else:
        loop.run_until_complete(run())
