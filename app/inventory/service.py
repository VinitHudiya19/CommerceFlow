from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.inventory.models import Inventory
from app.products.models import Product
from app.inventory.schemas import InventoryResponse
from app.common.exceptions import ResourceNotFoundException

async def list_all_inventories(db: AsyncSession) -> list[InventoryResponse]:
    stmt = select(Inventory).options(selectinload(Inventory.product))
    res = await db.execute(stmt)
    inventories = res.scalars().all()
    
    responses = []
    for inv in inventories:
        product = inv.product
        prod_name = product.name if product else "Unknown Product"
        responses.append(InventoryResponse(
            id=inv.id,
            productId=inv.productId,
            productName=prod_name,
            quantity=inv.quantity,
            lowStockThreshold=inv.lowStockThreshold
        ))
    return responses

async def update_product_inventory(product_id: int, quantity: int, db: AsyncSession) -> InventoryResponse:
    # Verify product exists
    prod_stmt = select(Product).where(Product.id == product_id)
    prod_res = await db.execute(prod_stmt)
    product = prod_res.scalars().first()
    if not product:
        raise ResourceNotFoundException("Product", "id", product_id)

    # Fetch inventory
    inv_stmt = select(Inventory).where(Inventory.productId == product_id)
    inv_res = await db.execute(inv_stmt)
    inv = inv_res.scalars().first()
    
    if not inv:
        # Create inventory if somehow not exists
        inv = Inventory(productId=product_id, quantity=quantity, lowStockThreshold=10)
        db.add(inv)
    else:
        inv.quantity = quantity

    await db.commit()
    await db.refresh(inv)

    return InventoryResponse(
        id=inv.id,
        productId=inv.productId,
        productName=product.name,
        quantity=inv.quantity,
        lowStockThreshold=inv.lowStockThreshold
    )
