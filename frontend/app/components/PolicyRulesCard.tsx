"use client";

import { AlertTriangle, CheckCircle2, Lock, ShieldCheck, Zap } from "lucide-react";

export default function PolicyRulesCard() {
  const rules = [
    {
      id: "rule_1",
      title: "Rule 1: Fraud & Security Risk Guardrail",
      desc: "Intercepts transactions flagged for fraud or risk engine errors (error_source = 'fraud' | 'risk'). Bypasses LLM reasoning and immediately blocks automated recovery to prevent chargebacks.",
      action: "BLOCKED_MANUAL_REVIEW → Escalate to Human Support",
      status: "Active Guardrail",
      color: "border-purple-500/30 bg-purple-500/5 text-purple-300",
      badgeColor: "bg-purple-500/20 text-purple-300 border-purple-500/40",
    },
    {
      id: "rule_2",
      title: "Rule 2: 3-Attempt Customer Intervention Cap",
      desc: "Tracks total historical recovery interventions per customer ID. If a customer has received 3 or more automated recovery attempts, subsequent failures are blocked from auto-messaging.",
      action: "BLOCKED_INTERVENTION_CAP → Escalate to Human Support",
      status: "Active Guardrail",
      color: "border-amber-500/30 bg-amber-500/5 text-amber-300",
      badgeColor: "bg-amber-500/20 text-amber-300 border-amber-500/40",
    },
    {
      id: "rule_3",
      title: "Rule 3: LLM Confidence Threshold (< 70%)",
      desc: "Evaluates the combined diagnosis & strategy confidence score returned by Gemini 2.5 Flash. If confidence is below 0.70, the policy gate blocks automated execution.",
      action: "BLOCKED_LOW_CONFIDENCE → Escalate to Human Support",
      status: "Active Guardrail",
      color: "border-cyan-500/30 bg-cyan-500/5 text-cyan-300",
      badgeColor: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40",
    },
  ];

  return (
    <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl shadow-xl mb-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-400">
            <ShieldCheck className="w-5 h-5 stroke-[2.5]" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
              Deterministic Policy Gate Engine & Guardrails
              <span className="px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 text-[10px] font-mono border border-purple-500/30">
                Regulatory Safe
              </span>
            </h3>
            <p className="text-xs text-slate-400 font-mono">
              Independent, hardcoded business rule layer that overrides AI agent hallucinations
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {rules.map((rule) => (
          <div
            key={rule.id}
            className={`p-5 rounded-2xl border flex flex-col justify-between ${rule.color}`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className={`text-[10px] font-mono font-bold uppercase px-2.5 py-1 rounded-full border ${rule.badgeColor}`}>
                  {rule.status}
                </span>
                <Lock className="w-4 h-4 text-slate-400" />
              </div>
              <h4 className="text-sm font-bold text-white mb-2">
                {rule.title}
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                {rule.desc}
              </p>
            </div>

            <div className="pt-3 border-t border-slate-800/60 font-mono text-xs">
              <span className="text-slate-400 block text-[10px] uppercase">
                Enforced Output
              </span>
              <span className="font-semibold text-white">
                {rule.action}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
