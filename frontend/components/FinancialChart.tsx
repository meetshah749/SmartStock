"use client";

import React, { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  LineChart,
  Line,
  BarChart,
  Bar,
} from "recharts";
import { Clock, TrendingUp, BarChart2, Activity } from "lucide-react";

interface PricePoint {
  timestamp: string;
  time_label: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface FinancialChartProps {
  symbol: string;
  currency?: string;
}

export function FinancialChart({ symbol, currency = "INR" }: FinancialChartProps) {
  const [timeframe, setTimeframe] = useState("1M");
  const [data, setData] = useState<PricePoint[]>([]);
  const [indicators, setIndicators] = useState<any>(null);
  const [showRsi, setShowRsi] = useState(false);
  const [showMacd, setShowMacd] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    // Fetch prices
    fetch(`http://localhost:8000/api/v1/stocks/${symbol}/prices?timeframe=${timeframe}`)
      .then((res) => (res.ok ? res.json() : []))
      .then((prices) => {
        setData(prices);
      })
      .catch(() => {})
      .finally(() => setLoading(false));

    // Fetch indicators
    fetch(`http://localhost:8000/api/v1/stocks/${symbol}/indicators?timeframe=${timeframe}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((indData) => {
        if (indData) setIndicators(indData.indicators);
      })
      .catch(() => {});
  }, [symbol, timeframe]);

  const isPositive =
    data.length >= 2 ? data[data.length - 1].close >= data[0].close : true;

  const chartColor = isPositive ? "#10B981" : "#EF4444";

  // Merge price data with indicators for rendering
  const mergedData = data.map((pt, idx) => ({
    ...pt,
    sma20: indicators?.sma20?.[idx] || null,
    rsi: indicators?.rsi14?.[idx] || null,
    macdHist: indicators?.macd?.histogram?.[idx] || null,
  }));

  return (
    <div className="w-full rounded-2xl bg-surface-card border border-border p-6 flex flex-col gap-6 shadow-xl">
      
      {/* Top Chart Controls Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-border/50 pb-4">
        
        {/* Timeframe Buttons */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-surface-main border border-border">
          {["1D", "1W", "1M", "3M", "6M", "1Y", "5Y"].map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                timeframe === tf
                  ? "bg-brand-primary text-white shadow"
                  : "text-txt-muted hover:text-txt-primary"
              }`}
            >
              {tf}
            </button>
          ))}
        </div>

        {/* Technical Indicators Toggles & Status Pill */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowRsi(!showRsi)}
            className={`px-3 py-1 rounded-lg text-xs font-bold border transition-all ${
              showRsi
                ? "bg-ai-violet/20 text-ai-light border-ai-violet/40"
                : "bg-surface-elevated text-txt-muted border-border hover:text-txt-primary"
            }`}
          >
            RSI (14)
          </button>

          <button
            onClick={() => setShowMacd(!showMacd)}
            className={`px-3 py-1 rounded-lg text-xs font-bold border transition-all ${
              showMacd
                ? "bg-brand-primary/20 text-brand-bright border-brand-primary/40"
                : "bg-surface-elevated text-txt-muted border-border hover:text-txt-primary"
            }`}
          >
            MACD
          </button>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-warning/10 text-warning border border-warning/20 text-[10px] font-bold uppercase">
            <Clock className="w-3 h-3" />
            <span>DATA STATUS: DELAYED (15M)</span>
          </div>
        </div>

      </div>

      {/* Primary Price Area Chart */}
      <div className="w-full h-72 sm:h-80 relative">
        {loading ? (
          <div className="w-full h-full flex items-center justify-center text-xs text-txt-muted animate-pulse">
            Loading chart data...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={mergedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={chartColor} stopOpacity={0.4} />
                  <stop offset="95%" stopColor={chartColor} stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="time_label"
                stroke="#64748B"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                domain={["auto", "auto"]}
                stroke="#64748B"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                tickFormatter={(val) => `${currency === "INR" ? "₹" : "$"}${val}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#151F35",
                  borderColor: "#263552",
                  borderRadius: "0.75rem",
                  color: "#F8FAFC",
                  fontSize: "12px",
                }}
                formatter={(val: any) => [`${currency === "INR" ? "₹" : "$"}${val}`, "Close Price"]}
              />
              <Area
                type="monotone"
                dataKey="close"
                stroke={chartColor}
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#priceGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Optional RSI Indicator Sub-chart */}
      {showRsi && (
        <div className="w-full h-36 pt-4 border-t border-border/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-ai-light uppercase tracking-wider">RSI (14) Sub-chart</span>
            <span className="text-[11px] font-mono text-txt-muted">Overbought ≥ 70 | Oversold ≤ 30</span>
          </div>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={mergedData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <XAxis dataKey="time_label" hide />
              <YAxis domain={[0, 100]} stroke="#64748B" fontSize={10} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: "#151F35", borderColor: "#263552", color: "#A78BFA", fontSize: "11px" }}
              />
              <Line type="monotone" dataKey="rsi" stroke="#8B5CF6" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Optional MACD Indicator Sub-chart */}
      {showMacd && (
        <div className="w-full h-36 pt-4 border-t border-border/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-brand-bright uppercase tracking-wider">MACD Histogram Sub-chart</span>
            <span className="text-[11px] font-mono text-txt-muted">Signal Line Cross overs</span>
          </div>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={mergedData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <XAxis dataKey="time_label" hide />
              <YAxis stroke="#64748B" fontSize={10} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: "#151F35", borderColor: "#263552", color: "#60A5FA", fontSize: "11px" }}
              />
              <Bar dataKey="macdHist" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

    </div>
  );
}
