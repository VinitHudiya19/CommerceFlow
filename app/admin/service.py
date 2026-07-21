from decimal import Decimal
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.users.models import User
from app.orders.models import Order, OrderStatus
from app.inventory.models import Inventory
from app.payments.models import Payment, PaymentStatus
from app.admin.schemas import DashboardStatsResponse

async def get_dashboard_stats(db: AsyncSession) -> DashboardStatsResponse:
    # 1. Total Revenue: sum of all completed payments
    rev_stmt = select(func.sum(Payment.amount)).where(Payment.status == PaymentStatus.COMPLETED)
    rev_res = await db.execute(rev_stmt)
    total_rev = rev_res.scalar() or Decimal("0.00")

    # 2. Total Users count
    user_stmt = select(func.count(User.id))
    user_res = await db.execute(user_stmt)
    total_users = user_res.scalar() or 0

    # 3. Total Orders count
    order_stmt = select(func.count(Order.id))
    order_res = await db.execute(order_stmt)
    total_orders = order_res.scalar() or 0

    # 4. Pending Orders count (Status PENDING or PLACED)
    pending_stmt = select(func.count(Order.id)).where(
        Order.status.in_([OrderStatus.PENDING, OrderStatus.PLACED])
    )
    pending_res = await db.execute(pending_stmt)
    pending_orders = pending_res.scalar() or 0

    # 5. Low Stock Products count (Inventory quantity <= threshold)
    low_stock_stmt = select(func.count(Inventory.id)).where(
        Inventory.quantity <= Inventory.lowStockThreshold
    )
    low_stock_res = await db.execute(low_stock_stmt)
    low_stock_products = low_stock_res.scalar() or 0

    return DashboardStatsResponse(
        totalRevenue=total_rev,
        totalUsers=total_users,
        totalOrders=total_orders,
        pendingOrders=pending_orders,
        lowStockProducts=low_stock_products
    )
