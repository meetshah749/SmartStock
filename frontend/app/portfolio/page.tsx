"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  PieChart as PieChartIcon,
  Layers,
  ArrowUpRight,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";
import { useAuth } from "@/lib/auth";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { TradeModal } from "@/components/TradeModal";

interface HoldingItem {
  id: string;
  symbol: string;
  company_name: string;
  quantity: number;
  avg_buy_price_rupees: number;
  total_invested_rupees: number;
  current_price_rupees: number;
  current_value_rupees: number;
  unrealized_pnl_rupees: number;
  unrealized_pnl_percent: number;
}

interface PortfolioSummary {
  total_invested_rupees: number;
  current_value_rupees: number;
  unrealized_pnl_rupees: number;
  unrealized_pnl_percent: number;
  realized_pnl_rupees: number;
  wallet_balance_rupees: number;
  holdings_count: number;
}

const COLORS = ["#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", "#06B6D4", "#EC4899"];

function PortfolioContent() {
  const { accessToken } = useAuth();
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [holdings, setHoldings] = useState<HoldingItem[]>([]);
  const [loading, setLoading] = useState(true);

  const [activeTrade, setActiveTrade] = useState<{
    symbol: string;
    companyName: string;
    price: number;
    currency: string;
    orderType: "buy" | "sell";
  } | null>(null);

  const fetchData = () => {
    if (!accessToken) return;
    setLoading(true);

    Promise.all([
      fetch("http://localhost:8000/api/v1/portfolio", {
        headers: { Authorization: `Bearer ${accessToken}` },
      }).then((res) => (res.ok ? res.json() : null)),
      fetch("http://localhost:8000/api/v1/portfolio/holdings", {
        headers: { Authorization: `Bearer ${accessToken}` },
      }).then((res) => (res.ok ? res.json() : [])),
    ])
      .then(([sumData, holdData]) => {
        setSummary(sumData);
        setHoldings(holdData);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, [accessToken]);

  const pieData = holdings.map((h) => ({
    name: h.symbol,
    value: h.current_value_rupees,
  }));

  return (
    <div className="space-y-8">
      
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-txt-primary tracking-tight">Virtual Portfolio & Net Worth</h1>
          <p className="text-xs text-txt-muted mt-1">
            Track active positions, unrealized P&L, realized returns, and asset distribution in real-time.
          </p>
        </div>

        <button
          onClick={fetchData}
          className="px-4 py-2 rounded-xl bg-surface-card border border-border text-txt-secondary hover:text-txt-primary text-xs font-bold flex items-center gap-2"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Quotes
        </button>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 font-numeric">
        
        <div className="p-6 rounded-2xl bg-surface-card border border-border flex flex-col gap-1 shadow-lg">
          <span className="text-xs font-semibold text-txt-muted uppercase">Portfolio Net Worth</span>
          <div className="text-2xl font-extrabold text-txt-primary">
            ₹{((summary?.current_value_rupees || 0) + (summary?.wallet_balance_rupees || 500)).toFixed(2)}
          </div>
          <span className="text-[10px] text-txt-muted">Includes ₹{summary?.wallet_balance_rupees.toFixed(2)} Cash</span>
        </div>

        <div className="p-6 rounded-2xl bg-surface-card border border-border flex flex-col gap-1 shadow-lg">
          <span className="text-xs font-semibold text-txt-muted uppercase">Total Invested</span>
          <div className="text-2xl font-extrabold text-brand-bright">
            ₹{(summary?.total_invested_rupees || 0).toFixed(2)}
          </div>
          <span className="text-[10px] text-txt-muted">{summary?.holdings_count || 0} Active Positions</span>
        </div>

        <div className="p-6 rounded-2xl bg-surface-card border border-border flex flex-col gap-1 shadow-lg">
          <span className="text-xs font-semibold text-txt-muted uppercase">Unrealized P&L</span>
          <div
            className={`text-2xl font-extrabold flex items-center gap-1 ${
              (summary?.unrealized_pnl_rupees || 0) >= 0
                ? "text-financial-profit"
                : "text-financial-loss"
            }`}
          >
            {(summary?.unrealized_pnl_rupees || 0) >= 0 ? "+" : ""}
            ₹{(summary?.unrealized_pnl_rupees || 0).toFixed(2)}
            <span className="text-xs font-bold">
              ({summary?.unrealized_pnl_percent || 0}%)
            </span>
          </div>
          <span className="text-[10px] text-txt-muted">Live Market Gain/Loss</span>
        </div>

        <div className="p-6 rounded-2xl bg-surface-card border border-border flex flex-col gap-1 shadow-lg">
          <span className="text-xs font-semibold text-txt-muted uppercase">Realized Returns</span>
          <div
            className={`text-2xl font-extrabold ${
              (summary?.realized_pnl_rupees || 0) >= 0
                ? "text-financial-profit"
                : "text-financial-loss"
            }`}
          >
            {(summary?.realized_pnl_rupees || 0) >= 0 ? "+" : ""}
            ₹{(summary?.realized_pnl_rupees || 0).toFixed(2)}
          </div>
          <span className="text-[10px] text-txt-muted">Closed Trade Profits</span>
        </div>

      </div>

      {/* Main Grid: Allocation Chart & Holdings Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Holdings Table */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-surface-card border border-border space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-txt-primary flex items-center gap-2">
              <Layers className="w-5 h-5 text-brand-bright" /> Active Holdings
            </h2>
            <Link href="/stocks" className="text-xs font-semibold text-brand-bright hover:underline">
              Trade More Equities
            </Link>
          </div>

          {loading ? (
            <div className="py-8 text-center text-xs text-txt-muted animate-pulse">
              Loading active portfolio positions...
            </div>
          ) : holdings.length === 0 ? (
            <div className="py-12 text-center text-xs text-txt-muted space-y-3">
              <p>You do not have any active stock holdings in your virtual portfolio.</p>
              <Link
                href="/stocks"
                className="inline-block px-5 py-2 rounded-xl bg-brand-primary text-white font-bold text-xs"
              >
                Browse Equities & Place Virtual Order
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-numeric">
                <thead>
                  <tr className="border-b border-border text-txt-muted text-[11px] uppercase">
                    <th className="pb-3 font-semibold">Stock</th>
                    <th className="pb-3 font-semibold">Qty</th>
                    <th className="pb-3 font-semibold">Avg Buy</th>
                    <th className="pb-3 font-semibold">Current</th>
                    <th className="pb-3 font-semibold">Unrealized P&L</th>
                    <th className="pb-3 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50">
                  {holdings.map((h) => {
                    const isProfit = h.unrealized_pnl_rupees >= 0;
                    return (
                      <tr key={h.id} className="hover:bg-surface-elevated transition-colors">
                        <td className="py-3.5">
                          <Link href={`/stocks/${h.symbol}`} className="font-extrabold text-txt-primary hover:text-brand-bright">
                            {h.symbol}
                          </Link>
                          <span className="block text-[10px] text-txt-muted truncate max-w-[120px]">
                            {h.company_name}
                          </span>
                        </td>
                        <td className="py-3.5 font-bold text-txt-primary">{h.quantity}</td>
                        <td className="py-3.5 text-txt-secondary">₹{h.avg_buy_price_rupees.toFixed(2)}</td>
                        <td className="py-3.5 font-bold text-txt-primary">₹{h.current_price_rupees.toFixed(2)}</td>
                        <td className="py-3.5">
                          <span
                            className={`font-bold ${
                              isProfit ? "text-financial-profit" : "text-financial-loss"
                            }`}
                          >
                            {isProfit ? "+" : ""}₹{h.unrealized_pnl_rupees.toFixed(2)} ({h.unrealized_pnl_percent}%)
                          </span>
                        </td>
                        <td className="py-3.5 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() =>
                                setActiveTrade({
                                  symbol: h.symbol,
                                  companyName: h.company_name,
                                  price: h.current_price_rupees,
                                  currency: "INR",
                                  orderType: "buy",
                                })
                              }
                              className="px-2.5 py-1 rounded bg-financial-profit/20 text-financial-profit font-bold text-[10px]"
                            >
                              Buy
                            </button>
                            <button
                              onClick={() =>
                                setActiveTrade({
                                  symbol: h.symbol,
                                  companyName: h.company_name,
                                  price: h.current_price_rupees,
                                  currency: "INR",
                                  orderType: "sell",
                                })
                              }
                              className="px-2.5 py-1 rounded bg-financial-loss/20 text-financial-loss font-bold text-[10px]"
                            >
                              Sell
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Allocation Doughnut Chart */}
        <div className="p-6 rounded-2xl bg-surface-card border border-border space-y-4 shadow-xl flex flex-col justify-between">
          <h2 className="text-base font-bold text-txt-primary flex items-center gap-2">
            <PieChartIcon className="w-5 h-5 text-ai-light" /> Asset Allocation
          </h2>

          {pieData.length > 0 ? (
            <div className="w-full h-56 relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#151F35",
                      borderColor: "#263552",
                      borderRadius: "0.75rem",
                      fontSize: "12px",
                      color: "#F8FAFC",
                    }}
                    formatter={(val: any) => [`₹${val.toFixed(2)}`, "Asset Value"]}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="py-12 text-center text-xs text-txt-muted">
              Place virtual trades to view asset allocation charts.
            </div>
          )}

          <div className="p-3 rounded-lg bg-surface-elevated border border-border text-[11px] text-txt-muted leading-relaxed">
            Portfolio balances are simulated for education and virtual trading strategy testing.
          </div>
        </div>

      </div>

      {/* Trade Modal Trigger */}
      {activeTrade && (
        <TradeModal
          symbol={activeTrade.symbol}
          companyName={activeTrade.companyName}
          price={activeTrade.price}
          currency={activeTrade.currency}
          orderType={activeTrade.orderType}
          onClose={() => setActiveTrade(null)}
          onSuccess={fetchData}
        />
      )}

    </div>
  );
}

export default function PortfolioPage() {
  return (
    <ProtectedRoute>
      <PortfolioContent />
    </ProtectedRoute>
  );
}
