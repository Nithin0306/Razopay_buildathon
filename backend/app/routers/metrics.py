import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AuditLog, Customer, PolicyGateStatus, Transaction, TransactionStatus

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def get_metrics(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Retrieve high-level recovery metrics and performance counters."""
    # Total failed transactions count
    total_failed_res = await db.execute(
        select(func.count(Transaction.id))
    )
    total_failed = total_failed_res.scalar() or 0

    # Total recovered count
    total_recovered_res = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.status == TransactionStatus.RECOVERED
        )
    )
    total_recovered = total_recovered_res.scalar() or 0

    # Total escalated count
    total_escalated_res = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.status == TransactionStatus.ESCALATED
        )
    )
    total_escalated = total_escalated_res.scalar() or 0

    # Blocked by policy gate count
    blocked_res = await db.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.policy_gate_status != PolicyGateStatus.PASSED
        )
    )
    blocked_by_policy = blocked_res.scalar() or 0

    # Sum amount at risk (paise)
    amount_at_risk_res = await db.execute(
        select(func.sum(Transaction.amount_paise))
    )
    total_amount_at_risk = amount_at_risk_res.scalar() or 0

    # Sum amount recovered (paise)
    amount_recovered_res = await db.execute(
        select(func.sum(AuditLog.amount_recovered_paise)).where(
            Transaction.status == TransactionStatus.RECOVERED
        ).join(Transaction, AuditLog.transaction_id == Transaction.id)
    )
    total_amount_recovered = amount_recovered_res.scalar() or 0

    # Calculate recovery rate percentage
    recovery_rate_pct = (
        round((total_recovered / total_failed) * 100, 2) if total_failed > 0 else 0.0
    )

    return {
        "total_failed": total_failed,
        "total_recovered": total_recovered,
        "recovery_rate_pct": recovery_rate_pct,
        "total_amount_at_risk_paise": total_amount_at_risk,
        "total_amount_recovered_paise": total_amount_recovered,
        "escalated_count": total_escalated,
        "blocked_by_policy_count": blocked_by_policy,
    }


@router.get("/audit-log", status_code=status.HTTP_200_OK)
async def get_audit_log(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve paginated audit log entries with joined transaction details."""
    offset = (page - 1) * limit

    # Count total logs
    total_count_res = await db.execute(select(func.count(AuditLog.id)))
    total_logs = total_count_res.scalar() or 0

    # Query paginated audit log joined with transaction and customer
    stmt = (
        select(AuditLog, Transaction, Customer)
        .join(Transaction, AuditLog.transaction_id == Transaction.id)
        .outerjoin(Customer, Transaction.customer_id == Customer.customer_id)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    logs_data = []
    for log, tx, cust in rows:
        logs_data.append({
            "log_id": str(log.id),
            "transaction_id": str(tx.id),
            "razorpay_entity_id": tx.razorpay_entity_id,
            "entity_type": tx.entity_type.value if hasattr(tx.entity_type, "value") else str(tx.entity_type),
            "customer_id": tx.customer_id,
            "customer_email": cust.email if cust else None,
            "customer_phone": cust.phone if cust else None,
            "error_reason": tx.razorpay_error_reason,
            "amount_paise": tx.amount_paise,
            "agent_diagnosis": log.agent_diagnosis,
            "root_cause_category": log.root_cause_category,
            "confidence_score": log.confidence_score,
            "suggested_action": log.suggested_action,
            "policy_gate_status": log.policy_gate_status.value if hasattr(log.policy_gate_status, "value") else str(log.policy_gate_status),
            "final_action": log.final_action,
            "action_result": log.action_result,
            "amount_recovered_paise": log.amount_recovered_paise,
            "recovery_link_url": tx.recovery_link_url,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return {
        "data": logs_data,
        "total": total_logs,
        "page": page,
        "limit": limit,
    }


@router.get("/transactions", status_code=status.HTTP_200_OK)
async def get_transactions(
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List all transactions with optional status filter."""
    stmt = select(Transaction).order_by(Transaction.created_at.desc())
    if status_filter:
        try:
            tx_status_enum = TransactionStatus(status_filter.lower())
            stmt = stmt.where(Transaction.status == tx_status_enum)
        except ValueError:
            logger.warning(f"Invalid status filter requested: {status_filter}")
            return []

    result = await db.execute(stmt)
    transactions = result.scalars().all()

    return [
        {
            "id": str(tx.id),
            "razorpay_entity_id": tx.razorpay_entity_id,
            "entity_type": tx.entity_type.value if hasattr(tx.entity_type, "value") else str(tx.entity_type),
            "customer_id": tx.customer_id,
            "amount_paise": tx.amount_paise,
            "currency": tx.currency,
            "status": tx.status.value if hasattr(tx.status, "value") else str(tx.status),
            "razorpay_error_code": tx.razorpay_error_code,
            "razorpay_error_reason": tx.razorpay_error_reason,
            "recovery_link_id": tx.recovery_link_id,
            "recovery_link_url": tx.recovery_link_url,
            "recovered_at": tx.recovered_at.isoformat() if tx.recovered_at else None,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
        }
        for tx in transactions
    ]
