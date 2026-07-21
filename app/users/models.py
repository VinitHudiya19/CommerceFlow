import enum
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    fullName: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    passwordHash: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    role: Mapped[Role] = mapped_column(SQLEnum(Role), default=Role.CUSTOMER)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    failedAttempts: Mapped[int] = mapped_column(default=0)
    lockTime: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    verificationToken: Mapped[str] = mapped_column(String(100), nullable=True)
    verificationTokenExpiry: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    refresh_token = relationship("RefreshToken", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin")

class Address(Base):
    __tablename__ = "addresses"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    userId: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(50), default="Home") # e.g. Home, Office
    addressLine1: Mapped[str] = mapped_column(String(150))
    addressLine2: Mapped[str] = mapped_column(String(150), nullable=True)
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    pincode: Mapped[str] = mapped_column(String(10))

    # Relationships
    user = relationship("User", back_populates="addresses")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    userId: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expiryDate: Mapped[datetime] = mapped_column(DateTime)

    # Relationships
    user = relationship("User", back_populates="refresh_token")
