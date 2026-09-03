"use client";

import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// Mock 7-day visual dataset showing revenue growth & recovery progression
const CHART_DATA = [
  { day: "Mon", atRisk: 120000, recovered: 45000, txFailed: 4, txRecovered: 2 },
  { day: "Tue", atRisk: 180000, recovered: 90000, txFailed: 6, txRecovered: 3 },
  { day: "Wed", atRisk: 250000, recovered: 180000, txFailed: 8, txRecovered: 5 },
  { day: "Thu", atRisk: 310000, recovered: 240000, txFailed: 10, txRecovered: 7 },
  { day: "Fri", atRisk: 420000, recovered: 350000, txFailed: 14, txRecovered: 11 },
  { day: "Sat", atRisk: 580000, recovered: 490000, txFailed: 18, txRecovered: 15 },
  { day: "Sun", atRisk: 845000, recovered: 720000, txFailed: 28, txRecovered: 22 },
];

export default function RevenueChart() {
  const [isMounted, setIsMounted] = useState(false);
  const [viewMode, setViewMode] = useState<"revenue" | "volume">("revenue");

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const formatCurrencyShort = (val: number) => {
    if (val >= 100000) return `₹${(val / 100000).toFixed(1)}L`;
    if (val >= 1000) return `₹${(val / 1000).toFixed(0)}k`;
    return `₹${val}`;
  };

  return (
    <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl shadow-xl mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            Revenue Recovery & Profit Progression
          </h3>
          <p className="text-xs text-slate-400 font-mono">
            Cumulative Revenue Saved vs At-Risk Failed Checkout Volume
          </p>
        </div>

        {/* View Toggle */}
        <div className="flex items-center p-1 rounded-xl bg-slate-950 border border-slate-800 self-start sm:self-auto text-xs font-mono">
          <button
            onClick={() => setViewMode("revenue")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              viewMode === "revenue"
                ? "bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Rupees Saved (₹)
          </button>
          <button
            onClick={() => setViewMode("volume")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              viewMode === "volume"
                ? "bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Transaction Count
          </button>
        </div>
      </div>

      {/* Recharts Area Chart */}
      <div className="h-72 w-full">
        {isMounted ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={CHART_DATA}
              margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
            >
              <defs>
                <linearGradient id="gradientRecovered" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="gradientAtRisk" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#F43F5E" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#F43F5E" stopOpacity={0.0} />
                </linearGradient>
              </defs>

              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#1E293B"
                vertical={false}
              />
              <XAxis
                dataKey="day"
                stroke="#64748B"
                fontSize={12}
                tickLine={false}
                axisLine={{ stroke: "#1E293B" }}
              />
              <YAxis
                stroke="#64748B"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) =>
                  viewMode === "revenue" ? formatCurrencyShort(v) : v
                }
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0B0F17",
                  borderColor: "#334155",
                  borderRadius: "16px",
                  fontSize: "12px",
                  boxShadow: "0 20px 25px -5px rgba(0,0,0,0.5)",
                }}
                labelStyle={{ color: "#F8FAFC", fontWeight: "bold" }}
                formatter={(val: any, name: any) => [
                  viewMode === "revenue"
                    ? `₹${Number(val).toLocaleString("en-IN")}`
                    : `${val} Tx`,
                  name === "recovered" || name === "txRecovered"
                    ? "Profit Saved"
                    : "At Risk",
                ]}
              />

              <Area
                type="monotone"
                dataKey={viewMode === "revenue" ? "atRisk" : "txFailed"}
                name={viewMode === "revenue" ? "atRisk" : "txFailed"}
                stroke="#F43F5E"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#gradientAtRisk)"
              />
              <Area
                type="monotone"
                dataKey={viewMode === "revenue" ? "recovered" : "txRecovered"}
                name={viewMode === "revenue" ? "recovered" : "txRecovered"}
                stroke="#10B981"
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#gradientRecovered)"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full w-full flex items-center justify-center text-slate-400 font-mono text-sm">
            Loading Profit Chart...
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-slate-800/60 text-xs font-mono">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500" />
          <span className="text-slate-300">Recovered Revenue (Profit Saved)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-rose-500 shadow-sm shadow-rose-500" />
          <span className="text-slate-300">Initial At-Risk Revenue</span>
        </div>
      </div>
    </div>
  );
}
