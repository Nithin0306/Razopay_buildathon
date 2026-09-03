"use client";

import { Bell, RefreshCw, ShieldCheck, Zap } from "lucide-react";

interface HeaderProps {
  onRefresh: () => void;
  isLoading: boolean;
  lastUpdated: Date | null;
}

export default function Header({
  onRefresh,
  isLoading,
  lastUpdated,
}: HeaderProps) {
  return (
    <header className="h-16 border-b border-slate-800/60 bg-[#0B0F17]/60 backdrop-blur-xl px-6 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
            AI Revenue Recovery Command Center
          </h2>
          <p className="text-xs text-slate-400 font-mono">
            Autonomous Razorpay Payment Interception & Policy Gate Engine
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Live Webhook Status Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium font-mono shadow-sm shadow-emerald-500/5">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span>Webhook Engine Active</span>
        </div>

        {/* Deterministic Guardrails Pill */}
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-xs font-medium font-mono">
          <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
          <span>Policy Gate Active</span>
        </div>

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition-all active:scale-95 disabled:opacity-50"
          title="Refresh Metrics"
        >
          <RefreshCw
            className={`w-4 h-4 ${isLoading ? "animate-spin text-emerald-400" : ""}`}
          />
        </button>

        {/* Notification indicator */}
        <div className="relative p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-emerald-500" />
        </div>
      </div>
    </header>
  );
}
