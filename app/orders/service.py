from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.orders.models import Order, OrderItem, OrderStatus
from app.users.models import User, Address
from app.cart.models import Cart
from app.inventory.models import Inventory
from app.orders.schemas import OrderRequest, OrderResponse, OrderItemResponse
from app.common.exceptions import BadRequestException, ResourceNotFoundException
from app.cart.service import get_or_create_cart
from app.orders.tasks import process_order_placement_task, process_order_cancellation_task

async def place_order(user_id: int, request: OrderRequest, db: AsyncSession) -> OrderResponse:
    # 1. Fetch User details (Ensure email verification check)
    user_stmt = select(User).where(User.id == user_id)
    user_res = await db.execute(user_stmt)
    user = user_res.scalars().first()
    if not user:
        raise ResourceNotFoundException("User", "id", user_id)
    if not user.verified:
        raise BadRequestException("Please verify your email address to place orders.")

    # 2. Fetch User's Cart
    cart = await get_or_create_cart(user_id, db)
    if not cart.items:
        raise BadRequestException("Your cart is empty")

    # 3. Fetch Delivery Address
    addr_stmt = select(Address).where(Address.id == request.addressId)
    addr_res = await db.execute(addr_stmt)
    address = addr_res.scalars().first()
    if not address or address.userId != user_id:
        raise BadRequestException("This address doesn't belong to you")

    # Format delivery address snapshot string
    address_snapshot = f"{address.label}: {address.addressLine1}"
    if address.addressLine2:
        address_snapshot += f", {address.addressLine2}"
    address_snapshot += f", {address.city}, {address.state} - {address.pincode}"

    # 4. Check Stock Availability
    for item in cart.items:
        inv_stmt = select(Inventory).where(Inventory.productId == item.productId)
        inv_res = await db.execute(inv_stmt)
        inv = inv_res.scalars().first()
        if not inv or inv.quantity < item.quantity:
            product_name = item.product.name if item.product else "Product"
            raise BadRequestException(f"Not enough stock for: {product_name}")

    # 5. Create Order
    total_amount = sum(item.quantity * item.unitPrice for item in cart.items)
    order = Order(
        userId=user_id,
        totalAmount=total_amount,
        status=OrderStatus.PENDING,
        deliveryAddress=address_snapshot
    )
    db.add(order)
    await db.flush() # Populate order.id

    # 6. Create Order Items
    order_items = []
    for item in cart.items:
        product_name = item.product.name if item.product else "Unknown Product"
        subtotal = item.quantity * item.unitPrice
        
        order_item = OrderItem(
            orderId=order.id,
            productId=item.productId,
            productName=product_name,
            quantity=item.quantity,
            unitPrice=item.unitPrice,
            subtotal=subtotal
        )
        db.add(order_item)
        order_items.append(order_item)

    # 7. Clear Shopping Cart
    for item in cart.items:
        await db.delete(item)

    order.items = order_items

    await db.commit()
    await db.refresh(order)

    # 8. Dispatch Background Celery Task for stock allocation & payment initiation
    process_order_placement_task.delay(order.id)

    # Convert to Response DTO
    return map_order_response(order)

async def list_user_orders(user_id: int, db: AsyncSession) -> list[OrderResponse]:
    stmt = select(Order).where(Order.userId == user_id).order_by(Order.createdAt.desc())
    res = await db.execute(stmt)
    orders = res.scalars().all()
    return [map_order_response(o) for o in orders]

async def cancel_user_order(user_id: int, order_id: int, db: AsyncSession) -> OrderResponse:
    stmt = select(Order).where(and_(Order.id == order_id, Order.userId == user_id))
    res = await db.execute(stmt)
    order = res.scalars().first()
    
    if not order:
        raise ResourceNotFoundException("Order", "id", order_id)
    if order.status in (OrderStatus.CANCELLED, OrderStatus.DELIVERED):
        raise BadRequestException(f"Cannot cancel order in status: {order.status.name}")

    order.status = OrderStatus.CANCELLED
    await db.commit()

    # Dispatch Background Task to restore inventory stock
    process_order_cancellation_task.delay(order_id)

    return map_order_response(order)

# -- Helpers --

def map_order_response(order: Order) -> OrderResponse:
    item_responses = [
        OrderItemResponse(
            id=item.id,
            productId=item.productId,
            productName=item.productName,
            quantity=item.quantity,
            unitPrice=item.unitPrice,
            subtotal=item.subtotal
        ) for item in order.items
    ]
    return OrderResponse(
        id=order.id,
        userId=order.userId,
        totalAmount=order.totalAmount,
        status=order.status.name,
        deliveryAddress=order.deliveryAddress,
        createdAt=order.createdAt,
        items=item_responses
    )
