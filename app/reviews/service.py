from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.reviews.models import Review
from app.products.models import Product
from app.reviews.schemas import ReviewRequest, ReviewResponse, AISummaryResponse
from app.common.exceptions import ResourceNotFoundException, BadRequestException
from app.reviews.ai_service import AISummarizerService

async def add_product_review(user_id: int, user_name: str, request: ReviewRequest, db: AsyncSession) -> ReviewResponse:
    # 1. Verify product exists
    prod_stmt = select(Product).where(Product.id == request.productId)
    prod_res = await db.execute(prod_stmt)
    if not prod_res.scalars().first():
        raise ResourceNotFoundException("Product", "id", request.productId)

    # 2. Check if user already reviewed this product
    stmt = select(Review).where(Review.productId == request.productId, Review.userId == user_id)
    res = await db.execute(stmt)
    if res.scalars().first():
        raise BadRequestException("You have already reviewed this product")

    review = Review(
        productId=request.productId,
        userId=user_id,
        userName=user_name,
        rating=request.rating,
        comment=request.comment
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return ReviewResponse.model_validate(review)

async def get_product_reviews(product_id: int, db: AsyncSession) -> list[ReviewResponse]:
    # Fetch all reviews for product ordered by date
    stmt = select(Review).where(Review.productId == product_id).order_by(Review.createdAt.desc())
    res = await db.execute(stmt)
    reviews = res.scalars().all()
    return [ReviewResponse.model_validate(r) for r in reviews]

async def get_reviews_ai_summary(product_id: int, db: AsyncSession) -> AISummaryResponse:
    # 1. Verify product exists
    prod_stmt = select(Product).where(Product.id == product_id)
    prod_res = await db.execute(prod_stmt)
    if not prod_res.scalars().first():
        raise ResourceNotFoundException("Product", "id", product_id)

    # 2. Fetch all reviews
    stmt = select(Review).where(Review.productId == product_id)
    res = await db.execute(stmt)
    reviews = list(res.scalars().all())

    # 3. Call AI Summarizer Service
    summary_text = await AISummarizerService.summarize_reviews(reviews)
    return AISummaryResponse(summary=summary_text)
