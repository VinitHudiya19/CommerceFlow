from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.cart.models import Cart, CartItem
from app.products.models import Product
from app.cart.schemas import CartResponse, CartItemResponse, CartItemRequest
from app.common.exceptions import ResourceNotFoundException, BadRequestException

async def get_or_create_cart(user_id: int, db: AsyncSession) -> Cart:
    # Query cart or create it lazily if not found with selectinload options
    stmt = select(Cart).options(
        selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.images)
    ).where(Cart.userId == user_id)
    res = await db.execute(stmt)
    cart = res.scalars().first()
    
    if not cart:
        cart = Cart(userId=user_id)
        db.add(cart)
        await db.commit()
        # Re-query with selectinload to ensure items relationship is loaded
        res = await db.execute(stmt)
        cart = res.scalars().first()
        
    return cart

async def get_user_cart_response(user_id: int, db: AsyncSession) -> CartResponse:
    cart = await get_or_create_cart(user_id, db)
    
    item_responses = []
    total_amount = Decimal("0.00")
    
    for item in cart.items:
        product = item.product
        product_name = product.name if product else "Unknown Product"
        image_url = product.images[0].imageUrl if product and product.images else None
        
        subtotal = item.quantity * item.unitPrice
        total_amount += subtotal
        
        item_responses.append(CartItemResponse(
            id=item.id,
            productId=item.productId,
            productName=product_name,
            unitPrice=item.unitPrice,
            quantity=item.quantity,
            subtotal=subtotal,
            productImageUrl=image_url
        ))
        
    return CartResponse(
        id=cart.id,
        userId=cart.userId,
        items=item_responses,
        totalAmount=total_amount
    )

async def add_item_to_cart(user_id: int, request: CartItemRequest, db: AsyncSession) -> CartResponse:
    cart = await get_or_create_cart(user_id, db)
    
    # Verify product exists
    prod_stmt = select(Product).where(Product.id == request.productId)
    prod_res = await db.execute(prod_stmt)
    product = prod_res.scalars().first()
    if not product:
        raise ResourceNotFoundException("Product", "id", request.productId)

    # Check if item already in cart
    existing_item = next((item for item in cart.items if item.productId == request.productId), None)
    
    if existing_item:
        existing_item.quantity += request.quantity
        existing_item.unitPrice = product.price # update snapshot
    else:
        new_item = CartItem(
            cartId=cart.id,
            productId=request.productId,
            quantity=request.quantity,
            unitPrice=product.price # Snapshot pricing
        )
        db.add(new_item)

    await db.commit()
    return await get_user_cart_response(user_id, db)

async def update_cart_item_qty(user_id: int, item_id: int, quantity: int, db: AsyncSession) -> CartResponse:
    cart = await get_or_create_cart(user_id, db)
    
    item = next((item for item in cart.items if item.id == item_id), None)
    if not item:
        raise ResourceNotFoundException("CartItem", "id", item_id)
        
    item.quantity = quantity
    await db.commit()
    return await get_user_cart_response(user_id, db)

async def remove_item_from_cart(user_id: int, item_id: int, db: AsyncSession) -> CartResponse:
    cart = await get_or_create_cart(user_id, db)
    
    item = next((item for item in cart.items if item.id == item_id), None)
    if not item:
        raise ResourceNotFoundException("CartItem", "id", item_id)
        
    await db.delete(item)
    await db.commit()
    
    # Reload and return
    db.expire(cart)
    return await get_user_cart_response(user_id, db)

async def clear_user_cart(user_id: int, db: AsyncSession):
    cart = await get_or_create_cart(user_id, db)
    for item in cart.items:
        await db.delete(item)
    await db.commit()
