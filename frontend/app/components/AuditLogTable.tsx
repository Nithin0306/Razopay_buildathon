"use client";

import { useState } from "react";
import { AuditLogEntry } from "@/types";
import {
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Filter,
  Search,
  ShieldAlert,
  ShieldCheck,
  User,
} from "lucide-react";

interface AuditLogTableProps {
  logs: AuditLogEntry[];
  total: number;
  page: number;
  limit: number;
  onPageChange: (newPage: number) => void;
  isLoading: boolean;
}

export default function AuditLogTable({
  logs,
  total,
  page,
  limit,
  onPageChange,
  isLoading,
}: AuditLogTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  // Filter logs by search term and status filter tab
  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      !searchTerm ||
      log.razorpay_entity_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.customer_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.error_reason?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.agent_diagnosis?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "recovered" && log.amount_recovered_paise > 0) ||
      (statusFilter === "recovering" &&
        log.policy_gate_status === "passed" &&
        log.amount_recovered_paise === 0) ||
      (statusFilter === "blocked" && log.policy_gate_status !== "passed");

    return matchesSearch && matchesStatus;
  });

  const getPolicyBadge = (status: string) => {
    switch (status) {
      case "passed":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium font-mono">
            <ShieldCheck className="w-3.5 h-3.5" /> Passed
          </span>
        );
      case "blocked_manual_review":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-300 text-xs font-medium font-mono">
            <ShieldAlert className="w-3.5 h-3.5 text-purple-400" /> Fraud Block
          </span>
        );
      case "blocked_intervention_cap":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-medium font-mono">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Cap Block
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-medium font-mono">
            <ShieldAlert className="w-3.5 h-3.5" /> {status}
          </span>
        );
    }
  };

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl shadow-xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            Live AI Audit Stream & Decision Engine
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-mono border border-emerald-500/30">
              Audit Trail
            </span>
          </h3>
          <p className="text-xs text-slate-400 font-mono">
            Step-by-step diagnostic breakdown, Gemini LLM confidence, & policy gate log
          </p>
        </div>

        {/* Search & Filter Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search Entity ID, Customer..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-4 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-emerald-500/50 w-48 lg:w-60 font-mono"
            />
          </div>

          <div className="flex items-center p-1 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono">
            <button
              onClick={() => setStatusFilter("all")}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                statusFilter === "all"
                  ? "bg-slate-800 text-white font-semibold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              All ({total})
            </button>
            <button
              onClick={() => setStatusFilter("recovered")}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                statusFilter === "recovered"
                  ? "bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Recovered
            </button>
            <button
              onClick={() => setStatusFilter("blocked")}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                statusFilter === "blocked"
                  ? "bg-purple-500/20 text-purple-300 font-semibold border border-purple-500/30"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Policy Blocked
            </button>
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="overflow-x-auto rounded-2xl border border-slate-800/80">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950 text-slate-400 font-mono uppercase tracking-wider text-[10px] border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4">Razorpay Entity</th>
              <th className="py-3 px-4">Amount & Status</th>
              <th className="py-3 px-4">AI Agent Diagnosis</th>
              <th className="py-3 px-4">Confidence</th>
              <th className="py-3 px-4">Policy Gate</th>
              <th className="py-3 px-4">Recovery Action</th>
              <th className="py-3 px-4 text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {isLoading ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-slate-400">
                  Fetching live audit log records...
                </td>
              </tr>
            ) : filteredLogs.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-8 text-center text-slate-400">
                  No audit log entries match your filter.
                </td>
              </tr>
            ) : (
              filteredLogs.map((log) => {
                const isExpanded = expandedLogId === log.log_id;
                const isRecovered = log.amount_recovered_paise > 0;
                return (
                  <tr
                    key={log.log_id}
                    className="hover:bg-slate-800/30 transition-colors group"
                  >
                    {/* Timestamp */}
                    <td className="py-3.5 px-4 text-slate-400 whitespace-nowrap">
                      {log.created_at
                        ? new Date(log.created_at).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit",
                          })
                        : "Just now"}
                    </td>

                    {/* Razorpay Entity & Customer */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <div className="font-semibold text-white">
                        {log.razorpay_entity_id}
                      </div>
                      <div className="text-[11px] text-slate-400 flex items-center gap-1">
                        <User className="w-3 h-3 text-slate-400" />
                        {log.customer_email || log.customer_id || "Anonymous"}
                      </div>
                    </td>

                    {/* Amount & Status */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <div className="font-bold text-white">
                        ₹{(log.amount_paise / 100).toLocaleString("en-IN")}
                      </div>
                      {isRecovered ? (
                        <span className="text-[10px] text-emerald-400 font-semibold flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" /> Recovered ₹
                          {(log.amount_recovered_paise / 100).toLocaleString(
                            "en-IN"
                          )}
                        </span>
                      ) : (
                        <span className="text-[10px] text-rose-400">
                          {log.error_reason || "failed"}
                        </span>
                      )}
                    </td>

                    {/* AI Agent Diagnosis */}
                    <td className="py-3.5 px-4 max-w-xs font-sans text-slate-300">
                      <p className="line-clamp-2 leading-relaxed text-xs">
                        {log.agent_diagnosis || "Analyzing error root cause..."}
                      </p>
                      <span className="text-[10px] font-mono text-slate-400">
                        Category:{" "}
                        <strong className="text-slate-300">
                          {log.root_cause_category || "unknown"}
                        </strong>
                      </span>
                    </td>

                    {/* Confidence Score */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-emerald-400">
                          {((log.confidence_score || 0.85) * 100).toFixed(0)}%
                        </span>
                        <div className="w-12 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-emerald-400 rounded-full"
                            style={{
                              width: `${(log.confidence_score || 0.85) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    </td>

                    {/* Policy Gate */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      {getPolicyBadge(log.policy_gate_status)}
                    </td>

                    {/* Action Taken */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <div className="text-slate-200 font-medium">
                        {log.final_action || log.suggested_action}
                      </div>
                      {log.recovery_link_url && (
                        <a
                          href={log.recovery_link_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[10px] text-emerald-400 hover:underline inline-flex items-center gap-0.5 font-mono"
                        >
                          View Link <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      )}
                    </td>

                    {/* Expand Detail Button */}
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <button
                        onClick={() =>
                          setExpandedLogId(
                            isExpanded ? null : log.log_id
                          )
                        }
                        className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-colors"
                      >
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-800/60 text-xs font-mono text-slate-400">
        <span>
          Showing Page {page} of {totalPages} ({total} Total Logs)
        </span>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onPageChange(Math.max(1, page - 1))}
            disabled={page <= 1}
            className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 hover:text-white disabled:opacity-40"
          >
            Previous
          </button>
          <button
            onClick={() => onPageChange(Math.min(totalPages, page + 1))}
            disabled={page >= totalPages}
            className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 hover:text-white disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
