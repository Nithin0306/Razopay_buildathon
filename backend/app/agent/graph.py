import logging
from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select

from app.agent.nodes import (
    diagnose_node,
    execute_node,
    policy_gate_node,
    strategize_node,
)
from app.agent.state import AgentState
from app.database import AsyncSessionLocal
from app.models import (
    AuditLog,
    Customer,
    PolicyGateStatus,
    Transaction,
    TransactionStatus,
)

logger = logging.getLogger(__name__)


def create_recovery_agent_graph():
    builder = StateGraph(AgentState)

    builder.add_node("diagnose", diagnose_node)
    builder.add_node("strategize", strategize_node)
    builder.add_node("policy_gate", policy_gate_node)
    builder.add_node("execute", execute_node)

    builder.add_edge(START, "diagnose")
    builder.add_edge("diagnose", "strategize")
    builder.add_edge("strategize", "policy_gate")
    builder.add_edge("policy_gate", "execute")
    builder.add_edge("execute", END)

    return builder.compile()


recovery_agent_graph = create_recovery_agent_graph()


async def run_recovery_agent(transaction_id: str) -> dict[str, Any]:
    async with AsyncSessionLocal() as session:
        # Load transaction
        result = await session.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        tx = result.scalar_one_or_none()
        if not tx:
            logger.error(f"Transaction {transaction_id} not found for agent execution")
            return {"error": "Transaction not found"}

        # Load customer intervention count
        interventions = 0
        if tx.customer_id:
            cust_res = await session.execute(
                select(Customer).where(Customer.customer_id == tx.customer_id)
            )
            cust = cust_res.scalar_one_or_none()
            if cust:
                interventions = cust.total_interventions

        # Prepare initial state
        initial_state: AgentState = {
            "transaction_id": str(tx.id),
            "razorpay_entity_id": tx.razorpay_entity_id,
            "entity_type": tx.entity_type.value if hasattr(tx.entity_type, "value") else str(tx.entity_type),
            "amount_paise": tx.amount_paise,
            "customer_id": tx.customer_id,
            "error_code": tx.razorpay_error_code,
            "error_reason": tx.razorpay_error_reason,
            "error_source": tx.razorpay_error_source,
            "error_step": tx.razorpay_error_step,
            "raw_payload": tx.raw_webhook_payload,
            "customer_total_interventions": interventions,
        }

        # Invoke LangGraph
        final_state = await recovery_agent_graph.ainvoke(initial_state)

        # Parse policy gate status enum
        pg_status_str = final_state.get("policy_gate_status", "passed")
        try:
            pg_status_enum = PolicyGateStatus(pg_status_str)
        except ValueError:
            pg_status_enum = PolicyGateStatus.PASSED

        # Write AuditLog
        audit_log = AuditLog(
            transaction_id=tx.id,
            agent_diagnosis=final_state.get("diagnosis"),
            root_cause_category=final_state.get("root_cause_category"),
            suggested_action=final_state.get("suggested_action"),
            confidence_score=final_state.get("confidence_score"),
            policy_gate_status=pg_status_enum,
            final_action=final_state.get("final_action"),
            action_result=final_state.get("action_result"),
        )
        session.add(audit_log)

        # Update Customer interventions if policy passed
        if pg_status_enum == PolicyGateStatus.PASSED and tx.customer_id:
            cust_res = await session.execute(
                select(Customer).where(Customer.customer_id == tx.customer_id)
            )
            cust = cust_res.scalar_one_or_none()
            if cust:
                cust.total_interventions += 1
                cust.last_intervention_at = datetime.now(timezone.utc)

        # Update Transaction status & recovery links
        action_res = final_state.get("action_result", {})
        if action_res.get("recovery_link_id"):
            tx.recovery_link_id = action_res["recovery_link_id"]
            tx.recovery_link_url = action_res.get("recovery_link_url")
            tx.status = TransactionStatus.RECOVERING
        elif final_state.get("final_action") == "escalate_to_human":
            tx.status = TransactionStatus.ESCALATED
        else:
            tx.status = TransactionStatus.RECOVERING

        await session.commit()

        return dict(final_state)
