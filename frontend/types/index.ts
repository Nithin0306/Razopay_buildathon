export type PolicyGateStatus =
  | "passed"
  | "blocked_fraud"
  | "blocked_manual_review"
  | "blocked_intervention_cap"
  | "blocked_low_confidence"
  | "blocked_high_value";

export type TransactionStatus =
  | "failed"
  | "recovering"
  | "recovered"
  | "escalated";

export interface MetricsResponse {
  total_failed: number;
  total_recovered: number;
  recovery_rate_pct: number;
  total_amount_at_risk_paise: number;
  total_amount_recovered_paise: number;
  escalated_count: number;
  blocked_by_policy_count: number;
}

export interface AuditLogEntry {
  log_id: string;
  transaction_id: string;
  razorpay_entity_id: string;
  entity_type: "payment" | "subscription";
  customer_id: string | null;
  customer_email: string | null;
  customer_phone: string | null;
  error_reason: string | null;
  amount_paise: number;
  agent_diagnosis: string | null;
  root_cause_category: string | null;
  confidence_score: number | null;
  suggested_action: string | null;
  policy_gate_status: PolicyGateStatus;
  final_action: string | null;
  action_result: Record<string, any> | null;
  amount_recovered_paise: number;
  recovery_link_url: string | null;
  created_at: string | null;
}

export interface AuditLogPaginatedResponse {
  data: AuditLogEntry[];
  total: number;
  page: number;
  limit: number;
}

export interface TransactionEntry {
  id: string;
  razorpay_entity_id: string;
  entity_type: string;
  customer_id: string | null;
  amount_paise: number;
  currency: string;
  status: TransactionStatus;
  razorpay_error_code: string | null;
  razorpay_error_reason: string | null;
  recovery_link_id: string | null;
  recovery_link_url: string | null;
  recovered_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface ScenarioDefinition {
  id: string;
  title: string;
  description: string;
  category: "failure" | "recovery";
  event: string;
  amount: number; // in rupees
  icon: string;
  badgeColor: string;
  payload: Record<string, any>;
}
