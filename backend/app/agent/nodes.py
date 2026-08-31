import logging
from datetime import datetime, timezone
from typing import Any

from google import genai

from app.agent.policy_gate import evaluate_policy
from app.agent.prompts import (
    DIAGNOSE_SYSTEM_PROMPT,
    STRATEGIZE_SYSTEM_PROMPT,
    extract_json_from_text,
)
from app.agent.state import AgentState
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def _get_genai_client() -> genai.Client | None:
    if (
        not settings.gemini_api_key
        or settings.gemini_api_key == "dummy_gemini_key"
    ):
        return None
    try:
        return genai.Client(api_key=settings.gemini_api_key)
    except Exception as e:
        logger.warning(f"Could not initialize GenAI client: {e}")
        return None


async def diagnose_node(state: AgentState) -> dict[str, Any]:
    client = _get_genai_client()
    diagnosis = None
    root_cause = "unknown"
    confidence = 0.70

    if client:
        prompt = DIAGNOSE_SYSTEM_PROMPT.format(
            entity_type=state.get("entity_type", "payment"),
            error_code=state.get("error_code", ""),
            error_reason=state.get("error_reason", ""),
            error_source=state.get("error_source", ""),
            error_step=state.get("error_step", ""),
            raw_payload=state.get("raw_payload", {}),
        )
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            parsed = extract_json_from_text(response.text)
            if parsed and isinstance(parsed, dict):
                diagnosis = parsed.get("diagnosis")
                root_cause = parsed.get("root_cause_category", "unknown")
                confidence = float(parsed.get("confidence", 0.85))
        except Exception as e:
            logger.warning(f"Gemini diagnose LLM call failed, fallback to heuristic: {e}")

    # Fallback Heuristics with precise priority
    if not diagnosis:
        reason = (state.get("error_reason") or "").lower()
        code = (state.get("error_code") or "").lower()
        source = (state.get("error_source") or "").lower()

        if "fraud" in source or "risk" in source or "fraud" in reason:
            root_cause = "fraud_block"
            diagnosis = "Transaction flagged for security risk/fraud."
            confidence = 0.95
        elif "expired" in reason or "expired_card" in reason:
            root_cause = "expired_card"
            diagnosis = "Customer card has expired or details invalid."
            confidence = 0.85
        elif "insufficient" in reason or "funds" in reason:
            root_cause = "insufficient_funds"
            diagnosis = "Customer card declined due to insufficient funds."
            confidence = 0.90
        elif "bank" in reason or "network" in reason or "gateway" in reason or "timeout" in reason:
            root_cause = "bank_block"
            diagnosis = "Bank network or gateway technical error occurred."
            confidence = 0.80
        elif "bad_request" in code:
            root_cause = "insufficient_funds"
            diagnosis = "Transaction failed due to customer request parameters or insufficient funds."
            confidence = 0.80
        else:
            root_cause = "unknown"
            diagnosis = f"Transaction failure recorded: {reason or code or 'unspecified error'}"
            confidence = 0.75

    return {
        "diagnosis": diagnosis,
        "root_cause_category": root_cause,
        "diagnose_confidence": confidence,
    }


async def strategize_node(state: AgentState) -> dict[str, Any]:
    client = _get_genai_client()
    suggested_action = None
    rationale = None
    confidence = 0.80

    root_cause = state.get("root_cause_category", "unknown")
    diagnose_conf = state.get("diagnose_confidence", 0.75)

    if client:
        prompt = STRATEGIZE_SYSTEM_PROMPT.format(
            diagnosis=state.get("diagnosis", ""),
            root_cause_category=root_cause,
            diagnose_confidence=diagnose_conf,
            amount_paise=state.get("amount_paise", 0),
            customer_total_interventions=state.get("customer_total_interventions", 0),
        )
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            parsed = extract_json_from_text(response.text)
            if parsed and isinstance(parsed, dict):
                suggested_action = parsed.get("suggested_action")
                rationale = parsed.get("rationale")
                confidence = float(parsed.get("confidence", 0.85))
        except Exception as e:
            logger.warning(f"Gemini strategize LLM call failed, fallback to heuristic: {e}")

    # Fallback Heuristic Rules
    if not suggested_action:
        if root_cause in ("insufficient_funds", "expired_card"):
            suggested_action = "generate_recovery_link"
            rationale = "Send instant digital recovery link via SMS/Email for customer retry."
            confidence = 0.90
        elif root_cause in ("bank_block", "network"):
            suggested_action = "schedule_retry"
            rationale = "Transient gateway error; schedule automated retry."
            confidence = 0.85
        elif root_cause == "fraud_block":
            suggested_action = "escalate_to_human"
            rationale = "High security risk; escalate to support queue."
            confidence = 0.95
        else:
            suggested_action = "generate_recovery_link"
            rationale = "Default high-probability recovery strategy."
            confidence = 0.75

    combined_confidence = min(diagnose_conf, confidence)

    return {
        "suggested_action": suggested_action,
        "action_rationale": rationale or "",
        "strategize_confidence": confidence,
        "confidence_score": combined_confidence,
    }


async def policy_gate_node(state: AgentState) -> dict[str, Any]:
    policy_res = evaluate_policy(state)
    return {
        "policy_gate_status": policy_res.status.value,
        "final_action": policy_res.final_action,
    }


async def execute_node(state: AgentState) -> dict[str, Any]:
    final_action = state.get("final_action", "escalate_to_human")
    now_iso = datetime.now(timezone.utc).isoformat()

    if final_action == "generate_recovery_link":
        link_id = f"plink_{state.get('razorpay_entity_id', 'test')}"
        short_url = f"https://rzp.io/i/{link_id}"
        result = {
            "status": "success",
            "action": "generate_recovery_link",
            "recovery_link_id": link_id,
            "recovery_link_url": short_url,
            "details": "Payment link generated successfully.",
        }
    elif final_action == "schedule_retry":
        result = {
            "status": "scheduled",
            "action": "schedule_retry",
            "scheduled_at": now_iso,
            "details": "Automated retry scheduled in 2 hours.",
        }
    elif final_action == "attempt_manual_charge":
        result = {
            "status": "initiated",
            "action": "attempt_manual_charge",
            "details": "Manual charge command initiated.",
        }
    else:
        result = {
            "status": "escalated",
            "action": "escalate_to_human",
            "details": "Escalated to human support queue.",
        }

    return {
        "action_result": result,
        "executed_at": now_iso,
    }
