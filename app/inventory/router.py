from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.schemas import ApiResponse
from app.inventory.schemas import InventoryResponse
from app.security.dependencies import get_admin_user
from app.inventory.service import list_all_inventories, update_product_inventory

router = APIRouter(prefix="/api/inventory", tags=["Inventory Management"])

@router.get("", response_model=ApiResponse[list[InventoryResponse]])
async def get_all_inventory(_admin: dict = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    # Retrieve product stocks levels list (Admin only)
    data = await list_all_inventories(db)
    return ApiResponse(success=True, message="Inventory levels retrieved", data=data)

@router.put("/product/{product_id}", response_model=ApiResponse[InventoryResponse])
async def update_inventory(
    product_id: int,
    quantity: int = Query(..., ge=0),
    _admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    # Adjust stock configuration of product item (Admin only)
    data = await update_product_inventory(product_id, quantity, db)
    return ApiResponse(success=True, message="Inventory updated successfully", data=data)
