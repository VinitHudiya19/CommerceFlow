from decimal import Decimal
from sqlalchemy import Integer, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Cart(Base):
    __tablename__ = "carts"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    userId: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    # Relationships
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan", lazy="selectin")

class CartItem(Base):
    __tablename__ = "cart_items"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cartId: Mapped[int] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"))
    productId: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unitPrice: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Relationships
    cart = relationship("Cart", back_populates="items", lazy="noload")
    product = relationship("Product", lazy="selectin")
