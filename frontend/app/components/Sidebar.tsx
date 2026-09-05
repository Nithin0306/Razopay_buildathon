"use client";

import {
  Activity,
  Bot,
  CheckCircle2,
  DollarSign,
  LayoutDashboard,
  Play,
  ShieldCheck,
} from "lucide-react";
import Image from "next/image";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  metricsRecoveredRate: number;
}

export default function Sidebar({
  activeTab,
  setActiveTab,
  metricsRecoveredRate,
}: SidebarProps) {
  const navItems = [
    { id: "overview", label: "Dashboard", icon: LayoutDashboard },
    { id: "audit", label: "Live AI Audit Stream", icon: Activity },
    { id: "simulator", label: "Webhook Simulator", icon: Play },
    { id: "policy", label: "Policy Guardrails", icon: ShieldCheck },
  ];

  return (
    <aside className="w-64 bg-[#0B0F17]/90 backdrop-blur-2xl border-r border-slate-800/60 flex flex-col justify-between p-5 min-h-screen text-slate-300 select-none">
      <div>
        {/* Brand Logo */}
        <div className="flex items-center gap-3 px-2 py-3 mb-8">
          <div className="w-10 h-10 rounded-xl overflow-hidden bg-white shadow-lg shadow-emerald-500/20 ring-1 ring-white/20 shrink-0">
            <Image
              src="/logo.png"
              alt="Razorpay"
              width={40}
              height={40}
              className="w-full h-full object-cover"
              priority
            />
          </div>
          <div>
            <h1 className="font-bold text-white tracking-tight text-base leading-tight">
              Razopay <span className="text-emerald-400 font-extrabold">AI</span>
            </h1>
            <p className="text-[11px] text-slate-400 font-mono tracking-wide">
              Revenue Recovery Agent
            </p>
          </div>
        </div>

        {/* Navigation Section */}
        <nav className="space-y-1.5">
          <p className="px-3 text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-2 font-mono">
            Navigation
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 ${
                  isActive
                    ? "bg-gradient-to-r from-emerald-500/20 to-teal-500/10 text-emerald-300 border border-emerald-500/30 shadow-lg shadow-emerald-500/5 font-semibold"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                }`}
              >
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? "text-emerald-400" : "text-slate-400"
                  }`}
                />
                <span>{item.label}</span>
                {isActive && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Agent Engine Status Box */}
      <div className="space-y-4">
        <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800/80 relative overflow-hidden group">
          <div className="absolute -right-4 -bottom-4 w-20 h-20 bg-emerald-500/10 rounded-full blur-xl group-hover:bg-emerald-500/20 transition-all" />
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-semibold text-white">
                LangGraph Agent
              </span>
            </div>
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-mono mb-2.5">
            Model: Gemini 2.5 Flash
          </p>
          <div className="space-y-1">
            <div className="flex justify-between text-[11px] font-mono">
              <span className="text-slate-400">Recovery Rate</span>
              <span className="text-emerald-400 font-semibold">
                {metricsRecoveredRate.toFixed(1)}%
              </span>
            </div>
            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-500"
                style={{ width: `${Math.min(metricsRecoveredRate, 100)}%` }}
              />
            </div>
          </div>
        </div>

        <div className="px-2 flex items-center justify-between text-[11px] text-slate-400 font-mono">
          <span>Razorpay Track 3</span>
          <span className="text-slate-400">v1.0.0</span>
        </div>
      </div>
    </aside>
  );
}
