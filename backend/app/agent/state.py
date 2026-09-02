from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    transaction_id: str
    razorpay_entity_id: str
    entity_type: str
    amount_paise: int
    customer_id: Optional[str]
    customer_email: Optional[str]
    customer_phone: Optional[str]
    customer_name: Optional[str]
    error_code: Optional[str]
    error_reason: Optional[str]
    error_source: Optional[str]
    error_step: Optional[str]
    raw_payload: Optional[dict[str, Any]]
    customer_total_interventions: int

    # Populated by diagnose node
    diagnosis: str
    root_cause_category: str
    diagnose_confidence: float

    # Populated by strategize node
    suggested_action: str
    action_rationale: str
    strategize_confidence: float
    confidence_score: float

    # Populated by policy gate node
    policy_gate_status: str
    final_action: str

    # Populated by execute node
    action_result: dict[str, Any]

