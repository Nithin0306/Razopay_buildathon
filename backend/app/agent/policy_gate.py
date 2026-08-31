from dataclasses import dataclass, field
from typing import Any

from app.agent.state import AgentState
from app.models.db import PolicyGateStatus


@dataclass
class PolicyConfig:
    max_interventions_per_customer: int = 3
    min_confidence_threshold: float = 0.70
    blocked_error_sources: list[str] = field(
        default_factory=lambda: ["fraud", "security", "risk"]
    )
    blocked_root_causes: list[str] = field(
        default_factory=lambda: ["fraud_block"]
    )
    fallback_action: str = "escalate_to_human"


@dataclass
class PolicyResult:
    status: PolicyGateStatus
    final_action: str
    reason: str


class PolicyGateEngine:
    def __init__(self, config: PolicyConfig | None = None):
        self.config = config or PolicyConfig()

    def evaluate(self, state: AgentState) -> PolicyResult:
        suggested_action = state.get("suggested_action", "escalate_to_human")
        confidence_score = state.get("confidence_score", 0.0)
        interventions = state.get("customer_total_interventions", 0)
        error_source = (state.get("error_source") or "").lower()
        root_cause = (state.get("root_cause_category") or "").lower()

        # Rule 1: Fraud & Security check
        if (
            error_source in self.config.blocked_error_sources
            or root_cause in self.config.blocked_root_causes
        ):
            return PolicyResult(
                status=PolicyGateStatus.BLOCKED_MANUAL_REVIEW,
                final_action=self.config.fallback_action,
                reason=f"Blocked due to security/fraud risk (source={error_source}, root_cause={root_cause})",
            )

        # Rule 2: Intervention Cap check
        if interventions >= self.config.max_interventions_per_customer:
            return PolicyResult(
                status=PolicyGateStatus.BLOCKED_INTERVENTION_CAP,
                final_action=self.config.fallback_action,
                reason=f"Customer reached intervention cap ({interventions}/{self.config.max_interventions_per_customer})",
            )

        # Rule 3: Low Confidence check
        if confidence_score < self.config.min_confidence_threshold:
            return PolicyResult(
                status=PolicyGateStatus.BLOCKED_LOW_CONFIDENCE,
                final_action=self.config.fallback_action,
                reason=f"Confidence score {confidence_score:.2f} below threshold {self.config.min_confidence_threshold}",
            )

        # Rule 4: Passed policy gate
        return PolicyResult(
            status=PolicyGateStatus.PASSED,
            final_action=suggested_action,
            reason="Policy evaluation passed successfully",
        )


def evaluate_policy(
    state: AgentState, config: PolicyConfig | None = None
) -> PolicyResult:
    engine = PolicyGateEngine(config=config)
    return engine.evaluate(state)
