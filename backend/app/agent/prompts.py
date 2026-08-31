import json
import re
from typing import Any

DIAGNOSE_SYSTEM_PROMPT = """You are an expert payment recovery diagnostic AI.
Analyze the following Razorpay payment/subscription failure details and output a JSON object with:
1. "diagnosis": A concise natural-language explanation of why the payment failed.
2. "root_cause_category": Exactly one of ["insufficient_funds", "network", "bank_block", "expired_card", "fraud_block", "unknown"].
3. "confidence": A float between 0.0 and 1.0 representing your diagnostic confidence.

Input details:
- Entity Type: {entity_type}
- Error Code: {error_code}
- Error Reason: {error_reason}
- Error Source: {error_source}
- Error Step: {error_step}
- Raw Payload: {raw_payload}

Respond ONLY with valid JSON.
"""

STRATEGIZE_SYSTEM_PROMPT = """You are an expert payment recovery strategist AI.
Based on the failure diagnosis, select the highest probability recovery action.

Available Actions:
- "generate_recovery_link": Create a Razorpay Payment Link to send to the customer via SMS/Email.
- "attempt_manual_charge": Retry/charge subscription or payment.
- "schedule_retry": Schedule an automated retry after a cooling period.
- "escalate_to_human": Flag for manual support intervention.

Input Diagnosis:
- Diagnosis: {diagnosis}
- Root Cause Category: {root_cause_category}
- Diagnostic Confidence: {diagnose_confidence}
- Amount (Paise): {amount_paise}
- Customer Interventions: {customer_total_interventions}

Output JSON format:
{{
  "suggested_action": "generate_recovery_link" | "attempt_manual_charge" | "schedule_retry" | "escalate_to_human",
  "rationale": "Reason for selecting this strategy",
  "confidence": float between 0.0 and 1.0
}}

Respond ONLY with valid JSON.
"""


def extract_json_from_text(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    match = re.search(r"(\{.*?\})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return None
