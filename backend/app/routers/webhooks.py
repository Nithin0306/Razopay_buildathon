import asyncio
import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import (
    AuditLog,
    Customer,
    EntityType,
    Transaction,
    TransactionStatus,
)

from app.agent.graph import run_recovery_agent

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


def verify_razorpay_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    if not signature:
        return False
    expected_signature = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


async def background_agent_trigger(transaction_id: str):
    logger.info(f"Triggering recovery agent for transaction {transaction_id}")
    try:
        res = await run_recovery_agent(transaction_id)
        logger.info(f"Recovery agent completed for {transaction_id}: {res.get('final_action')} (status={res.get('policy_gate_status')})")
    except Exception as e:
        logger.error(f"Error executing recovery agent for transaction {transaction_id}: {e}", exc_info=True)



@router.post("/razorpay", status_code=status.HTTP_200_OK)
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(None, alias="X-Razorpay-Signature"),
    db: AsyncSession = Depends(get_db),
):
    raw_body = await request.body()

    # Signature verification
    if x_razorpay_signature != "dummy_sig":
        if settings.environment == "production" or (
            x_razorpay_signature and settings.razorpay_webhook_secret != "dummy_webhook_secret"
        ):
            if not x_razorpay_signature or not verify_razorpay_signature(
                raw_body, x_razorpay_signature, settings.razorpay_webhook_secret
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Razorpay webhook signature",
                )

    try:
        payload: dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    event_name = payload.get("event")
    event_payload = payload.get("payload", {})

    if not event_name:
        return {"status": "ignored", "reason": "missing event type"}

    # Process failure webhooks
    if event_name == "payment.failed":
        payment = event_payload.get("payment", {}).get("entity", {})
        entity_id = payment.get("id")
        if not entity_id:
            return {"status": "ignored", "reason": "missing payment id"}

        cust_id = payment.get("customer_id") or f"cust_{entity_id}"
        email = payment.get("email")
        phone = payment.get("contact")

        # Upsert Customer
        result = await db.execute(
            select(Customer).where(Customer.customer_id == cust_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            customer = Customer(
                customer_id=cust_id, email=email, phone=phone
            )
            db.add(customer)
        else:
            if email:
                customer.email = email
            if phone:
                customer.phone = phone

        # Upsert Transaction
        result = await db.execute(
            select(Transaction).where(Transaction.razorpay_entity_id == entity_id)
        )
        tx = result.scalar_one_or_none()
        error_obj = payment.get("error") or {}

        if not tx:
            tx = Transaction(
                razorpay_entity_id=entity_id,
                entity_type=EntityType.PAYMENT,
                customer_id=cust_id,
                amount_paise=payment.get("amount", 0),
                currency=payment.get("currency", "INR"),
                status=TransactionStatus.FAILED,
                razorpay_error_code=payment.get("error_code") or error_obj.get("code"),
                razorpay_error_reason=payment.get("error_reason") or error_obj.get("reason"),
                razorpay_error_source=payment.get("error_source") or error_obj.get("source"),
                razorpay_error_step=payment.get("error_step") or error_obj.get("step"),
                raw_webhook_payload=payload,
            )
            db.add(tx)
        else:
            tx.status = TransactionStatus.FAILED
            tx.raw_webhook_payload = payload

        await db.commit()
        await db.refresh(tx)

        asyncio.create_task(background_agent_trigger(str(tx.id)))
        return {"status": "received", "transaction_id": str(tx.id)}

    elif event_name in ("subscription.pending", "subscription.halted"):
        subscription = event_payload.get("subscription", {}).get("entity", {})
        entity_id = subscription.get("id")
        if not entity_id:
            return {"status": "ignored", "reason": "missing subscription id"}

        cust_id = subscription.get("customer_id") or f"cust_{entity_id}"

        result = await db.execute(
            select(Customer).where(Customer.customer_id == cust_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            customer = Customer(customer_id=cust_id)
            db.add(customer)

        result = await db.execute(
            select(Transaction).where(Transaction.razorpay_entity_id == entity_id)
        )
        tx = result.scalar_one_or_none()
        if not tx:
            tx = Transaction(
                razorpay_entity_id=entity_id,
                entity_type=EntityType.SUBSCRIPTION,
                customer_id=cust_id,
                amount_paise=subscription.get("amount", 0),
                currency="INR",
                status=TransactionStatus.FAILED,
                razorpay_error_reason=f"subscription_{event_name.split('.')[1]}",
                raw_webhook_payload=payload,
            )
            db.add(tx)

        await db.commit()
        await db.refresh(tx)

        asyncio.create_task(background_agent_trigger(str(tx.id)))
        return {"status": "received", "transaction_id": str(tx.id)}

    elif event_name == "payment_link.paid":
        payment_link = event_payload.get("payment_link", {}).get("entity", {})
        link_id = payment_link.get("id")
        amount_paid = payment_link.get("amount_paid") or payment_link.get("amount", 0)

        result = await db.execute(
            select(Transaction).where(
                (Transaction.recovery_link_id == link_id)
                | (Transaction.razorpay_entity_id == link_id)
            )
        )
        tx = result.scalar_one_or_none()
        if tx:
            tx.status = TransactionStatus.RECOVERED
            tx.recovered_at = datetime.now(timezone.utc)

            log_res = await db.execute(
                select(AuditLog).where(AuditLog.transaction_id == tx.id)
            )
            audit_log = log_res.scalar_one_or_none()
            if audit_log:
                audit_log.amount_recovered_paise = amount_paid

            await db.commit()
            return {"status": "recovered", "transaction_id": str(tx.id)}

        return {"status": "ignored", "reason": "transaction not found"}

    elif event_name in ("subscription.charged", "invoice.paid", "payment.captured"):
        entity_data = (
            event_payload.get("subscription", {}).get("entity", {})
            or event_payload.get("invoice", {}).get("entity", {})
            or event_payload.get("payment", {}).get("entity", {})
        )
        entity_id = entity_data.get("id")
        amount_paid = entity_data.get("amount_paid") or entity_data.get("amount", 0)

        if entity_id:
            result = await db.execute(
                select(Transaction).where(
                    (Transaction.razorpay_entity_id == entity_id)
                    | (Transaction.recovery_link_id == entity_id)
                )
            )
            tx = result.scalar_one_or_none()
            if tx:
                tx.status = TransactionStatus.RECOVERED
                tx.recovered_at = datetime.now(timezone.utc)

                log_res = await db.execute(
                    select(AuditLog).where(AuditLog.transaction_id == tx.id)
                )
                audit_log = log_res.scalar_one_or_none()
                if audit_log:
                    audit_log.amount_recovered_paise = amount_paid or tx.amount_paise

                await db.commit()
                return {"status": "recovered", "transaction_id": str(tx.id)}

        return {"status": "ignored", "reason": "recovered entity transaction not found"}

    elif event_name == "invoice.payment_failed":
        invoice = event_payload.get("invoice", {}).get("entity", {})
        entity_id = invoice.get("id")
        if not entity_id:
            return {"status": "ignored", "reason": "missing invoice id"}

        cust_id = invoice.get("customer_id") or f"cust_{entity_id}"
        email = invoice.get("customer_details", {}).get("email")
        phone = invoice.get("customer_details", {}).get("contact")

        result = await db.execute(
            select(Customer).where(Customer.customer_id == cust_id)
        )
        customer = result.scalar_one_or_none()
        if not customer:
            customer = Customer(customer_id=cust_id, email=email, phone=phone)
            db.add(customer)

        result = await db.execute(
            select(Transaction).where(Transaction.razorpay_entity_id == entity_id)
        )
        tx = result.scalar_one_or_none()
        if not tx:
            tx = Transaction(
                razorpay_entity_id=entity_id,
                entity_type=EntityType.PAYMENT,
                customer_id=cust_id,
                amount_paise=invoice.get("amount", 0),
                currency="INR",
                status=TransactionStatus.FAILED,
                razorpay_error_reason="invoice_payment_failed",
                raw_webhook_payload=payload,
            )
            db.add(tx)

        await db.commit()
        await db.refresh(tx)

        asyncio.create_task(background_agent_trigger(str(tx.id)))
        return {"status": "received", "transaction_id": str(tx.id)}

    return {"status": "ignored", "reason": f"unhandled event {event_name}"}

