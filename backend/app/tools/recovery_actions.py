"""
Recovery action executors — each function wraps a specific Razorpay API call
and returns a normalised result dict that is stored in AuditLog.action_result.

Live calls are made when a real Razorpay SDK client is available (i.e. real
credentials are set). When credentials are dummy/missing the functions fall
back to a rich simulation response so the rest of the workflow is unaffected.
"""

import logging
from dataclasses import dataclass
from typing import Any

from app.config import get_settings
from app.tools.razorpay_client import get_razorpay_client

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Shared result dataclass ──────────────────────────────────────────────────

@dataclass
class ActionResult:
    status: str          # "success" | "simulated" | "failed"
    action: str          # action key, mirrors final_action
    live: bool           # True when a real Razorpay API call was made
    data: dict[str, Any] # raw SDK response or simulation payload
    details: str         # human-readable summary


def _result(status: str, action: str, live: bool, data: dict, details: str) -> dict:
    return {
        "status": status,
        "action": action,
        "live": live,
        **data,
        "details": details,
    }


# ── 4.1 Generate Payment Recovery Link ───────────────────────────────────────

def generate_recovery_link(
    *,
    transaction_id: str,
    razorpay_entity_id: str,
    amount_paise: int,
    customer_id: str | None = None,
    customer_email: str | None = None,
    customer_phone: str | None = None,
    customer_name: str | None = None,
    description: str = "Recovery link for failed payment",
    callback_url: str | None = None,
) -> dict[str, Any]:
    """
    Create a Razorpay Payment Link for the failed transaction.
    Returns a normalised result dict with recovery_link_id and recovery_link_url.
    """
    client = get_razorpay_client()
    cb_url = callback_url or f"{settings.frontend_url}/recovery/success"

    payload: dict[str, Any] = {
        "amount": amount_paise,
        "currency": "INR",
        "description": description,
        "customer": {
            "name": customer_name or "Customer",
            "email": customer_email or "",
            "contact": customer_phone or "",
        },
        "notify": {
            "sms": bool(customer_phone),
            "email": bool(customer_email),
        },
        "reminder_enable": True,
        "callback_url": cb_url,
        "callback_method": "get",
        "reference_id": f"recovery_{razorpay_entity_id}",
        "notes": {
            "transaction_id": transaction_id,
            "original_payment_id": razorpay_entity_id,
            "source": "ai_recovery_agent",
        },
    }

    if client:
        try:
            resp = client.payment_link.create(payload)
            logger.info(
                f"[LIVE] Payment link created: {resp.get('id')} for tx={transaction_id}"
            )
            return _result(
                status="success",
                action="generate_recovery_link",
                live=True,
                data={
                    "recovery_link_id": resp.get("id"),
                    "recovery_link_url": resp.get("short_url"),
                    "razorpay_response": {
                        "id": resp.get("id"),
                        "short_url": resp.get("short_url"),
                        "status": resp.get("status"),
                        "amount": resp.get("amount"),
                    },
                },
                details=f"Live payment link created: {resp.get('short_url')}",
            )
        except Exception as exc:
            logger.error(f"Razorpay payment_link.create failed: {exc}")
            return _result(
                status="failed",
                action="generate_recovery_link",
                live=True,
                data={"error": str(exc)},
                details=f"Razorpay API error: {exc}",
            )

    # Simulation mode
    sim_link_id = f"plink_{razorpay_entity_id}"
    sim_url = f"https://rzp.io/i/{sim_link_id}"
    logger.info(f"[SIM] Payment link simulated: {sim_link_id} for tx={transaction_id}")
    return _result(
        status="simulated",
        action="generate_recovery_link",
        live=False,
        data={
            "recovery_link_id": sim_link_id,
            "recovery_link_url": sim_url,
        },
        details="Simulated payment link (no live credentials configured).",
    )


# ── 4.2 Attempt Manual Subscription Charge ───────────────────────────────────

def attempt_manual_charge(
    *,
    transaction_id: str,
    razorpay_entity_id: str,
    entity_type: str = "subscription",
) -> dict[str, Any]:
    """
    Resume or force-charge a halted/pending subscription.
    Uses client.subscription.resume() for halted subs, or
    client.invoice.issue() if an invoice is in draft state.
    """
    client = get_razorpay_client()

    if client:
        try:
            if entity_type == "subscription":
                resp = client.subscription.resume(razorpay_entity_id, {})
                logger.info(f"[LIVE] Subscription resumed: {razorpay_entity_id}")
                return _result(
                    status="success",
                    action="attempt_manual_charge",
                    live=True,
                    data={
                        "subscription_id": razorpay_entity_id,
                        "razorpay_response": {
                            "id": resp.get("id"),
                            "status": resp.get("status"),
                        },
                    },
                    details=f"Subscription {razorpay_entity_id} resume command sent.",
                )
            else:
                # For a payment entity, trigger capture if authorized
                resp = client.payment.capture(razorpay_entity_id, {"amount": 0})
                logger.info(f"[LIVE] Payment capture attempted: {razorpay_entity_id}")
                return _result(
                    status="success",
                    action="attempt_manual_charge",
                    live=True,
                    data={
                        "payment_id": razorpay_entity_id,
                        "razorpay_response": {
                            "id": resp.get("id"),
                            "status": resp.get("status"),
                        },
                    },
                    details=f"Payment capture attempted for {razorpay_entity_id}.",
                )
        except Exception as exc:
            logger.error(f"Razorpay attempt_manual_charge failed: {exc}")
            return _result(
                status="failed",
                action="attempt_manual_charge",
                live=True,
                data={"error": str(exc)},
                details=f"Razorpay API error: {exc}",
            )

    # Simulation mode
    logger.info(f"[SIM] Manual charge simulated for {razorpay_entity_id}")
    return _result(
        status="simulated",
        action="attempt_manual_charge",
        live=False,
        data={"entity_id": razorpay_entity_id, "entity_type": entity_type},
        details="Simulated manual charge (no live credentials configured).",
    )


# ── 4.3 Schedule Retry ───────────────────────────────────────────────────────

def schedule_retry(
    *,
    transaction_id: str,
    razorpay_entity_id: str,
    retry_after_hours: int = 2,
) -> dict[str, Any]:
    """
    Schedule an automated retry for transient failures (network/bank errors).
    In production this would enqueue a delayed Celery/APScheduler job.
    Currently logs intent and returns a scheduled status for the audit trail.
    """
    from datetime import datetime, timedelta, timezone
    retry_at = (
        datetime.now(timezone.utc) + timedelta(hours=retry_after_hours)
    ).isoformat()

    logger.info(
        f"[SCHEDULE] Retry scheduled for tx={transaction_id} at {retry_at}"
    )
    return _result(
        status="scheduled",
        action="schedule_retry",
        live=False,
        data={
            "entity_id": razorpay_entity_id,
            "retry_at": retry_at,
            "retry_after_hours": retry_after_hours,
        },
        details=f"Retry scheduled in {retry_after_hours}h at {retry_at}.",
    )


# ── 4.4 Escalate to Human ────────────────────────────────────────────────────

def escalate_to_human(
    *,
    transaction_id: str,
    razorpay_entity_id: str,
    reason: str = "Agent policy gate blocked automated recovery",
) -> dict[str, Any]:
    """
    Log an escalation event. No Razorpay API call — creates an audit trail
    entry so the support team can act on the transaction.
    """
    logger.warning(
        f"[ESCALATE] tx={transaction_id} ({razorpay_entity_id}) escalated: {reason}"
    )
    return _result(
        status="escalated",
        action="escalate_to_human",
        live=False,
        data={
            "entity_id": razorpay_entity_id,
            "escalation_reason": reason,
        },
        details=reason,
    )
