"""Comprehensive Diagnostic Test Suite for Phase 3 (LangGraph Agent & Modular Policy Gate)."""

import asyncio
import time
from datetime import datetime, timezone

from sqlalchemy import select

from app.agent.graph import recovery_agent_graph, run_recovery_agent
from app.agent.policy_gate import PolicyConfig, PolicyGateEngine, evaluate_policy
from app.database import AsyncSessionLocal, Base, engine
from app.models import (
    AuditLog,
    Customer,
    EntityType,
    PolicyGateStatus,
    Transaction,
    TransactionStatus,
)

test_results = []


def record_case(
    scenario_id: int,
    scenario_name: str,
    passed: bool,
    expected: str,
    actual: str,
    details: str,
):
    status_str = "PASS" if passed else "FAIL"
    test_results.append({
        "id": scenario_id,
        "name": scenario_name,
        "passed": passed,
        "status": status_str,
        "expected": expected,
        "actual": actual,
        "details": details,
    })
    print(f"[{status_str}] Scenario {scenario_id}: {scenario_name}")
    print(f"       Expected : {expected}")
    print(f"       Actual   : {actual}")
    print(f"       Details  : {details}\n")


async def run_phase3_input_scenarios():
    print("================================================================")
    print("  PHASE 3 DIAGNOSTIC TEST SUITE — COMPREHENSIVE INPUT MATRIX")
    print("================================================================\n")

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ── Scenario 1: Standard Insufficient Funds (Payment) ──────────────────────
    try:
        ts = int(time.time() * 1000)
        cust_id = f"cust_sc1_{ts}"
        entity_id = f"pay_sc1_{ts}"

        async with AsyncSessionLocal() as session:
            session.add(Customer(customer_id=cust_id, email="sc1@example.com"))
            tx = Transaction(
                razorpay_entity_id=entity_id,
                entity_type=EntityType.PAYMENT,
                customer_id=cust_id,
                amount_paise=250000,
                status=TransactionStatus.FAILED,
                razorpay_error_code="BAD_REQUEST_ERROR",
                razorpay_error_reason="insufficient_funds",
                razorpay_error_source="customer",
                razorpay_error_step="payment_authentication",
            )
            session.add(tx)
            await session.commit()
            tx_id = str(tx.id)

        res = await run_recovery_agent(tx_id)
        passed = (
            res.get("root_cause_category") == "insufficient_funds"
            and res.get("policy_gate_status") == "passed"
            and res.get("final_action") == "generate_recovery_link"
        )
        record_case(
            1,
            "Insufficient Funds (Payment)",
            passed,
            "root_cause=insufficient_funds, policy=passed, action=generate_recovery_link",
            f"root_cause={res.get('root_cause_category')}, policy={res.get('policy_gate_status')}, action={res.get('final_action')}",
            f"Recovery link generated: {res.get('action_result', {}).get('recovery_link_url')}",
        )
    except Exception as e:
        record_case(1, "Insufficient Funds (Payment)", False, "Success", "Exception", str(e))

    # ── Scenario 2: Expired Card Failure ──────────────────────────────────────
    try:
        ts = int(time.time() * 1000)
        cust_id = f"cust_sc2_{ts}"
        entity_id = f"pay_sc2_{ts}"

        async with AsyncSessionLocal() as session:
            session.add(Customer(customer_id=cust_id, email="sc2@example.com"))
            tx = Transaction(
                razorpay_entity_id=entity_id,
                entity_type=EntityType.PAYMENT,
                customer_id=cust_id,
                amount_paise=150000,
                status=TransactionStatus.FAILED,
                razorpay_error_code="BAD_REQUEST_ERROR",
                razorpay_error_reason="expired_card",
                razorpay_error_source="customer",
                razorpay_error_step="payment_authentication",
            )
            session.add(tx)
            await session.commit()
            tx_id = str(tx.id)

        res = await run_recovery_agent(tx_id)
        passed = (
            res.get("root_cause_category") == "expired_card"
            and res.get("policy_gate_status") == "passed"
            and res.get("final_action") == "generate_recovery_link"
        )
        record_case(
            2,
            "Expired Card Failure",
            passed,
            "root_cause=expired_card, policy=passed, action=generate_recovery_link",
            f"root_cause={res.get('root_cause_category')}, policy={res.get('policy_gate_status')}, action={res.get('final_action')}",
            f"Diagnosis: {res.get('diagnosis')}",
        )
    except Exception as e:
        record_case(2, "Expired Card Failure", False, "Success", "Exception", str(e))

    # ── Scenario 3: Bank / Gateway Network Timeout ────────────────────────────
    try:
        ts = int(time.time() * 1000)
        cust_id = f"cust_sc3_{ts}"
        entity_id = f"pay_sc3_{ts}"

        async with AsyncSessionLocal() as session:
            session.add(Customer(customer_id=cust_id, email="sc3@example.com"))
            tx = Transaction(
                razorpay_entity_id=entity_id,
                entity_type=EntityType.PAYMENT,
                customer_id=cust_id,
                amount_paise=500000,
                status=TransactionStatus.FAILED,
                razorpay_error_code="GATEWAY_ERROR",
                razorpay_error_reason="bank_technical_error",
                razorpay_error_source="bank",
                razorpay_error_step="payment_authorization",
            )
            session.add(tx)
            await session.commit()
            tx_id = str(tx.id)

        res = await run_recovery_agent(tx_id)
        passed = (
            res.get("root_cause_category") in ("bank_block", "network")
            and res.get("policy_gate_status") == "passed"
            and res.get("final_action") == "schedule_retry"
        )
        record_case(
            3,
            "Bank Technical Timeout",
            passed,
            "root_cause=bank_block, policy=passed, action=schedule_retry",
            f"root_cause={res.get('root_cause_category')}, policy={res.get('policy_gate_status')}, action={res.get('final_action')}",
            f"Action result: {res.get('action_result')}",
        )
    except Exception as e:
        record_case(3, "Bank Technical Timeout", False, "Success", "Exception", str(e))

    # ── Scenario 4: Security / Fraud Risk Interception ────────────────────────
    try:
        ts = int(time.time() * 1000)
        cust_id = f"cust_sc4_{ts}"
        entity_id = f"pay_sc4_{ts}"

        async with AsyncSessionLocal() as session:
            session.add(Customer(customer_id=cust_id, email="sc4@example.com"))
            tx = Transaction(
                razorpay_entity_id=entity_id,
                entity_type=EntityType.PAYMENT,
                customer_id=cust_id,
                amount_paise=800000,
                status=TransactionStatus.FAILED,
                razorpay_error_code="GATEWAY_ERROR",
                razorpay_error_reason="suspected_fraud",
                razorpay_error_source="fraud",
                razorpay_error_step="risk_check",
            )
            session.add(tx)
            await session.commit()
            tx_id = str(tx.id)

        res = await run_recovery_agent(tx_id)
        passed = (
            res.get("policy_gate_status") == "blocked_manual_review"
            and res.get("final_action") == "escalate_to_human"
        )
        record_case(
            4,
            "Security / Fraud Interception",
            passed,
            "policy=blocked_manual_review, action=escalate_to_human",
            f"policy={res.get('policy_gate_status')}, action={res.get('final_action')}",
            "Fraud error source correctly blocked by Policy Gate Engine",
        )
    except Exception as e:
        record_case(4, "Security / Fraud Interception", False, "Success", "Exception", str(e))

    # ── Scenario 5: Customer Intervention Cap Limit (>= 3 Interventions) ──────
    try:
        ts = int(time.time() * 1000)
        cust_id = f"cust_sc5_{ts}"
        entity_id = f"pay_sc5_{ts}"

        async with AsyncSessionLocal() as session:
            session.add(Customer(customer_id=cust_id, email="sc5@example.com", total_interventions=3))
            tx = Transaction(
                razorpay_entity_id=entity_id,
                entity_type=EntityType.PAYMENT,
                customer_id=cust_id,
                amount_paise=300000,
                status=TransactionStatus.FAILED,
                razorpay_error_code="BAD_REQUEST_ERROR",
                razorpay_error_reason="insufficient_funds",
            )
            session.add(tx)
            await session.commit()
            tx_id = str(tx.id)

        res = await run_recovery_agent(tx_id)
        passed = (
            res.get("policy_gate_status") == "blocked_intervention_cap"
            and res.get("final_action") == "escalate_to_human"
        )
        record_case(
            5,
            "Customer Intervention Cap Limit",
            passed,
            "policy=blocked_intervention_cap, action=escalate_to_human",
            f"policy={res.get('policy_gate_status')}, action={res.get('final_action')}",
            "4th attempt blocked because customer reached 3 interventions limit",
        )
    except Exception as e:
        record_case(5, "Customer Intervention Cap Limit", False, "Success", "Exception", str(e))

    # ── Scenario 6: Low Confidence Score Threshold Block ──────────────────────
    try:
        test_state = {
            "suggested_action": "generate_recovery_link",
            "confidence_score": 0.55,  # Below 0.70 threshold
            "customer_total_interventions": 0,
        }
        res_policy = evaluate_policy(test_state)
        passed = (
            res_policy.status == PolicyGateStatus.BLOCKED_LOW_CONFIDENCE
            and res_policy.final_action == "escalate_to_human"
        )
        record_case(
            6,
            "Low Confidence Score Block (< 0.70)",
            passed,
            "status=blocked_low_confidence, action=escalate_to_human",
            f"status={res_policy.status.value}, action={res_policy.final_action}",
            f"Reason: {res_policy.reason}",
        )
    except Exception as e:
        record_case(6, "Low Confidence Score Block", False, "Success", "Exception", str(e))

    # ── Scenario 7: Subscription Halted / Pending Recovery ────────────────────
    try:
        ts = int(time.time() * 1000)
        cust_id = f"cust_sc7_{ts}"
        entity_id = f"sub_sc7_{ts}"

        async with AsyncSessionLocal() as session:
            session.add(Customer(customer_id=cust_id, email="sc7@example.com"))
            tx = Transaction(
                razorpay_entity_id=entity_id,
                entity_type=EntityType.SUBSCRIPTION,
                customer_id=cust_id,
                amount_paise=99900,
                status=TransactionStatus.FAILED,
                razorpay_error_reason="subscription_halted",
            )
            session.add(tx)
            await session.commit()
            tx_id = str(tx.id)

        res = await run_recovery_agent(tx_id)
        passed = (
            res.get("entity_type") == "subscription"
            and res.get("policy_gate_status") == "passed"
            and res.get("final_action") in ("generate_recovery_link", "attempt_manual_charge")
        )
        record_case(
            7,
            "Subscription Halted Failure",
            passed,
            "entity=subscription, policy=passed",
            f"entity={res.get('entity_type')}, policy={res.get('policy_gate_status')}, action={res.get('final_action')}",
            "Subscription recovery strategy evaluated successfully",
        )
    except Exception as e:
        record_case(7, "Subscription Halted Failure", False, "Success", "Exception", str(e))

    # ── Scenario 8: Missing Customer ID / Anonymous Transaction ───────────────
    try:
        ts = int(time.time() * 1000)
        entity_id = f"pay_sc8_{ts}"

        async with AsyncSessionLocal() as session:
            tx = Transaction(
                razorpay_entity_id=entity_id,
                entity_type=EntityType.PAYMENT,
                customer_id=None,  # Anonymous
                amount_paise=49900,
                status=TransactionStatus.FAILED,
                razorpay_error_reason="insufficient_funds",
            )
            session.add(tx)
            await session.commit()
            tx_id = str(tx.id)

        res = await run_recovery_agent(tx_id)
        passed = (
            res.get("policy_gate_status") == "passed"
            and res.get("final_action") == "generate_recovery_link"
        )
        record_case(
            8,
            "Anonymous Customer Transaction",
            passed,
            "policy=passed, action=generate_recovery_link",
            f"policy={res.get('policy_gate_status')}, action={res.get('final_action')}",
            "Agent handled missing customer_id without exception",
        )
    except Exception as e:
        record_case(8, "Anonymous Customer Transaction", False, "Success", "Exception", str(e))

    # ── Scenario 9: High-Value Enterprise Transaction (₹5,00,000) ──────────────
    try:
        ts = int(time.time() * 1000)
        cust_id = f"cust_sc9_{ts}"
        entity_id = f"pay_sc9_{ts}"

        async with AsyncSessionLocal() as session:
            session.add(Customer(customer_id=cust_id, email="enterprise@corp.com"))
            tx = Transaction(
                razorpay_entity_id=entity_id,
                entity_type=EntityType.PAYMENT,
                customer_id=cust_id,
                amount_paise=50000000,  # ₹5,00,000
                status=TransactionStatus.FAILED,
                razorpay_error_reason="insufficient_funds",
            )
            session.add(tx)
            await session.commit()
            tx_id = str(tx.id)

        res = await run_recovery_agent(tx_id)

        async with AsyncSessionLocal() as session:
            log = (await session.execute(select(AuditLog).where(AuditLog.transaction_id == tx_id))).scalar_one_or_none()
            assert log is not None

        passed = (
            res.get("amount_paise") == 50000000
            and log.final_action == "generate_recovery_link"
        )
        record_case(
            9,
            "High-Value Transaction (₹5,00,000)",
            passed,
            "amount_paise=50000000, AuditLog populated",
            f"amount_paise={res.get('amount_paise')}, log.action={log.final_action}",
            "Enterprise transaction processed and AuditLog accurately persisted",
        )
    except Exception as e:
        record_case(9, "High-Value Transaction", False, "Success", "Exception", str(e))

    # Summary
    total = len(test_results)
    passed_cnt = sum(1 for r in test_results if r["passed"])
    failed_cnt = total - passed_cnt

    print("================================================================")
    print(f"  PHASE 3 DIAGNOSTIC SUMMARY: {passed_cnt}/{total} PASSED ({failed_cnt} FAILED)")
    print("================================================================")


if __name__ == "__main__":
    asyncio.run(run_phase3_input_scenarios())
