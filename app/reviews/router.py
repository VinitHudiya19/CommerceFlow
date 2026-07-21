from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.common.schemas import ApiResponse
from app.reviews.schemas import ReviewRequest, ReviewResponse, AISummaryResponse
from app.security.dependencies import get_current_user
from app.reviews.models import Review
from app.reviews.service import add_product_review, get_product_reviews, get_reviews_ai_summary

router = APIRouter(prefix="/api/reviews", tags=["Reviews & Ratings"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[ReviewResponse])
async def create_review(
    request: ReviewRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Post review rating (1-5) and feedback comment for a product
    data = await add_product_review(current_user["id"], current_user["email"], request, db)
    return ApiResponse(success=True, message="Review submitted successfully", data=data)

@router.get("/product/{product_id}", response_model=ApiResponse[list[ReviewResponse]])
async def get_reviews(product_id: int, db: AsyncSession = Depends(get_db)):
    # Retrieve customer review list for a product
    data = await get_product_reviews(product_id, db)
    return ApiResponse(success=True, message="Reviews retrieved", data=data)

@router.get("/product/{product_id}/rating", response_model=ApiResponse[dict])
async def get_rating_summary(product_id: int, db: AsyncSession = Depends(get_db)):
    # Get aggregated rating statistics (average rating score and count)
    stmt = select(func.avg(Review.rating), func.count(Review.id)).where(Review.productId == product_id)
    res = await db.execute(stmt)
    avg_rating, total_count = res.first() or (0.0, 0)
    
    avg_val = float(avg_rating) if avg_rating is not None else 0.0
    return ApiResponse(success=True, message="Rating summary retrieved", data={
        "averageRating": round(avg_val, 1),
        "totalReviews": total_count
    })

@router.get("/product/{product_id}/ai-summary", response_model=ApiResponse[AISummaryResponse])
async def get_ai_summary(product_id: int, db: AsyncSession = Depends(get_db)):
    # Generate NLP bullet summary of all customer feedback
    data = await get_reviews_ai_summary(product_id, db)
    return ApiResponse(success=True, message="AI summary compiled successfully", data=data)
