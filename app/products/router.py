from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.common.schemas import ApiResponse
from app.products.schemas import ProductRequest, ProductResponse, CategoryRequest, CategoryResponse, PaginatedProductResponse
from app.security.dependencies import get_current_user, get_admin_user
from app.products.service import (
    create_new_category, get_all_categories, create_new_product,
    update_existing_product, deactivate_product, get_product_by_id, search_all_products
)
from app.products.recommendations import get_ai_recommendations

router = APIRouter(tags=["Products & Catalog"])

# -- Categories --

@router.post("/api/categories", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[CategoryResponse])
async def create_category(request: CategoryRequest, _admin: dict = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    # Create new product category (Admin only)
    data = await create_new_category(request, db)
    return ApiResponse(success=True, message="Category created successfully", data=data)

@router.get("/api/categories", response_model=ApiResponse[list[CategoryResponse]])
async def get_categories(db: AsyncSession = Depends(get_db)):
    # Retrieve all categories
    data = await get_all_categories(db)
    return ApiResponse(success=True, message="Categories retrieved", data=data)

# -- Products --

@router.get("/api/products/recommendations", response_model=ApiResponse[list[ProductResponse]])
async def get_recommendations(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Fetch personalized recommendations using AI Recommendation Engine
    data = await get_ai_recommendations(current_user["id"], db)
    return ApiResponse(success=True, message="Recommendations retrieved successfully", data=data)

@router.post("/api/products", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[ProductResponse])
async def create_product(request: ProductRequest, _admin: dict = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    # Publish a new catalog product (Admin only)
    data = await create_new_product(request, db)
    return ApiResponse(success=True, message="Product created successfully", data=data)

@router.put("/api/products/{product_id}", response_model=ApiResponse[ProductResponse])
async def update_product(
    product_id: int,
    request: ProductRequest,
    _admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    # Update catalog product details (Admin only)
    data = await update_existing_product(product_id, request, db)
    return ApiResponse(success=True, message="Product updated successfully", data=data)

@router.delete("/api/products/{product_id}", response_model=ApiResponse[None])
async def delete_product(product_id: int, _admin: dict = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    # Soft delete / deactivate product (Admin only)
    await deactivate_product(product_id, db)
    return ApiResponse(success=True, message="Product deleted successfully", data=None)

@router.get("/api/products/{product_id}", response_model=ApiResponse[ProductResponse])
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    # Get details of a single product (Cached in Redis)
    data = await get_product_by_id(product_id, db)
    return ApiResponse(success=True, message="Product retrieved", data=data)

@router.get("/api/products", response_model=ApiResponse[PaginatedProductResponse])
async def list_products(
    search: str | None = Query(None),
    categoryId: int | None = Query(None),
    minPrice: float | None = Query(None),
    maxPrice: float | None = Query(None),
    activeOnly: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    # Dynamic search products (Dynamic filtering by Category, Price bounds, Name search)
    data = await search_all_products(search, categoryId, minPrice, maxPrice, activeOnly, db)
    return ApiResponse(success=True, message="Products retrieved", data={"content": data})
