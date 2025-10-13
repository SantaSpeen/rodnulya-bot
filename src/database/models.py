from __future__ import annotations

import datetime
from typing import AsyncGenerator, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    String,
    func,
    ForeignKey,
    Enum,
    Numeric,
    Integer,
    CheckConstraint,
    Index,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Reuse your enums module
from database.enum import TransactionType, TransactionStatus  # type: ignore

IdType = BigInteger().with_variant(Integer, "sqlite")

class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# --- Users & Plans ---
class SubscriptionPlan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(IdType, primary_key=True)

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024))
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    squad_uuids: Mapped[Optional[str]] = mapped_column(String(2048))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Creator: make it an FK (a plan can live if creator is deleted)
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ORM relations
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="plan",
        foreign_keys="User.plan_id",
        primaryjoin="User.plan_id == SubscriptionPlan.id",
        passive_deletes=True,
    )

    created_by_user: Mapped["User"] = relationship(
        "User",
        foreign_keys="[SubscriptionPlan.created_by]",
        viewonly=True,
    )

    __table_args__ = (
        Index("ix_plans_is_active", "is_active"),
    )


class User(Base):
    """User model for storing telegram user information."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(IdType, primary_key=True)

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(2), default="ru")

    username: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))

    terms_accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # If plan is deleted, don't delete user; just nullify
    plan_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("plans.id", ondelete="SET NULL"), nullable=True
    )
    active_until: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_moderator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ban_reason: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # ORM relations
    plan: Mapped[Optional["SubscriptionPlan"]] = relationship(
        "SubscriptionPlan",
        back_populates="users",
        foreign_keys="[User.plan_id]",
        primaryjoin="User.plan_id == SubscriptionPlan.id",
    )
    payments: Mapped["Payment"] = relationship("Payment", back_populates="user", passive_deletes=True)
    transactions: Mapped["Transaction"] = relationship("Transaction", back_populates="user", passive_deletes=True)

    __table_args__ = (
        Index("ix_users_active_until", "active_until"),
    )

    @property
    def is_subscription_active(self) -> bool:
        return bool(self.active_until and self.active_until > datetime.datetime.now(datetime.timezone.utc))

    def ban(self, reason: Optional[str] = None) -> "User":
        self.banned = True
        self.ban_reason = reason
        return self

    def unban(self) -> "User":
        self.banned = False
        self.ban_reason = None
        return self

    def accept_terms(self) -> "User":
        self.terms_accepted = True
        return self

    def update_lang(self, lang_code: str) -> "User":
        self.locale = lang_code
        return self

# --- Payments & Transactions ---
class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(IdType, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)

    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="RUB")

    payment_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status"),
        default=TransactionStatus.PENDING,
        nullable=False,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_payments_amount_nonneg"),
        Index("ix_payments_status", "status"),
        Index("ix_payments_created_at", "created_at"),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(IdType, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type"), nullable=False
    )

    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status"),
        default=TransactionStatus.PENDING,
        nullable=False,
    )

    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="RUB", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", back_populates="transactions")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_transactions_amount_nonneg"),
        Index("ix_transactions_status", "status"),
        Index("ix_transactions_type", "type"),
        Index("ix_transactions_created_at", "created_at"),
    )


# --- Database manager ---
class DatabaseManager:
    """Database manager for handling database operations."""

    def __init__(self, database_url: str):
        """Initialize database manager.

        Args:
            database_url: Database connection URL
        """
        self.engine = create_async_engine(database_url, echo=False)
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self) -> None:
        """Initialize database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def dispose(self) -> None:
        """Dispose database engine."""
        await self.engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session.

        Yields:
            AsyncSession: Database session
        """
        async with self.session_factory() as session:
            yield session
