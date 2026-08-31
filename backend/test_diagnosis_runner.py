"""Diagnostic Test Runner for Phase 1 (Database) and Phase 2 (Webhook Ingestion)."""

import asyncio
import hashlib
import hmac
import sys
import time
from datetime import datetime, timezone

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.config import get_settings
from app.database import AsyncSessionLocal, Base, engine
from app.main import app
from app.models import (
    AuditLog,
    Customer,
    EntityType,
    PolicyGateStatus,
    Transaction,
    TransactionStatus,
)
from app.schemas.webhook import PaymentEntity, RazorpayError, WebhookEvent

results = []


def record_result(phase: str, test_name: str, passed: bool, details: str):
    status_str = "PASS" if passed else "FAIL"
    results.append({
        "phase": phase,
        "test_name": test_name,
        "passed": passed,
        "status": status_str,
        "details": details,
    })
    print(f"[{status_str}] {phase} :: {test_name} - {details}")


async def run_phase1_tests():
    print("\n--- Running Phase 1: Database & ORM Layer Tests ---")

    # Test 1.1: Config & Engine Initialization
    try:
        settings = get_settings()
        assert settings.database_url is not None
        record_result("Phase 1", "Config & Engine Init", True, f"DB URL: {settings.database_url}")
    except Exception as e:
        record_result("Phase 1", "Config & Engine Init", False, str(e))

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Test 1.2: Customer CRUD
    try:
        async with AsyncSessionLocal() as session:
            cust_id = f"diag_cust_{int(time.time())}"
            cust = Customer(
                customer_id=cust_id,
                email="diag@example.com",
                phone="+919876543210",
                name="Diagnostic User",
            )
            session.add(cust)
            await session.commit()

            fetched = (
                await session.execute(
                    select(Customer).where(Customer.customer_id == cust_id)
                )
            ).scalar_one_or_none()

            assert fetched is not None
            assert fetched.email == "diag@example.com"

            # Update
            fetched.total_interventions += 1
            await session.commit()

            updated = (
                await session.execute(
                    select(Customer).where(Customer.customer_id == cust_id)
                )
            ).scalar_one()

            assert updated.total_interventions == 1
            record_result(
                "Phase 1",
                "Customer Model CRUD",
                True,
                f"Customer {cust_id} created and updated successfully",
            )
    except Exception as e:
        record_result("Phase 1", "Customer Model CRUD", False, str(e))

    # Test 1.3: Transaction CRUD & Enum Handling
    try:
        async with AsyncSessionLocal() as session:
            tx_entity_id = f"pay_diag_{int(time.time())}"
            tx = Transaction(
                razorpay_entity_id=tx_entity_id,
                entity_type=EntityType.PAYMENT,
                amount_paise=150000,
                status=TransactionStatus.FAILED,
                razorpay_error_code="BAD_REQUEST_ERROR",
                razorpay_error_reason="insufficient_funds",
                raw_webhook_payload={"test": "diagnostic_data"},
            )
            session.add(tx)
            await session.commit()

            fetched_tx = (
                await session.execute(
                    select(Transaction).where(
                        Transaction.razorpay_entity_id == tx_entity_id
                    )
                )
            ).scalar_one_or_none()

            assert fetched_tx is not None
            assert fetched_tx.amount_paise == 150000
            assert fetched_tx.status == TransactionStatus.FAILED
            record_result(
                "Phase 1",
                "Transaction Model CRUD",
                True,
                f"Transaction {fetched_tx.id} created with status {fetched_tx.status}",
            )
    except Exception as e:
        record_result("Phase 1", "Transaction Model CRUD", False, str(e))

    # Test 1.4: AuditLog Model & Relationship FK
    try:
        async with AsyncSessionLocal() as session:
            # Get previous transaction
            tx = (
                await session.execute(
                    select(Transaction).where(
                        Transaction.razorpay_entity_id == tx_entity_id
                    )
                )
            ).scalar_one()

            log_entry = AuditLog(
                transaction_id=tx.id,
                agent_diagnosis="Insufficient funds in customer account",
                root_cause_category="insufficient_funds",
                suggested_action="generate_recovery_link",
                confidence_score=0.95,
                policy_gate_status=PolicyGateStatus.PASSED,
                final_action="generate_recovery_link",
            )
            session.add(log_entry)
            await session.commit()

            # Relationship check
            tx_with_logs = (
                await session.execute(
                    select(Transaction).where(Transaction.id == tx.id)
                )
            ).scalar_one()

            # Query audit log by FK
            fetched_log = (
                await session.execute(
                    select(AuditLog).where(AuditLog.transaction_id == tx.id)
                )
            ).scalar_one()

            assert fetched_log.confidence_score == 0.95
            record_result(
                "Phase 1",
                "AuditLog Model & FK Relationship",
                True,
                f"AuditLog {fetched_log.id} linked to Transaction {tx.id}",
            )
    except Exception as e:
        record_result("Phase 1", "AuditLog Model & FK Relationship", False, str(e))


async def run_phase2_tests():
    print("\n--- Running Phase 2: Razorpay Webhook Ingestion Tests ---")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        # Test 2.1: Health Endpoint Check
        try:
            res = await client.get("/health")
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "ok"
            record_result("Phase 2", "API Health Endpoint", True, f"Response: {data}")
        except Exception as e:
            record_result("Phase 2", "API Health Endpoint", False, str(e))

        # Test 2.2: Pydantic Schema Parsing Test
        try:
            payload_dict = {
                "entity": "event",
                "event": "payment.failed",
                "payload": {
                    "payment": {
                        "entity": {
                            "id": "pay_schema_test",
                            "amount": 50000,
                            "currency": "INR",
                            "status": "failed",
                            "error_reason": "insufficient_funds",
                        }
                    }
                },
                "created_at": int(time.time()),
            }
            parsed_event = WebhookEvent.model_validate(payload_dict)
            assert parsed_event.event == "payment.failed"
            record_result(
                "Phase 2",
                "Pydantic Schema Parsing",
                True,
                f"Parsed event '{parsed_event.event}' successfully",
            )
        except Exception as e:
            record_result("Phase 2", "Pydantic Schema Parsing", False, str(e))

        # Test 2.3: Signature Verification Logic
        try:
            secret = "test_secret_key"
            body = b'{"event":"test"}'
            sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

            from app.routers.webhooks import verify_razorpay_signature

            assert verify_razorpay_signature(body, sig, secret) is True
            assert verify_razorpay_signature(body, "invalid_sig", secret) is False
            record_result(
                "Phase 2",
                "HMAC Signature Verification",
                True,
                "Valid signature passed, invalid signature rejected",
            )
        except Exception as e:
            record_result("Phase 2", "HMAC Signature Verification", False, str(e))

        # Test 2.4: `payment.failed` Ingestion Endpoint
        pay_id = f"pay_wh_{int(time.time())}"
        cust_id = f"cust_wh_{int(time.time())}"
        try:
            webhook_body = {
                "event": "payment.failed",
                "payload": {
                    "payment": {
                        "entity": {
                            "id": pay_id,
                            "amount": 350000,
                            "currency": "INR",
                            "status": "failed",
                            "customer_id": cust_id,
                            "email": "wh_test@razorpay.com",
                            "contact": "+919123456789",
                            "error_code": "BAD_REQUEST_ERROR",
                            "error_reason": "insufficient_funds",
                            "error_source": "customer",
                            "error_step": "payment_authentication",
                        }
                    }
                },
            }
            res = await client.post("/webhooks/razorpay", json=webhook_body)
            assert res.status_code == 200
            json_res = res.json()
            assert json_res["status"] == "received"
            assert "transaction_id" in json_res

            # Verify in DB
            async with AsyncSessionLocal() as session:
                tx = (
                    await session.execute(
                        select(Transaction).where(
                            Transaction.razorpay_entity_id == pay_id
                        )
                    )
                ).scalar_one()

                assert tx.status == TransactionStatus.FAILED
                assert tx.amount_paise == 350000
                assert tx.razorpay_error_reason == "insufficient_funds"

                cust = (
                    await session.execute(
                        select(Customer).where(Customer.customer_id == cust_id)
                    )
                ).scalar_one()

                assert cust.email == "wh_test@razorpay.com"

            record_result(
                "Phase 2",
                "payment.failed Webhook Ingestion",
                True,
                f"Ingested payment {pay_id}, created Customer {cust_id} and Transaction",
            )
        except Exception as e:
            record_result(
                "Phase 2", "payment.failed Webhook Ingestion", False, str(e)
            )

        # Test 2.5: Idempotent Duplicate Webhook Handling
        try:
            res = await client.post("/webhooks/razorpay", json=webhook_body)
            assert res.status_code == 200
            assert res.json()["status"] == "received"
            record_result(
                "Phase 2",
                "Duplicate Webhook Idempotency",
                True,
                "Re-ingested duplicate webhook without DB constraint violation",
            )
        except Exception as e:
            record_result(
                "Phase 2", "Duplicate Webhook Idempotency", False, str(e)
            )

        # Test 2.6: `payment_link.paid` Recovery Webhook
        try:
            paid_body = {
                "event": "payment_link.paid",
                "payload": {
                    "payment_link": {
                        "entity": {
                            "id": pay_id,
                            "amount_paid": 350000,
                        }
                    }
                },
            }
            res = await client.post("/webhooks/razorpay", json=paid_body)
            assert res.status_code == 200
            assert res.json()["status"] == "recovered"

            # Check DB status transition
            async with AsyncSessionLocal() as session:
                tx = (
                    await session.execute(
                        select(Transaction).where(
                            Transaction.razorpay_entity_id == pay_id
                        )
                    )
                ).scalar_one()

                assert tx.status == TransactionStatus.RECOVERED
                assert tx.recovered_at is not None

            record_result(
                "Phase 2",
                "payment_link.paid Status Transition",
                True,
                f"Transaction {pay_id} status updated to RECOVERED with timestamp {tx.recovered_at}",
            )
        except Exception as e:
            record_result(
                "Phase 2", "payment_link.paid Status Transition", False, str(e)
            )


async def main():
    print("================================================================")
    print("   AI REVENUE RECOVERY AGENT — DIAGNOSTIC TEST SUITE (P1 & P2)")
    print("================================================================")
    await run_phase1_tests()
    await run_phase2_tests()

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = total - passed_count

    print("\n================================================================")
    print(f"SUMMARY: {passed_count}/{total} PASSED ({failed_count} FAILED)")
    print("================================================================")

    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
