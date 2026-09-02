"""
Phase 4 Diagnostic Test Suite
Tests the Razorpay Execution Tool layer (razorpay_client + recovery_actions)
and verifies that the execute_node correctly dispatches to each action.
Runs entirely in simulation mode (no live Razorpay credentials required).
"""

import asyncio
import time

from sqlalchemy import select

from app.agent.graph import recovery_agent_graph, run_recovery_agent
from app.agent.state import AgentState
from app.database import AsyncSessionLocal, Base, engine
from app.models import (
    AuditLog,
    Customer,
    EntityType,
    PolicyGateStatus,
    Transaction,
    TransactionStatus,
)
from app.tools import recovery_actions
from app.tools.razorpay_client import get_razorpay_client

results: list[dict] = []


def record(name: str, passed: bool, expected: str, actual: str, note: str = ""):
    tag = "PASS" if passed else "FAIL"
    results.append({"name": name, "passed": passed})
    print(f"[{tag}] {name}")
    print(f"       Expected : {expected}")
    print(f"       Actual   : {actual}")
    if note:
        print(f"       Note     : {note}")
    print()


# ── helpers ──────────────────────────────────────────────────────────────────

async def _make_transaction(
    entity_id: str,
    entity_type: EntityType = EntityType.PAYMENT,
    amount: int = 100000,
    error_reason: str = "insufficient_funds",
    error_source: str = "customer",
    cust_id: str | None = None,
    email: str = "test@example.com",
    phone: str = "9999999999",
    interventions: int = 0,
) -> str:
    """Insert a Customer + Transaction row and return transaction_id as str."""
    async with AsyncSessionLocal() as session:
        if cust_id:
            session.add(Customer(
                customer_id=cust_id,
                email=email,
                phone=phone,
                total_interventions=interventions,
            ))
        tx = Transaction(
            razorpay_entity_id=entity_id,
            entity_type=entity_type,
            customer_id=cust_id,
            amount_paise=amount,
            status=TransactionStatus.FAILED,
            razorpay_error_reason=error_reason,
            razorpay_error_source=error_source,
        )
        session.add(tx)
        await session.commit()
        return str(tx.id)


# ── Section 1: razorpay_client singleton ─────────────────────────────────────

def test_client_singleton():
    """Client should be None when dummy credentials are set."""
    client = get_razorpay_client()
    passed = client is None
    record(
        "4.1 SDK Client — None with dummy credentials",
        passed,
        "client is None",
        f"client is {type(client).__name__}",
        "Set RAZORPAY_KEY_ID + RAZORPAY_KEY_SECRET in .env to get a live client",
    )


# ── Section 2: recovery_actions unit tests ───────────────────────────────────

def test_generate_link_sim():
    res = recovery_actions.generate_recovery_link(
        transaction_id="tx_unit_001",
        razorpay_entity_id="pay_unit_001",
        amount_paise=250000,
        customer_email="user@example.com",
        customer_phone="9876543210",
        customer_name="Test User",
    )
    passed = (
        res["action"] == "generate_recovery_link"
        and res["status"] == "simulated"
        and res["live"] is False
        and "recovery_link_id" in res
        and res["recovery_link_url"].startswith("https://rzp.io/i/")
    )
    record(
        "4.2 generate_recovery_link — sim mode",
        passed,
        "status=simulated, live=False, recovery_link_url starts with https://rzp.io/i/",
        f"status={res['status']}, live={res['live']}, url={res.get('recovery_link_url')}",
    )


def test_attempt_manual_charge_sim():
    res = recovery_actions.attempt_manual_charge(
        transaction_id="tx_unit_002",
        razorpay_entity_id="sub_unit_002",
        entity_type="subscription",
    )
    passed = (
        res["action"] == "attempt_manual_charge"
        and res["status"] == "simulated"
        and res["live"] is False
    )
    record(
        "4.3 attempt_manual_charge — sim mode (subscription)",
        passed,
        "status=simulated, live=False",
        f"status={res['status']}, live={res['live']}",
    )


def test_schedule_retry():
    res = recovery_actions.schedule_retry(
        transaction_id="tx_unit_003",
        razorpay_entity_id="pay_unit_003",
        retry_after_hours=3,
    )
    passed = (
        res["action"] == "schedule_retry"
        and res["status"] == "scheduled"
        and "retry_at" in res
        and res["retry_after_hours"] == 3
    )
    record(
        "4.4 schedule_retry — scheduled status with timestamp",
        passed,
        "status=scheduled, retry_at present, retry_after_hours=3",
        f"status={res['status']}, retry_at={res.get('retry_at')}, hours={res.get('retry_after_hours')}",
    )


def test_escalate_to_human():
    reason = "Custom escalation reason"
    res = recovery_actions.escalate_to_human(
        transaction_id="tx_unit_004",
        razorpay_entity_id="pay_unit_004",
        reason=reason,
    )
    passed = (
        res["action"] == "escalate_to_human"
        and res["status"] == "escalated"
        and res["details"] == reason
    )
    record(
        "4.5 escalate_to_human — escalated status with reason",
        passed,
        f"status=escalated, details='{reason}'",
        f"status={res['status']}, details={res.get('details')}",
    )


# ── Section 3: end-to-end graph dispatch ─────────────────────────────────────

async def test_e2e_recovery_link():
    ts = int(time.time() * 1000)
    cust_id = f"cust_p4_link_{ts}"
    entity_id = f"pay_p4_link_{ts}"

    tx_id = await _make_transaction(
        entity_id=entity_id,
        amount=500000,
        error_reason="insufficient_funds",
        cust_id=cust_id,
        email="recovery@example.com",
        phone="9876543210",
    )
    try:
        state = await run_recovery_agent(tx_id)
        action_res = state.get("action_result", {})
        passed = (
            state.get("final_action") == "generate_recovery_link"
            and action_res.get("action") == "generate_recovery_link"
            and "recovery_link_id" in action_res
            and action_res.get("recovery_link_url", "").startswith("https://rzp.io/i/")
        )

        async with AsyncSessionLocal() as session:
            tx = (await session.execute(
                select(Transaction).where(Transaction.id == tx_id)
            )).scalar_one()
            log = (await session.execute(
                select(AuditLog).where(AuditLog.transaction_id == tx_id)
            )).scalar_one()

        passed = passed and (
            tx.status == TransactionStatus.RECOVERING
            and tx.recovery_link_id is not None
            and tx.recovery_link_url is not None
            and log.final_action == "generate_recovery_link"
            and log.policy_gate_status == PolicyGateStatus.PASSED
        )
        record(
            "4.6 E2E — insufficient_funds → generate_recovery_link dispatched",
            passed,
            "status=RECOVERING, recovery_link_id set, AuditLog.final_action=generate_recovery_link",
            f"tx.status={tx.status}, link_id={tx.recovery_link_id}, log.action={log.final_action}",
            f"recovery_link_url={tx.recovery_link_url}",
        )
    except Exception as e:
        record("4.6 E2E — insufficient_funds → generate_recovery_link", False, "success", f"Exception: {e}")


async def test_e2e_schedule_retry():
    ts = int(time.time() * 1000)
    cust_id = f"cust_p4_retry_{ts}"
    entity_id = f"pay_p4_retry_{ts}"

    tx_id = await _make_transaction(
        entity_id=entity_id,
        error_reason="bank_technical_error",
        error_source="bank",
        cust_id=cust_id,
    )
    try:
        state = await run_recovery_agent(tx_id)
        action_res = state.get("action_result", {})
        passed = (
            state.get("final_action") == "schedule_retry"
            and action_res.get("status") == "scheduled"
            and "retry_at" in action_res
        )

        async with AsyncSessionLocal() as session:
            tx = (await session.execute(
                select(Transaction).where(Transaction.id == tx_id)
            )).scalar_one()

        passed = passed and tx.status == TransactionStatus.RECOVERING
        record(
            "4.7 E2E — bank_error → schedule_retry dispatched",
            passed,
            "final_action=schedule_retry, action_result.status=scheduled, tx.status=RECOVERING",
            f"final_action={state.get('final_action')}, result.status={action_res.get('status')}, tx.status={tx.status}",
            f"retry_at={action_res.get('retry_at')}",
        )
    except Exception as e:
        record("4.7 E2E — bank_error → schedule_retry", False, "success", f"Exception: {e}")


async def test_e2e_escalate_fraud():
    ts = int(time.time() * 1000)
    cust_id = f"cust_p4_fraud_{ts}"
    entity_id = f"pay_p4_fraud_{ts}"

    tx_id = await _make_transaction(
        entity_id=entity_id,
        error_reason="suspected_fraud",
        error_source="fraud",
        cust_id=cust_id,
    )
    try:
        state = await run_recovery_agent(tx_id)
        action_res = state.get("action_result", {})
        passed = (
            state.get("final_action") == "escalate_to_human"
            and action_res.get("status") == "escalated"
            and state.get("policy_gate_status") == "blocked_manual_review"
        )

        async with AsyncSessionLocal() as session:
            tx = (await session.execute(
                select(Transaction).where(Transaction.id == tx_id)
            )).scalar_one()
            log = (await session.execute(
                select(AuditLog).where(AuditLog.transaction_id == tx_id)
            )).scalar_one()

        passed = passed and (
            tx.status == TransactionStatus.ESCALATED
            and log.policy_gate_status == PolicyGateStatus.BLOCKED_MANUAL_REVIEW
        )
        record(
            "4.8 E2E — fraud → policy_gate blocks → escalate_to_human",
            passed,
            "policy=blocked_manual_review, tx.status=ESCALATED, action_result.status=escalated",
            f"policy={state.get('policy_gate_status')}, tx.status={tx.status}, result.status={action_res.get('status')}",
            f"escalation_reason={action_res.get('escalation_reason')}",
        )
    except Exception as e:
        record("4.8 E2E — fraud → escalate", False, "success", f"Exception: {e}")


async def test_e2e_subscription_charge():
    ts = int(time.time() * 1000)
    cust_id = f"cust_p4_sub_{ts}"
    entity_id = f"sub_p4_{ts}"

    tx_id = await _make_transaction(
        entity_id=entity_id,
        entity_type=EntityType.SUBSCRIPTION,
        error_reason="subscription_halted",
        cust_id=cust_id,
    )
    try:
        state = await run_recovery_agent(tx_id)
        action_res = state.get("action_result", {})
        passed = (
            state.get("policy_gate_status") == "passed"
            and action_res.get("status") in ("simulated", "success", "scheduled")
        )

        async with AsyncSessionLocal() as session:
            log = (await session.execute(
                select(AuditLog).where(AuditLog.transaction_id == tx_id)
            )).scalar_one()

        passed = passed and log.final_action is not None
        record(
            "4.9 E2E — subscription_halted → action dispatched + AuditLog written",
            passed,
            "policy=passed, action dispatched, AuditLog.final_action set",
            f"policy={state.get('policy_gate_status')}, action={state.get('final_action')}, result.status={action_res.get('status')}",
        )
    except Exception as e:
        record("4.9 E2E — subscription_halted", False, "success", f"Exception: {e}")


async def test_e2e_contact_fields_in_link():
    """Verify customer email/phone/name are threaded into payment link payload."""
    ts = int(time.time() * 1000)
    cust_id = f"cust_p4_contact_{ts}"
    entity_id = f"pay_p4_contact_{ts}"

    tx_id = await _make_transaction(
        entity_id=entity_id,
        amount=199900,
        error_reason="insufficient_funds",
        cust_id=cust_id,
        email="jane.doe@example.com",
        phone="9123456780",
    )
    try:
        state = await run_recovery_agent(tx_id)
        # customer contact fields should be present in state
        passed = (
            state.get("customer_email") == "jane.doe@example.com"
            and state.get("customer_phone") == "9123456780"
            and state.get("final_action") == "generate_recovery_link"
        )
        record(
            "4.10 E2E — customer contact fields threaded into state for payment link",
            passed,
            "state.customer_email=jane.doe@example.com, state.customer_phone=9123456780",
            f"state.customer_email={state.get('customer_email')}, state.customer_phone={state.get('customer_phone')}",
        )
    except Exception as e:
        record("4.10 E2E — customer contact threading", False, "success", f"Exception: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    print("================================================================")
    print("  PHASE 4 DIAGNOSTIC TEST SUITE — RAZORPAY EXECUTION TOOLS")
    print("================================================================\n")

    async with engine.begin() as conn:
        from app.database import Base
        await conn.run_sync(Base.metadata.create_all)

    # Unit tests (sync)
    test_client_singleton()
    test_generate_link_sim()
    test_attempt_manual_charge_sim()
    test_schedule_retry()
    test_escalate_to_human()

    # End-to-end async tests
    await test_e2e_recovery_link()
    await test_e2e_schedule_retry()
    await test_e2e_escalate_fraud()
    await test_e2e_subscription_charge()
    await test_e2e_contact_fields_in_link()

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    print("================================================================")
    print(f"  PHASE 4 SUMMARY: {passed}/{total} PASSED ({failed} FAILED)")
    print("================================================================")

    if failed:
        import sys
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
