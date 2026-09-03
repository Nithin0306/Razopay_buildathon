"use client";

import { MetricsResponse } from "@/types";
import {
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  DollarSign,
  ShieldAlert,
  TrendingUp,
  Zap,
} from "lucide-react";

interface HeroProfitCardsProps {
  metrics: MetricsResponse;
}

export default function HeroProfitCards({ metrics }: HeroProfitCardsProps) {
  const recoveredRupees = metrics.total_amount_recovered_paise / 100;
  const atRiskRupees = metrics.total_amount_at_risk_paise / 100;

  const formatINR = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
      {/* ── CARD 1: HERO PROFIT SAVED (EMOTIONAL IMPACT CARD) ───────────────── */}
      <div className="relative overflow-hidden p-6 rounded-3xl bg-gradient-to-b from-slate-900/90 via-slate-900/60 to-emerald-950/30 border border-emerald-500/40 shadow-2xl shadow-emerald-500/10 group transition-all duration-300 hover:border-emerald-400 hover:shadow-emerald-500/20">
        {/* Glow Effects */}
        <div className="absolute -right-10 -top-10 w-36 h-36 bg-emerald-500/15 rounded-full blur-3xl group-hover:bg-emerald-500/25 transition-all duration-500" />
        <div className="absolute left-0 bottom-0 w-full h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400" />

        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 shadow-md shadow-emerald-500/20">
              <DollarSign className="w-5 h-5 stroke-[2.5]" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 font-mono">
                Profit Recovered
              </span>
              <p className="text-[11px] text-slate-400 font-medium">
                Saved by AI Agent
              </p>
            </div>
          </div>
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-xs font-semibold font-mono">
            <ArrowUpRight className="w-3.5 h-3.5 text-emerald-400" />
            +18.4%
          </span>
        </div>

        <div className="mb-3">
          <div className="text-3xl lg:text-4xl font-extrabold text-white tracking-tight drop-shadow-sm font-mono">
            {formatINR(recoveredRupees)}
          </div>
          <p className="text-xs text-slate-400 font-medium mt-1">
            Directly saved from failed Razorpay checkouts
          </p>
        </div>

        {/* Visual Progress Bar */}
        <div className="space-y-1.5 pt-2">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-slate-400">Recovery Efficiency</span>
            <span className="text-emerald-400 font-bold">
              {metrics.recovery_rate_pct}%
            </span>
          </div>
          <div className="w-full h-2 bg-slate-800/80 rounded-full overflow-hidden p-0.5 border border-slate-700/50">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-400 rounded-full transition-all duration-700 shadow-sm shadow-emerald-400"
              style={{ width: `${Math.max(metrics.recovery_rate_pct, 5)}%` }}
            />
          </div>
        </div>
      </div>

      {/* ── CARD 2: REVENUE AT RISK ────────────────────────────────────────── */}
      <div className="relative overflow-hidden p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl shadow-xl group transition-all duration-300 hover:border-rose-500/40">
        <div className="absolute -right-10 -top-10 w-32 h-32 bg-rose-500/10 rounded-full blur-3xl group-hover:bg-rose-500/15 transition-all" />

        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-rose-400 font-mono">
                Revenue At Risk
              </span>
              <p className="text-[11px] text-slate-400 font-medium">
                Failed Checkouts
              </p>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs font-medium font-mono">
            {metrics.total_failed} Events
          </span>
        </div>

        <div className="mb-3">
          <div className="text-3xl font-bold text-white tracking-tight font-mono">
            {formatINR(atRiskRupees)}
          </div>
          <p className="text-xs text-slate-400 font-medium mt-1">
            Total intercept value across webhooks
          </p>
        </div>

        <div className="flex items-center justify-between text-xs font-mono pt-2 border-t border-slate-800/60">
          <span className="text-slate-400">Recovered Tx Count</span>
          <span className="text-emerald-400 font-semibold">
            {metrics.total_recovered} / {metrics.total_failed}
          </span>
        </div>
      </div>

      {/* ── CARD 3: RECOVERY RATE & AI EFFICIENCY ───────────────────────────── */}
      <div className="relative overflow-hidden p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl shadow-xl group transition-all duration-300 hover:border-cyan-500/40">
        <div className="absolute -right-10 -top-10 w-32 h-32 bg-cyan-500/10 rounded-full blur-3xl group-hover:bg-cyan-500/15 transition-all" />

        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-400 font-mono">
                Recovery Speed
              </span>
              <p className="text-[11px] text-slate-400 font-medium">
                Automated Latency
              </p>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-xs font-medium font-mono">
            &lt; 850ms
          </span>
        </div>

        <div className="mb-3">
          <div className="text-3xl font-bold text-white tracking-tight font-mono flex items-baseline gap-2">
            {metrics.recovery_rate_pct}%
            <span className="text-xs text-slate-400 font-sans font-normal">
              Success Rate
            </span>
          </div>
          <p className="text-xs text-slate-400 font-medium mt-1">
            Gemini 2.5 Flash diagnosis + action link
          </p>
        </div>

        <div className="flex items-center justify-between text-xs font-mono pt-2 border-t border-slate-800/60">
          <span className="text-slate-400">Avg LLM Confidence</span>
          <span className="text-cyan-400 font-semibold">91.8%</span>
        </div>
      </div>

      {/* ── CARD 4: POLICY GATE GUARDRAILS ──────────────────────────────────── */}
      <div className="relative overflow-hidden p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl shadow-xl group transition-all duration-300 hover:border-purple-500/40">
        <div className="absolute -right-10 -top-10 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl group-hover:bg-purple-500/15 transition-all" />

        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-2xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-purple-400 font-mono">
                Policy Shield
              </span>
              <p className="text-[11px] text-slate-400 font-medium">
                Deterministic Gate
              </p>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs font-medium font-mono">
            Deterministic
          </span>
        </div>

        <div className="mb-3">
          <div className="text-3xl font-bold text-white tracking-tight font-mono">
            {metrics.blocked_by_policy_count}
          </div>
          <p className="text-xs text-slate-400 font-medium mt-1">
            Blocked unsafe / fraud interventions
          </p>
        </div>

        <div className="flex items-center justify-between text-xs font-mono pt-2 border-t border-slate-800/60">
          <span className="text-slate-400">Escalated to Human</span>
          <span className="text-purple-400 font-semibold">
            {metrics.escalated_count} Tx
          </span>
        </div>
      </div>
    </div>
  );
}
