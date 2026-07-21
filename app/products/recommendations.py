from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.products.models import Product, Category
from app.orders.models import Order, OrderItem
from app.users.models import User
from app.products.schemas import ProductResponse
from app.inventory.models import Inventory

async def get_ai_recommendations(user_id: int, db: AsyncSession) -> list[ProductResponse]:
    # 1. Fetch user's purchased product IDs
    orders_stmt = select(Order).where(and_(Order.userId == user_id, Order.status != "CANCELLED"))
    orders_res = await db.execute(orders_stmt)
    user_orders = orders_res.scalars().all()
    user_order_ids = [o.id for o in user_orders]

    purchased_product_ids = set()
    purchased_categories = set()
    if user_order_ids:
        items_stmt = select(OrderItem).where(OrderItem.orderId.in_(user_order_ids))
        items_res = await db.execute(items_stmt)
        user_items = items_res.scalars().all()
        for item in user_items:
            if item.productId:
                purchased_product_ids.add(item.productId)

    # Resolve categories of purchased products
    if purchased_product_ids:
        prod_stmt = select(Product).where(Product.id.in_(list(purchased_product_ids)))
        prod_res = await db.execute(prod_stmt)
        for p in prod_res.scalars().all():
            purchased_categories.add(p.categoryId)

    # 2. Collaborative Filtering & Purchase History (Co-occurrence)
    recommended_product_ids = []
    
    # Query other orders that contain products this user purchased
    if purchased_product_ids:
        co_orders_stmt = (
            select(OrderItem.orderId)
            .where(and_(OrderItem.productId.in_(list(purchased_product_ids)), OrderItem.productId.isnot(None)))
            .distinct()
        )
        co_orders_res = await db.execute(co_orders_stmt)
        co_order_ids = co_orders_res.scalars().all()
        
        # Exclude our user's orders
        co_order_ids = [oid for oid in co_order_ids if oid not in user_order_ids]

        if co_order_ids:
            # Query all items in those co-orders to find common co-purchased items
            co_items_stmt = select(OrderItem.productId).where(
                and_(OrderItem.orderId.in_(co_order_ids), OrderItem.productId.notin_(list(purchased_product_ids)))
            )
            co_items_res = await db.execute(co_items_stmt)
            for pid in co_items_res.scalars().all():
                if pid:
                    recommended_product_ids.append(pid)

    # 3. Category Similarity Fallback
    # Recommend active products in same categories user previously purchased, excluding already bought items
    if purchased_categories:
        cat_stmt = select(Product.id).where(
            and_(
                Product.categoryId.in_(list(purchased_categories)),
                Product.id.notin_(list(purchased_product_ids)),
                Product.active == True
            )
        ).limit(3)
        cat_res = await db.execute(cat_stmt)
        for pid in cat_res.scalars().all():
            recommended_product_ids.append(pid)

    # Remove duplicates but preserve ordering
    recommended_pids_unique = []
    seen = set()
    for pid in recommended_product_ids:
        if pid not in seen:
            seen.add(pid)
            recommended_pids_unique.append(pid)

    # 4. Global Fallback: If no recommendations are generated, suggest top active products
    if not recommended_pids_unique:
        fb_stmt = select(Product.id).where(Product.active == True).limit(4)
        fb_res = await db.execute(fb_stmt)
        recommended_pids_unique = list(fb_res.scalars().all())

    # Fetch full product details for recommended IDs
    if not recommended_pids_unique:
        return []

    final_stmt = select(Product).where(Product.id.in_(recommended_pids_unique))
    final_res = await db.execute(final_stmt)
    products = final_res.scalars().all()

    # Convert to ProductResponse
    responses = []
    for p in products:
        category_stmt = select(Category).where(Category.id == p.categoryId)
        cat_obj = (await db.execute(category_stmt)).scalars().first()
        cat_name = cat_obj.name if cat_obj else None

        inv_stmt = select(Inventory).where(Inventory.productId == p.id)
        inv = (await db.execute(inv_stmt)).scalars().first()
        stock = inv.quantity if inv else 0

        responses.append(ProductResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            price=p.price,
            categoryId=p.categoryId,
            categoryName=cat_name,
            active=p.active,
            images=[img.imageUrl for img in p.images],
            stock=stock,
            createdAt=p.createdAt
        ))

    return responses
