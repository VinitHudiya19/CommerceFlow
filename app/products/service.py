import json
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.products.models import Product, Category, ProductImage
from app.inventory.models import Inventory
from app.products.schemas import ProductRequest, ProductResponse, CategoryRequest, CategoryResponse
from app.common.exceptions import ResourceNotFoundException, BadRequestException
from app.common.redis import cache_get, cache_set, cache_delete

# -- Category Services --

async def create_new_category(request: CategoryRequest, db: AsyncSession) -> CategoryResponse:
    # Verify name uniqueness
    name_stmt = select(Category).where(Category.name == request.name)
    name_res = await db.execute(name_stmt)
    if name_res.scalars().first():
        raise BadRequestException(f"Category name '{request.name}' is already taken")

    category = Category(
        name=request.name,
        description=request.description,
        parentId=request.parentId
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return CategoryResponse.model_validate(category)

async def get_all_categories(db: AsyncSession) -> list[CategoryResponse]:
    stmt = select(Category)
    res = await db.execute(stmt)
    categories = res.scalars().all()
    return [CategoryResponse.model_validate(c) for c in categories]

# -- Product Services --

async def create_new_product(request: ProductRequest, db: AsyncSession) -> ProductResponse:
    # Verify Category exists
    cat_stmt = select(Category).where(Category.id == request.categoryId)
    cat_res = await db.execute(cat_stmt)
    category = cat_res.scalars().first()
    if not category:
        raise ResourceNotFoundException("Category", "id", request.categoryId)

    product = Product(
        name=request.name,
        description=request.description,
        price=request.price,
        categoryId=request.categoryId,
        active=request.active
    )
    db.add(product)
    await db.flush()

    # Seed initial image if provided
    if request.imageUrl:
        image = ProductImage(productId=product.id, imageUrl=request.imageUrl)
        db.add(image)

    # Initialize empty inventory
    inventory = Inventory(productId=product.id, quantity=0, lowStockThreshold=10)
    db.add(inventory)
    await db.commit()
    
    return await get_product_by_id(product.id, db)

async def update_existing_product(product_id: int, request: ProductRequest, db: AsyncSession) -> ProductResponse:
    # Verify Product exists
    stmt = select(Product).where(Product.id == product_id)
    res = await db.execute(stmt)
    product = res.scalars().first()
    if not product:
        raise ResourceNotFoundException("Product", "id", product_id)

    # Verify Category exists
    cat_stmt = select(Category).where(Category.id == request.categoryId)
    cat_res = await db.execute(cat_stmt)
    if not cat_res.scalars().first():
        raise ResourceNotFoundException("Category", "id", request.categoryId)

    product.name = request.name
    product.description = request.description
    product.price = request.price
    product.categoryId = request.categoryId
    product.active = request.active

    # Update or append image
    if request.imageUrl:
        # Clear existing images and set new one
        del_img_stmt = select(ProductImage).where(ProductImage.productId == product_id)
        img_res = await db.execute(del_img_stmt)
        for img in img_res.scalars().all():
            await db.delete(img)
        
        new_img = ProductImage(productId=product_id, imageUrl=request.imageUrl)
        db.add(new_img)

    await db.commit()

    # Evict Cache
    await cache_delete(f"product:{product_id}")
    await cache_delete("products:search:*")

    return await get_product_by_id(product_id, db)

async def deactivate_product(product_id: int, db: AsyncSession):
    stmt = select(Product).where(Product.id == product_id)
    res = await db.execute(stmt)
    product = res.scalars().first()
    if not product:
        raise ResourceNotFoundException("Product", "id", product_id)

    product.active = False
    await db.commit()

    # Evict Cache
    await cache_delete(f"product:{product_id}")

async def get_product_by_id(product_id: int, db: AsyncSession) -> ProductResponse:
    # 1. Try fetching from Redis Cache
    cache_key = f"product:{product_id}"
    cached = await cache_get(cache_key)
    if cached:
        try:
            return ProductResponse.model_validate(json.loads(cached))
        except Exception:
            pass

    # 2. Fetch from DB
    stmt = select(Product).options(selectinload(Product.images), selectinload(Product.category)).where(Product.id == product_id)
    res = await db.execute(stmt)
    product = res.scalars().first()
    if not product:
        raise ResourceNotFoundException("Product", "id", product_id)

    # Resolve category details
    cat_name = product.category.name if product.category else None

    # Resolve stock
    inv_stmt = select(Inventory).where(Inventory.productId == product.id)
    inv_res = await db.execute(inv_stmt)
    inv = inv_res.scalars().first()
    stock = inv.quantity if inv else 0

    response = ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        categoryId=product.categoryId,
        categoryName=cat_name,
        active=product.active,
        images=[img.imageUrl for img in product.images],
        stock=stock,
        createdAt=product.createdAt
    )

    # 3. Store in cache
    await cache_set(cache_key, json.dumps(response.model_dump(mode="json")), ttl=600)
    
    return response

async def search_all_products(
    search: str | None,
    category_id: int | None,
    min_price: float | None,
    max_price: float | None,
    active_only: bool,
    db: AsyncSession
) -> list[ProductResponse]:
    
    # We construct dynamic where conditions (FastAPI dynamic specs)
    conditions = []
    
    if active_only:
        conditions.append(Product.active == True)
        
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern)
            )
        )
        
    if category_id:
        conditions.append(Product.categoryId == category_id)
        
    if min_price is not None:
        conditions.append(Product.price >= min_price)
        
    if max_price is not None:
        conditions.append(Product.price <= max_price)

    stmt = select(Product).options(selectinload(Product.images), selectinload(Product.category))
    if conditions:
        stmt = stmt.where(and_(*conditions))

    res = await db.execute(stmt)
    products = res.scalars().all()

    responses = []
    for p in products:
        # Load Category details
        cat_stmt = select(Category).where(Category.id == p.categoryId)
        cat_res = await db.execute(cat_stmt)
        cat = cat_res.scalars().first()
        cat_name = cat.name if cat else None

        # Load Stock details
        inv_stmt = select(Inventory).where(Inventory.productId == p.id)
        inv_res = await db.execute(inv_stmt)
        inv = inv_res.scalars().first()
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
