"""
Interactive Simulation CLI for AI Revenue Recovery Agent.

Simulates diverse Razorpay failure webhooks, triggers the AI agent pipeline,
evaluates policy gates, executes recovery actions, and verifies metric closure.

Usage:
  python simulate.py --scenario 1
  python simulate.py --all
  python simulate.py --interactive
"""

import argparse
import asyncio
import hmac
import hashlib
import json
import time
from httpx import ASGITransport, AsyncClient, Client

from app.config import get_settings
from app.main import app

settings = get_settings()

SCENARIOS = {
    "1": {
        "name": "Insufficient Funds (Standard Payment Link)",
        "event": "payment.failed",
        "entity_type": "payment",
        "amount": 49900,
        "customer": {"email": "anand.kumar@example.com", "contact": "9876543210"},
        "error": {
            "code": "BAD_REQUEST_ERROR",
            "reason": "insufficient_funds",
            "source": "customer",
            "step": "payment_authentication",
        },
    },
    "2": {
        "name": "Expired Card (Payment Link Generation)",
        "event": "payment.failed",
        "entity_type": "payment",
        "amount": 129900,
        "customer": {"email": "priya.sharma@example.com", "contact": "9812345678"},
        "error": {
            "code": "BAD_REQUEST_ERROR",
            "reason": "expired_card",
            "source": "customer",
            "step": "payment_authorization",
        },
    },
    "3": {
        "name": "Bank Network Gateway Timeout (Scheduled Retry)",
        "event": "payment.failed",
        "entity_type": "payment",
        "amount": 299900,
        "customer": {"email": "rahul.verma@example.com", "contact": "9711223344"},
        "error": {
            "code": "GATEWAY_ERROR",
            "reason": "bank_technical_error",
            "source": "bank",
            "step": "payment_processing",
        },
    },
    "4": {
        "name": "Security Risk Interception (Policy Gate Blocked → Escalate)",
        "event": "payment.failed",
        "entity_type": "payment",
        "amount": 850000,
        "customer": {"email": "suspicious.user@example.com", "contact": "9900000000"},
        "error": {
            "code": "RISK_ENGINE_ERROR",
            "reason": "suspected_fraud",
            "source": "fraud",
            "step": "risk_check",
        },
    },
    "5": {
        "name": "Customer Intervention Cap Limit (Policy Gate Blocked → Escalate)",
        "event": "payment.failed",
        "entity_type": "payment",
        "amount": 199900,
        "customer": {"id": "cust_frequent_retry", "email": "frequent@example.com", "contact": "9888877777"},
        "error": {
            "code": "BAD_REQUEST_ERROR",
            "reason": "insufficient_funds",
            "source": "customer",
            "step": "payment_authentication",
        },
        "pre_seed_interventions": 3,
    },
    "6": {
        "name": "Subscription Halted Failure (Manual Charge / Invoice Trigger)",
        "event": "subscription.halted",
        "entity_type": "subscription",
        "amount": 99900,
        "customer": {"id": "cust_sub_01", "email": "sub.subscriber@example.com", "contact": "9654321098"},
        "error": {
            "reason": "subscription_halted",
        },
    },
    "7": {
        "name": "High-Value Enterprise Transaction (₹5,00,000)",
        "event": "payment.failed",
        "entity_type": "payment",
        "amount": 50000000,
        "customer": {"email": "cfo@enterprise-corp.com", "contact": "9999888877"},
        "error": {
            "code": "BAD_REQUEST_ERROR",
            "reason": "insufficient_funds",
            "source": "customer",
            "step": "payment_authorization",
        },
    },
}


def compute_signature(payload_bytes: bytes) -> str:
    secret = settings.razorpay_webhook_secret
    if secret == "dummy_webhook_secret":
        return "dummy_sig"
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


async def seed_interventions(customer_id: str, count: int):
    from app.database import AsyncSessionLocal
    from app.models import Customer
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        cust_res = await session.execute(
            select(Customer).where(Customer.customer_id == customer_id)
        )
        cust = cust_res.scalar_one_or_none()
        if not cust:
            cust = Customer(customer_id=customer_id, total_interventions=count)
            session.add(cust)
        else:
            cust.total_interventions = count
        await session.commit()


async def run_scenario(key: str, scenario: dict):
    print(f"\n================================================================")
    print(f"  RUNNING SCENARIO {key}: {scenario['name']}")
    print(f"================================================================")

    ts = int(time.time() * 1000)
    entity_id = f"{'sub' if scenario['entity_type'] == 'subscription' else 'pay'}_sim_{key}_{ts}"
    cust = scenario.get("customer", {})
    cust_id = cust.get("id") or f"cust_sim_{key}_{ts}"

    if "pre_seed_interventions" in scenario:
        await seed_interventions(cust_id, scenario["pre_seed_interventions"])
        print(f"[PRE-SEED] Pre-seeded customer {cust_id} with {scenario['pre_seed_interventions']} interventions.")

    # Build Razorpay webhook payload
    if scenario["event"] == "payment.failed":
        payload = {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": entity_id,
                        "amount": scenario["amount"],
                        "currency": "INR",
                        "status": "failed",
                        "customer_id": cust_id,
                        "email": cust.get("email"),
                        "contact": cust.get("contact"),
                        "error_code": scenario["error"].get("code"),
                        "error_reason": scenario["error"].get("reason"),
                        "error_source": scenario["error"].get("source"),
                        "error_step": scenario["error"].get("step"),
                    }
                }
            },
        }
    else:
        payload = {
            "event": scenario["event"],
            "payload": {
                "subscription": {
                    "entity": {
                        "id": entity_id,
                        "amount": scenario["amount"],
                        "customer_id": cust_id,
                        "status": "halted",
                    }
                }
            },
        }

    raw_body = json.dumps(payload).encode("utf-8")
    sig = compute_signature(raw_body)

    print(f"Step 1: Dispatching Webhook Event '{scenario['event']}'")
    print(f"        Entity ID: {entity_id} | Amount: ₹{scenario['amount']/100:,.2f}")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
        resp = await ac.post("/webhooks/razorpay", content=raw_body, headers=headers)
        print(f"        HTTP Response: {resp.status_code} -> {resp.json()}")

        # Wait for async background agent execution
        await asyncio.sleep(0.6)

        # Retrieve Audit Log entry
        res_audit = await ac.get("/api/audit-log?page=1&limit=5")
        data_list = res_audit.json().get("data", [])
        matched_log = next((l for l in data_list if l.get("razorpay_entity_id") == entity_id), None)

        if matched_log:
            print("\nStep 2: Agent Diagnostics & Reasoning Result")
            print(f"        Diagnosis  : {matched_log.get('agent_diagnosis')}")
            print(f"        Category   : {matched_log.get('root_cause_category')}")
            print(f"        Confidence : {matched_log.get('confidence_score')}")

            print("\nStep 3: Policy Gate & Strategic Action")
            print(f"        Policy Gate: {matched_log.get('policy_gate_status')}")
            print(f"        Final Action: {matched_log.get('final_action')}")

            print("\nStep 4: Recovery Execution Payload")
            print(f"        Result     : {json.dumps(matched_log.get('action_result'), indent=2)}")
            if matched_log.get("recovery_link_url"):
                print(f"        Recovery URL: {matched_log.get('recovery_link_url')}")
        else:
            print("        [WARN] Audit log entry still pending background write.")

    return entity_id, scenario["amount"]


async def run_recovery_simulation(entity_id: str, amount_paise: int):
    print(f"\n----------------------------------------------------------------")
    print(f"  SIMULATING RECOVERY: Customer pays via link for {entity_id}")
    print(f"----------------------------------------------------------------")

    payload = {
        "event": "payment_link.paid",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": f"plink_{entity_id}",
                    "amount_paid": amount_paise,
                    "status": "paid",
                }
            }
        },
    }

    raw_body = json.dumps(payload).encode("utf-8")
    sig = compute_signature(raw_body)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {"X-Razorpay-Signature": sig, "Content-Type": "application/json"}
        resp = await ac.post("/webhooks/razorpay", content=raw_body, headers=headers)
        print(f"        HTTP Response: {resp.status_code} -> {resp.json()}")

        res_metrics = await ac.get("/api/metrics")
        m = res_metrics.json()
        print(f"        Updated Metrics: Recovered = {m.get('total_recovered')}/{m.get('total_failed')} "
              f"({m.get('recovery_rate_pct')}%) | Amount Recovered: ₹{m.get('total_amount_recovered_paise')/100:,.2f}")


async def print_overall_dashboard():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/metrics")
        m = res.json()
        print(f"\n================================================================")
        print(f"  LIVE RECOVERY METRICS DASHBOARD SUMMARY")
        print(f"================================================================")
        print(f"  Total Transactions Processed : {m.get('total_failed')}")
        print(f"  Successfully Recovered       : {m.get('total_recovered')}")
        print(f"  Overall Recovery Rate        : {m.get('recovery_rate_pct')}%")
        print(f"  Escalated to Support Queue   : {m.get('escalated_count')}")
        print(f"  Blocked by Policy Gate       : {m.get('blocked_by_policy_count')}")
        print(f"  Total Amount at Risk         : ₹{m.get('total_amount_at_risk_paise', 0)/100:,.2f}")
        print(f"  Total Amount Recovered       : ₹{m.get('total_amount_recovered_paise', 0)/100:,.2f}")
        print(f"================================================================\n")


async def main():
    parser = argparse.ArgumentParser(description="AI Revenue Recovery Agent Simulator")
    parser.add_argument("--scenario", help="Scenario number (1-7 or 'all')")
    parser.add_argument("--all", action="store_true", help="Run all failure scenarios in sequence")
    parser.add_argument("--interactive", action="store_true", help="Interactive terminal menu")
    args = parser.parse_args()

    if args.all or args.scenario == "all":
        recoverable_entities = []
        for k, sc in SCENARIOS.items():
            entity_id, amt = await run_scenario(k, sc)
            if sc.get("error", {}).get("reason") in ("insufficient_funds", "expired_card"):
                recoverable_entities.append((entity_id, amt))

        print("\n>>> Simulating customer payment for recoverable transactions (50% recovery rate simulation)...")
        for entity_id, amt in recoverable_entities[:2]:
            await run_recovery_simulation(entity_id, amt)

        await print_overall_dashboard()

    elif args.scenario and args.scenario in SCENARIOS:
        sc = SCENARIOS[args.scenario]
        entity_id, amt = await run_scenario(args.scenario, sc)
        if sc.get("error", {}).get("reason") in ("insufficient_funds", "expired_card"):
            do_recover = input("\nSimulate customer payment link paid? (y/n): ").strip().lower()
            if do_recover == 'y':
                await run_recovery_simulation(entity_id, amt)
        await print_overall_dashboard()

    else:
        print("\n--- AI REVENUE RECOVERY AGENT SIMULATOR ---")
        print("Available Scenarios:")
        for k, sc in SCENARIOS.items():
            print(f"  [{k}] {sc['name']}")
        print("  [A] Run All Scenarios + Recovery Simulation")
        choice = input("\nSelect scenario to execute (1-7 or A): ").strip()

        if choice.upper() == 'A':
            for k, sc in SCENARIOS.items():
                await run_scenario(k, sc)
            await print_overall_dashboard()
        elif choice in SCENARIOS:
            sc = SCENARIOS[choice]
            entity_id, amt = await run_scenario(choice, sc)
            await print_overall_dashboard()
        else:
            print("Invalid selection.")


if __name__ == "__main__":
    asyncio.run(main())
