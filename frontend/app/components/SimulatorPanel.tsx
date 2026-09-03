"use client";

import { useState } from "react";
import { triggerWebhookSimulation } from "@/lib/api";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  CreditCard,
  DollarSign,
  Play,
  ShieldAlert,
  Sparkles,
  Zap,
} from "lucide-react";

interface SimulatorPanelProps {
  onSuccess: () => void;
}

export default function SimulatorPanel({ onSuccess }: SimulatorPanelProps) {
  const [loadingScenario, setLoadingScenario] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<"presets" | "custom">("presets");

  const scenarios = [
    {
      id: "insufficient_funds",
      title: "Card Declined — Insufficient Funds",
      desc: "Agent diagnoses issue, passes policy gate, and dispatches Payment Recovery Link.",
      badge: "Payment Link Action",
      color: "border-emerald-500/40 hover:border-emerald-400 bg-emerald-500/5",
      icon: CreditCard,
      iconColor: "text-emerald-400",
      amount: 49900,
      payload: {
        event: "payment.failed",
        payload: {
          payment: {
            entity: {
              id: `pay_sim_ui_${Date.now().toString().slice(-6)}`,
              amount: 49900,
              currency: "INR",
              status: "failed",
              customer_id: "cust_ui_demo",
              email: "anand.kumar@example.com",
              contact: "9876543210",
              error_code: "BAD_REQUEST_ERROR",
              error_reason: "insufficient_funds",
              error_source: "customer",
              error_step: "payment_authentication",
            },
          },
        },
      },
    },
    {
      id: "bank_timeout",
      title: "Bank Gateway Technical Timeout",
      desc: "Transient network failure. Agent schedules automated off-peak retry.",
      badge: "Schedule Retry",
      color: "border-cyan-500/40 hover:border-cyan-400 bg-cyan-500/5",
      icon: Clock,
      iconColor: "text-cyan-400",
      amount: 299900,
      payload: {
        event: "payment.failed",
        payload: {
          payment: {
            entity: {
              id: `pay_bank_ui_${Date.now().toString().slice(-6)}`,
              amount: 299900,
              currency: "INR",
              status: "failed",
              customer_id: "cust_bank_ui",
              email: "rahul@example.com",
              contact: "9711223344",
              error_code: "GATEWAY_ERROR",
              error_reason: "bank_technical_error",
              error_source: "bank",
              error_step: "payment_processing",
            },
          },
        },
      },
    },
    {
      id: "fraud_risk",
      title: "Security & Fraud Risk Flag",
      desc: "High risk score. Policy Gate blocks automated recovery and escalates to human team.",
      badge: "Policy Gate Blocked",
      color: "border-rose-500/40 hover:border-rose-400 bg-rose-500/5",
      icon: ShieldAlert,
      iconColor: "text-rose-400",
      amount: 850000,
      payload: {
        event: "payment.failed",
        payload: {
          payment: {
            entity: {
              id: `pay_fraud_ui_${Date.now().toString().slice(-6)}`,
              amount: 850000,
              currency: "INR",
              status: "failed",
              customer_id: "cust_risk_ui",
              email: "unknown_proxy@temp.org",
              contact: "9900000000",
              error_code: "RISK_ENGINE_ERROR",
              error_reason: "suspected_fraud",
              error_source: "fraud",
              error_step: "risk_check",
            },
          },
        },
      },
    },
    {
      id: "payment_paid",
      title: "Customer Pays Recovery Link (Profit Saved!)",
      desc: "Simulates customer opening payment link & completing payment. Metric transitions to RECOVERED.",
      badge: "+₹ Profit Recovered",
      color: "border-amber-500/40 hover:border-amber-400 bg-amber-500/5",
      icon: DollarSign,
      iconColor: "text-amber-400",
      amount: 49900,
      payload: {
        event: "payment_link.paid",
        payload: {
          payment_link: {
            entity: {
              id: `plink_pay_sim_ui_${Date.now().toString().slice(-6)}`,
              amount_paid: 49900,
              status: "paid",
            },
          },
        },
      },
    },
  ];

  const handleRunScenario = async (sc: typeof scenarios[0]) => {
    setLoadingScenario(sc.id);
    setLogs((prev) => [
      `[${new Date().toLocaleTimeString()}] Dispatching webhook: ${sc.title}...`,
    ]);

    try {
      const res = await triggerWebhookSimulation(sc.payload);
      setLogs((prev) => [
        ...prev,
        `[${new Date().toLocaleTimeString()}] HTTP 200 OK — Ingested tx=${res.transaction_id || "ok"}`,
        `[${new Date().toLocaleTimeString()}] Triggered LangGraph agent workflow: diagnose → strategize → policy_gate → execute`,
        `[${new Date().toLocaleTimeString()}] Action result written to DB Audit Log.`,
      ]);

      // Give small delay for agent background execution then refresh parent
      setTimeout(() => {
        onSuccess();
        setLoadingScenario(null);
      }, 700);
    } catch (err: any) {
      setLogs((prev) => [
        ...prev,
        `[${new Date().toLocaleTimeString()}] ERROR: ${err.message || "Failed to post webhook"}`,
      ]);
      setLoadingScenario(null);
    }
  };

  return (
    <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl shadow-xl mb-8">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
            <Zap className="w-5 h-5 stroke-[2.5]" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
              Interactive Webhook Simulator & Control Panel
              <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-mono border border-emerald-500/30">
                Judge Mode
              </span>
            </h3>
            <p className="text-xs text-slate-400 font-mono">
              Fire Razorpay webhook payloads live to test agent reasoning & policy guardrails
            </p>
          </div>
        </div>
      </div>

      {/* Preset Scenario Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
        {scenarios.map((sc) => {
          const Icon = sc.icon;
          const isLoading = loadingScenario === sc.id;
          return (
            <button
              key={sc.id}
              onClick={() => handleRunScenario(sc)}
              disabled={loadingScenario !== null}
              className={`p-4 rounded-2xl border transition-all text-left flex flex-col justify-between group ${sc.color} ${
                isLoading ? "opacity-70 scale-[0.98]" : "hover:scale-[1.01]"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Icon className={`w-5 h-5 ${sc.iconColor}`} />
                  <span className="text-[10px] font-mono font-semibold uppercase px-2 py-0.5 rounded-full bg-slate-950/80 border border-slate-800 text-slate-300">
                    {sc.badge}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-white mb-1 group-hover:text-emerald-300 transition-colors">
                  {sc.title}
                </h4>
                <p className="text-[11px] text-slate-400 leading-snug">
                  {sc.desc}
                </p>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">
                  ₹{(sc.amount / 100).toLocaleString("en-IN")}
                </span>
                <span className="flex items-center gap-1 text-emerald-400 font-semibold group-hover:translate-x-0.5 transition-transform">
                  {isLoading ? (
                    "Running..."
                  ) : (
                    <>
                      Fire Event <Play className="w-3 h-3 fill-emerald-400" />
                    </>
                  )}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Live Simulator Console Feed */}
      {logs.length > 0 && (
        <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 space-y-1 overflow-x-auto">
          <div className="flex items-center justify-between text-slate-400 text-[11px] pb-2 border-b border-slate-800 mb-2">
            <span className="flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
              Live Execution Log
            </span>
            <button
              onClick={() => setLogs([])}
              className="text-slate-400 hover:text-slate-200"
            >
              Clear
            </button>
          </div>
          {logs.map((log, idx) => (
            <div
              key={idx}
              className={`${
                log.includes("ERROR")
                  ? "text-rose-400"
                  : log.includes("HTTP 200")
                  ? "text-emerald-400"
                  : "text-slate-300"
              }`}
            >
              {log}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
