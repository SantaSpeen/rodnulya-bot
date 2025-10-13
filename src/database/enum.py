import enum


class TransactionType(enum.StrEnum):
    """Типы операций (приход/расход)."""
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    REFUND = "refund"
    PAYMENT = "payment"


class TransactionStatus(enum.StrEnum):
    """Статус операции."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
