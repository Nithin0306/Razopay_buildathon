"""Phase 5 Diagnostic Test Suite (Metrics API & Success Metric Closure)."""

import asyncio
import time
from httpx import ASGITransport, AsyncClient

from app.database import AsyncSessionLocal, Base, engine
from app.main import app
from app.models import AuditLog, Customer, EntityType, Transaction, TransactionStatus

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


async def run_phase5_tests():
    print("================================================================")
    print("  PHASE 5 DIAGNOSTIC TEST SUITE — METRICS & RECOVERY CLOSURE")
    print("================================================================\n")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # ── Test 5.1: Health & Metrics Endpoint Availability ───────────────────
        res_health = await ac.get("/health")
        res_metrics = await ac.get("/api/metrics")
        passed_51 = (
            res_health.status_code == 200
            and res_metrics.status_code == 200
            and "total_failed" in res_metrics.json()
        )
        record(
            "5.1 API Routing & Health Check",
            passed_51,
            "200 OK for /health and /api/metrics",
            f"health={res_health.status_code}, metrics={res_metrics.status_code}",
            f"Metrics keys: {list(res_metrics.json().keys())}",
        )

        # ── Test 5.2: Ingest Payment Failure & Verify Metrics Update ─────────────
        ts = int(time.time() * 1000)
        pay_id = f"pay_p5_{ts}"
        payload_fail = {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": pay_id,
                        "amount": 250000,
                        "currency": "INR",
                        "status": "failed",
                        "customer_id": f"cust_p5_{ts}",
                        "email": "metrics_user@example.com",
                        "contact": "9876543210",
                        "error_code": "BAD_REQUEST_ERROR",
                        "error_reason": "insufficient_funds",
                        "error_source": "customer",
                        "error_step": "payment_authentication",
                    }
                }
            },
        }

        res_post = await ac.post("/webhooks/razorpay", json=payload_fail)
        tx_id = res_post.json().get("transaction_id")
        await asyncio.sleep(0.5)  # Wait for agent background task

        res_metrics_after = await ac.get("/api/metrics")
        metrics_data = res_metrics_after.json()
        passed_52 = (
            res_post.status_code == 200
            and metrics_data.get("total_failed", 0) > 0
            and metrics_data.get("total_amount_at_risk_paise", 0) >= 250000
        )
        record(
            "5.2 Payment Failure Webhook → Metrics Risk Counter Update",
            passed_52,
            "total_failed > 0 and total_amount_at_risk_paise >= 250000",
            f"failed={metrics_data.get('total_failed')}, risk={metrics_data.get('total_amount_at_risk_paise')}",
        )

        # ── Test 5.3: Success Recovery Webhook (`payment_link.paid`) ─────────────
        payload_success = {
            "event": "payment_link.paid",
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": f"plink_{pay_id}",
                        "amount_paid": 250000,
                        "status": "paid",
                    }
                }
            },
        }

        res_success = await ac.post("/webhooks/razorpay", json=payload_success)
        res_metrics_recovered = await ac.get("/api/metrics")
        m_rec = res_metrics_recovered.json()
        passed_53 = (
            res_success.status_code == 200
            and res_success.json().get("status") == "recovered"
            and m_rec.get("total_recovered", 0) > 0
            and m_rec.get("recovery_rate_pct", 0) > 0.0
        )
        record(
            "5.3 Recovery Webhook (payment_link.paid) → Rate & Amount Update",
            passed_53,
            "status=recovered, total_recovered > 0, recovery_rate_pct > 0%",
            f"webhook={res_success.json().get('status')}, recovered={m_rec.get('total_recovered')}, rate={m_rec.get('recovery_rate_pct')}%",
            f"Total recovered amount: ₹{m_rec.get('total_amount_recovered_paise', 0) / 100:.2f}",
        )

        # ── Test 5.4: Paginated Audit Log (`GET /api/audit-log`) ──────────────────
        res_audit = await ac.get("/api/audit-log?page=1&limit=5")
        audit_json = res_audit.json()
        data_list = audit_json.get("data", [])
        passed_54 = (
            res_audit.status_code == 200
            and "data" in audit_json
            and audit_json.get("total", 0) > 0
            and len(data_list) > 0
            and "agent_diagnosis" in data_list[0]
            and "confidence_score" in data_list[0]
        )
        record(
            "5.4 Paginated Audit Log API (`GET /api/audit-log`)",
            passed_54,
            "200 OK with total count, data array, diagnosis & confidence fields",
            f"status={res_audit.status_code}, total={audit_json.get('total')}, page_len={len(data_list)}",
            f"Sample item diagnosis: {data_list[0].get('agent_diagnosis') if data_list else 'N/A'}",
        )

        # ── Test 5.5: Transactions Filter API (`GET /api/transactions`) ────────────
        res_tx_all = await ac.get("/api/transactions")
        res_tx_recovered = await ac.get("/api/transactions?status=recovered")
        res_tx_failed = await ac.get("/api/transactions?status=failed")

        passed_55 = (
            res_tx_all.status_code == 200
            and res_tx_recovered.status_code == 200
            and isinstance(res_tx_all.json(), list)
            and len(res_tx_all.json()) > 0
        )
        record(
            "5.5 Transactions API (`GET /api/transactions?status=...`)",
            passed_55,
            "200 OK list response for all and filtered endpoints",
            f"all={len(res_tx_all.json())}, recovered={len(res_tx_recovered.json())}, failed={len(res_tx_failed.json())}",
        )

    # Summary
    total = len(results)
    passed_cnt = sum(1 for r in results if r["passed"])
    failed_cnt = total - passed_cnt

    print("================================================================")
    print(f"  PHASE 5 SUMMARY: {passed_cnt}/{total} PASSED ({failed_cnt} FAILED)")
    print("================================================================")

    if failed_cnt > 0:
        import sys
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_phase5_tests())
