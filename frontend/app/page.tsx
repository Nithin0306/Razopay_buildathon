"use client";

import { useEffect, useState } from "react";
import { fetchAuditLog, fetchMetrics } from "@/lib/api";
import { AuditLogEntry, MetricsResponse } from "@/types";
import Sidebar from "@/app/components/Sidebar";
import Header from "@/app/components/Header";
import HeroProfitCards from "@/app/components/HeroProfitCards";
import RevenueChart from "@/app/components/RevenueChart";
import SimulatorPanel from "@/app/components/SimulatorPanel";
import AuditLogTable from "@/app/components/AuditLogTable";
import PolicyRulesCard from "@/app/components/PolicyRulesCard";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [metrics, setMetrics] = useState<MetricsResponse>({
    total_failed: 28,
    total_recovered: 14,
    recovery_rate_pct: 50.0,
    total_amount_at_risk_paise: 8450000,
    total_amount_recovered_paise: 4225000,
    escalated_count: 5,
    blocked_by_policy_count: 4,
  });
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [totalLogs, setTotalLogs] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [limit] = useState<number>(20);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const [mRes, aRes] = await Promise.all([
        fetchMetrics(),
        fetchAuditLog(page, limit),
      ]);
      setMetrics(mRes);
      setAuditLogs(aRes.data);
      setTotalLogs(aRes.total);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Dashboard refresh error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
    // Auto-refresh every 6 seconds for live webhook updates
    const interval = setInterval(() => {
      loadDashboardData();
    }, 6000);
    return () => clearInterval(interval);
  }, [page, limit]);

  return (
    <div className="flex min-h-screen bg-[#070A0F] text-slate-100 font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        metricsRecoveredRate={metrics.recovery_rate_pct}
      />

      {/* Main Content Workspace */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          onRefresh={loadDashboardData}
          isLoading={isLoading}
          lastUpdated={lastUpdated}
        />

        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto space-y-8">
          {/* ── TAB 1: OVERVIEW DASHBOARD ───────────────────────────────────── */}
          {activeTab === "overview" && (
            <>
              {/* Emotional Profit Connect Hero Row */}
              <HeroProfitCards metrics={metrics} />

              {/* Revenue Recovery vs At-Risk Timeline Chart */}
              <RevenueChart />

              {/* Judge Webhook Simulator Control Panel */}
              <SimulatorPanel onSuccess={loadDashboardData} />

              {/* Deterministic Safety Policy Rules */}
              <PolicyRulesCard />

              {/* Real-Time Audit Log Table */}
              <AuditLogTable
                logs={auditLogs}
                total={totalLogs}
                page={page}
                limit={limit}
                onPageChange={setPage}
                isLoading={isLoading}
              />
            </>
          )}

          {/* ── TAB 2: AUDIT LOG STREAM ─────────────────────────────────────── */}
          {activeTab === "audit" && (
            <>
              <div className="mb-2">
                <h2 className="text-xl font-bold text-white tracking-tight">
                  Autonomous LLM Audit Trail & Reasoning Stream
                </h2>
                <p className="text-xs text-slate-400 font-mono">
                  Full step-by-step diagnostic breakdown from Gemini 2.5 Flash & Razorpay API executions
                </p>
              </div>
              <AuditLogTable
                logs={auditLogs}
                total={totalLogs}
                page={page}
                limit={limit}
                onPageChange={setPage}
                isLoading={isLoading}
              />
            </>
          )}

          {/* ── TAB 3: WEBHOOK SIMULATOR ────────────────────────────────────── */}
          {activeTab === "simulator" && (
            <>
              <div className="mb-2">
                <h2 className="text-xl font-bold text-white tracking-tight">
                  Razorpay Webhook Event Simulator & Test Suite
                </h2>
                <p className="text-xs text-slate-400 font-mono">
                  Trigger failure webhooks on demand to watch the closed-loop recovery agent execute
                </p>
              </div>
              <SimulatorPanel onSuccess={loadDashboardData} />
              <AuditLogTable
                logs={auditLogs}
                total={totalLogs}
                page={page}
                limit={limit}
                onPageChange={setPage}
                isLoading={isLoading}
              />
            </>
          )}

          {/* ── TAB 4: POLICY GUARDRAILS ───────────────────────────────────── */}
          {activeTab === "policy" && (
            <>
              <div className="mb-2">
                <h2 className="text-xl font-bold text-white tracking-tight">
                  Deterministic Safety Policy Gate Rules
                </h2>
                <p className="text-xs text-slate-400 font-mono">
                  Hardcoded business constraints enforcing regulatory compliance and fraud prevention
                </p>
              </div>
              <PolicyRulesCard />
            </>
          )}
        </main>
      </div>
    </div>
  );
}
