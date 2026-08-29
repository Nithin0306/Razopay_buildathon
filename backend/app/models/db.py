import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import CHAR, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class EntityType(str, enum.Enum):
    PAYMENT = "payment"
    SUBSCRIPTION = "subscription"
    INVOICE = "invoice"


class TransactionStatus(str, enum.Enum):
    FAILED = "failed"
    PENDING = "pending"
    RECOVERING = "recovering"
    RECOVERED = "recovered"
    ESCALATED = "escalated"


class PolicyGateStatus(str, enum.Enum):
    PASSED = "passed"
    BLOCKED_INTERVENTION_CAP = "blocked_intervention_cap"
    BLOCKED_LOW_CONFIDENCE = "blocked_low_confidence"
    BLOCKED_MANUAL_REVIEW = "blocked_manual_review"


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_interventions: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    last_intervention_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="customer"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    razorpay_entity_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    entity_type: Mapped[EntityType] = mapped_column(
        SQLEnum(EntityType, values_callable=lambda x: [e.value for e in x])
    )
    customer_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey("customers.customer_id"), nullable=True
    )
    amount_paise: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(
        String(3), default="INR", server_default="INR"
    )
    status: Mapped[TransactionStatus] = mapped_column(
        SQLEnum(TransactionStatus, values_callable=lambda x: [e.value for e in x]),
        default=TransactionStatus.FAILED,
        server_default=TransactionStatus.FAILED.value,
    )
    razorpay_error_code: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    razorpay_error_reason: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    razorpay_error_source: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    razorpay_error_step: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    raw_webhook_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    recovery_link_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    recovery_link_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recovered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    customer: Mapped[Optional["Customer"]] = relationship(
        "Customer", back_populates="transactions"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="transaction"
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("transactions.id"),
        index=True,
    )
    agent_diagnosis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    root_cause_category: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    suggested_action: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    policy_gate_status: Mapped[Optional[PolicyGateStatus]] = mapped_column(
        SQLEnum(PolicyGateStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    final_action: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    action_result: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    amount_recovered_paise: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    transaction: Mapped["Transaction"] = relationship(
        "Transaction", back_populates="audit_logs"
    )
