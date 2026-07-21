from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    userId: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    productId: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    productName: Mapped[str] = mapped_column(String(150))
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", lazy="selectin")
