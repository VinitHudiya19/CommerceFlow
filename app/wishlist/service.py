from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.wishlist.models import WishlistItem
from app.products.models import Product
from app.wishlist.schemas import WishlistResponse
from app.common.exceptions import ResourceNotFoundException, BadRequestException

async def get_user_wishlist(user_id: int, db: AsyncSession) -> list[WishlistResponse]:
    # Query wishlist items for user
    stmt = select(WishlistItem).options(
        selectinload(WishlistItem.product).selectinload(Product.images)
    ).where(WishlistItem.userId == user_id)
    res = await db.execute(stmt)
    items = res.scalars().all()
    
    responses = []
    for item in items:
        product = item.product
        price = product.price if product else None
        image_url = product.images[0].imageUrl if product and product.images else None
        
        responses.append(WishlistResponse(
            id=item.id,
            productId=item.productId,
            productName=item.productName,
            productPrice=price,
            productImageUrl=image_url
        ))
        
    return responses

async def add_item_to_wishlist(user_id: int, product_id: int, db: AsyncSession) -> WishlistResponse:
    # Verify product exists
    prod_stmt = select(Product).where(Product.id == product_id)
    prod_res = await db.execute(prod_stmt)
    product = prod_res.scalars().first()
    if not product:
        raise ResourceNotFoundException("Product", "id", product_id)

    # Check if already in wishlist
    existing_stmt = select(WishlistItem).where(and_(WishlistItem.userId == user_id, WishlistItem.productId == product_id))
    existing_res = await db.execute(existing_stmt)
    if existing_res.scalars().first():
        raise BadRequestException("Product is already in your wishlist")

    item = WishlistItem(
        userId=user_id,
        productId=product_id,
        productName=product.name
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    image_url = product.images[0].imageUrl if product.images else None
    return WishlistResponse(
        id=item.id,
        productId=item.productId,
        productName=item.productName,
        productPrice=product.price,
        productImageUrl=image_url
    )

async def remove_item_from_wishlist(user_id: int, product_id: int, db: AsyncSession):
    # Verify item exists in user wishlist
    stmt = select(WishlistItem).where(and_(WishlistItem.userId == user_id, WishlistItem.productId == product_id))
    res = await db.execute(stmt)
    item = res.scalars().first()
    
    if not item:
        raise ResourceNotFoundException("WishlistItem", "productId", product_id)

    await db.delete(item)
    await db.commit()
