from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Review(Base):
    __tablename__ = "reviews"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    productId: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    userId: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    userName: Mapped[str] = mapped_column(String(100))
    rating: Mapped[int] = mapped_column(Integer) # 1 to 5
    comment: Mapped[str] = mapped_column(String(1000))
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="reviews")
