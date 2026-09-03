import {
  AuditLogEntry,
  AuditLogPaginatedResponse,
  MetricsResponse,
  TransactionEntry,
} from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Mock Fallback Data in case API is offline or loading
const MOCK_METRICS: MetricsResponse = {
  total_failed: 28,
  total_recovered: 14,
  recovery_rate_pct: 50.0,
  total_amount_at_risk_paise: 8450000,
  total_amount_recovered_paise: 4225000,
  escalated_count: 5,
  blocked_by_policy_count: 4,
};

const MOCK_AUDIT_LOGS: AuditLogEntry[] = [
  {
    log_id: "mock_log_1",
    transaction_id: "tx_99812",
    razorpay_entity_id: "pay_N8s9A128ksk",
    entity_type: "payment",
    customer_id: "cust_anand_k",
    customer_email: "anand.kumar@enterprise.in",
    customer_phone: "+91 98765 43210",
    error_reason: "insufficient_funds",
    amount_paise: 1250000,
    agent_diagnosis:
      "Customer card declined due to temporary insufficient funds at billing cycle. Recommended instant digital payment link.",
    root_cause_category: "insufficient_funds",
    confidence_score: 0.94,
    suggested_action: "generate_recovery_link",
    policy_gate_status: "passed",
    final_action: "generate_recovery_link",
    action_result: {
      status: "success",
      recovery_link_id: "plink_N8s9A128ksk",
      recovery_link_url: "https://rzp.io/i/plink_N8s9A128ksk",
      details: "Payment link generated and dispatched via SMS & Email.",
    },
    amount_recovered_paise: 1250000,
    recovery_link_url: "https://rzp.io/i/plink_N8s9A128ksk",
    created_at: new Date(Date.now() - 3 * 60000).toISOString(),
  },
  {
    log_id: "mock_log_2",
    transaction_id: "tx_99813",
    razorpay_entity_id: "pay_Risk99120A",
    entity_type: "payment",
    customer_id: "cust_flagged_user",
    customer_email: "unknown_proxy@temp.org",
    customer_phone: "+91 90000 00000",
    error_reason: "suspected_fraud",
    amount_paise: 8500000,
    agent_diagnosis:
      "High fraud velocity detected from anonymous IP block. Automated recovery blocked by deterministic safety gate.",
    root_cause_category: "fraud_block",
    confidence_score: 0.98,
    suggested_action: "escalate_to_human",
    policy_gate_status: "blocked_manual_review",
    final_action: "escalate_to_human",
    action_result: {
      status: "escalated",
      action: "escalate_to_human",
      escalation_reason: "Policy gate blocked: blocked_manual_review (Rule 1: Fraud Risk)",
    },
    amount_recovered_paise: 0,
    recovery_link_url: null,
    created_at: new Date(Date.now() - 12 * 60000).toISOString(),
  },
  {
    log_id: "mock_log_3",
    transaction_id: "tx_99814",
    razorpay_entity_id: "sub_SubHalted88",
    entity_type: "subscription",
    customer_id: "cust_priya_s",
    customer_email: "priya.sharma@techcorp.io",
    customer_phone: "+91 98123 45678",
    error_reason: "expired_card",
    amount_paise: 499000,
    agent_diagnosis:
      "Subscription renewal failed due to expired card on file. Dispatched card update payment link.",
    root_cause_category: "expired_card",
    confidence_score: 0.91,
    suggested_action: "generate_recovery_link",
    policy_gate_status: "passed",
    final_action: "generate_recovery_link",
    action_result: {
      status: "success",
      recovery_link_id: "plink_SubHalted88",
      recovery_link_url: "https://rzp.io/i/plink_SubHalted88",
      details: "Subscription update link generated.",
    },
    amount_recovered_paise: 499000,
    recovery_link_url: "https://rzp.io/i/plink_SubHalted88",
    created_at: new Date(Date.now() - 25 * 60000).toISOString(),
  },
  {
    log_id: "mock_log_4",
    transaction_id: "tx_99815",
    razorpay_entity_id: "pay_BankErr4001",
    entity_type: "payment",
    customer_id: "cust_rahul_v",
    customer_email: "rahul@verma.com",
    customer_phone: "+91 97112 23344",
    error_reason: "bank_technical_error",
    amount_paise: 299900,
    agent_diagnosis:
      "Transient gateway network timeout at issuing bank. Automated retry scheduled for off-peak retry window.",
    root_cause_category: "bank_block",
    confidence_score: 0.85,
    suggested_action: "schedule_retry",
    policy_gate_status: "passed",
    final_action: "schedule_retry",
    action_result: {
      status: "scheduled",
      retry_after_hours: 2,
      details: "Automated retry scheduled in 2 hours.",
    },
    amount_recovered_paise: 0,
    recovery_link_url: null,
    created_at: new Date(Date.now() - 40 * 60000).toISOString(),
  },
];

export async function fetchMetrics(): Promise<MetricsResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/metrics`, {
      cache: "no-store",
    });
    if (!res.ok) throw new Error("Failed to fetch metrics");
    return await res.json();
  } catch (error) {
    console.warn("Using fallback metrics data:", error);
    return MOCK_METRICS;
  }
}

export async function fetchAuditLog(
  page: number = 1,
  limit: number = 20
): Promise<AuditLogPaginatedResponse> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/audit-log?page=${page}&limit=${limit}`,
      { cache: "no-store" }
    );
    if (!res.ok) throw new Error("Failed to fetch audit log");
    return await res.json();
  } catch (error) {
    console.warn("Using fallback audit log data:", error);
    return {
      data: MOCK_AUDIT_LOGS,
      total: MOCK_AUDIT_LOGS.length,
      page,
      limit,
    };
  }
}

export async function fetchTransactions(
  statusFilter?: string
): Promise<TransactionEntry[]> {
  try {
    const url = statusFilter
      ? `${API_BASE_URL}/api/transactions?status=${statusFilter}`
      : `${API_BASE_URL}/api/transactions`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch transactions");
    return await res.json();
  } catch (error) {
    console.warn("Using fallback transactions data:", error);
    return [];
  }
}

export async function triggerWebhookSimulation(
  payload: Record<string, any>,
  signature: string = "dummy_sig"
): Promise<{ status: string; transaction_id?: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/webhooks/razorpay`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": signature,
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Webhook trigger failed");
    }
    return await res.json();
  } catch (error: any) {
    console.error("Webhook trigger error:", error);
    throw error;
  }
}
