"use client";

import React, { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Area, AreaChart, CartesianGrid, ReferenceDot, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Activity, ArrowLeft, BrainCircuit, CheckCircle2, Clock3, Database, FlaskConical, Loader2, Play, ShieldAlert, TrendingDown, TrendingUp } from "lucide-react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuth } from "@/lib/auth";

type StrategyType = "golden_cross" | "rsi_momentum" | "macd_trend" | "conservative_trend" | "buy_hold" | "custom";
type Indicator = "SMA20" | "SMA50" | "SMA200" | "EMA20" | "EMA50" | "RSI" | "MACD" | "MACD_SIGNAL" | "BOLLINGER_UPPER" | "BOLLINGER_MIDDLE" | "BOLLINGER_LOWER" | "ATR" | "VOLUME";
type Operator = ">" | "<" | ">=" | "<=" | "crosses_above" | "crosses_below";
type ConditionForm = { left: Indicator; operator: Operator; right_indicator: Indicator | ""; right_value: string };
type RuleForm = { join: "AND" | "OR"; conditions: ConditionForm[] };

interface SearchStock { symbol: string; company_name: string; exchange: string; currency?: string; }
interface EquityPoint { date: string; timestamp: string; portfolio_value: number; buy_hold_value: number | null; benchmark_value: number | null; drawdown_pct: number; }
interface BacktestResult {
  backtest_id: string;
  symbol: string;
  strategy: { type: string; name?: string };
  strategy_summary: { name: string; entry: string | object; exit: string | object };
  assumptions: { initial_capital: number; transaction_cost_pct: number; slippage_pct: number; execution_model: string };
  metrics: Record<string, number | string | null>;
  trades: Array<{ trade_id: string; timestamp: string; action: "BUY" | "SELL"; execution_price: number; quantity: number; gross_value: number; transaction_cost: number; slippage_cost: number; realized_pnl: number | null; reason: string }>;
  equity_curve: EquityPoint[];
  drawdown_curve: Array<{ date: string; drawdown_pct: number }>;
  comparison: { strategy_return_pct: number; buy_hold_return_pct: number; outperformance_vs_buy_hold_pct_points: number; nifty50_return_pct: number | null; outperformance_vs_nifty50_pct_points: number | null; nifty50_unavailable_reason: string | null };
  strategy_comparison: Array<{ strategy: string; return_pct: number; max_drawdown_pct: number; sharpe_ratio: number | null; win_rate_pct: number | null; total_trades: number }>;
  data: { provider: string; source: string; status: string; frequency: string; candles: number; retrieved_at: string; requested_period: { start: string; end: string } };
  notice: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const indicatorOptions: Indicator[] = ["SMA20", "SMA50", "SMA200", "EMA20", "EMA50", "RSI", "MACD", "MACD_SIGNAL", "BOLLINGER_UPPER", "BOLLINGER_MIDDLE", "BOLLINGER_LOWER", "ATR", "VOLUME"];
const strategyNames: Record<StrategyType, string> = {
  golden_cross: "Golden Cross", rsi_momentum: "RSI Momentum", macd_trend: "MACD Trend", conservative_trend: "Conservative Trend", buy_hold: "Buy & Hold", custom: "Custom Strategy",
};
const emptyCondition = (): ConditionForm => ({ left: "SMA20", operator: "crosses_above", right_indicator: "SMA50", right_value: "" });
const today = new Date();
const yesterday = new Date(today.getTime() - 86400000).toISOString().slice(0, 10);
const threeYearsAgo = new Date(today.getTime() - 3 * 365 * 86400000).toISOString().slice(0, 10);

function errorMessage(payload: any): string {
  const detail = payload?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((e) => e?.msg || String(e)).join("; ");
  return "The backtest request failed. Check your inputs and try again.";
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="flex flex-col gap-2 text-xs font-semibold text-txt-secondary"><span>{label}</span>{children}</label>;
}

function ConditionEditor({ title, rule, onChange }: { title: string; rule: RuleForm; onChange: (rule: RuleForm) => void }) {
  const update = (index: number, patch: Partial<ConditionForm>) => onChange({
    ...rule,
    conditions: rule.conditions.map((condition, i) => i === index ? { ...condition, ...patch } : condition),
  });
  const inputClass = "min-w-0 rounded-lg border border-border bg-surface-main px-2.5 py-2 text-[11px] text-txt-primary outline-none focus:border-brand-primary";
  return (
    <div className="space-y-3 rounded-xl border border-border bg-surface-main/70 p-3">
      <div className="flex items-center justify-between"><h4 className="text-[10px] font-extrabold uppercase tracking-wider text-ai-light">{title} when</h4>{rule.conditions.length > 1 && <select value={rule.join} onChange={(e) => onChange({ ...rule, join: e.target.value as RuleForm["join"] })} className={inputClass}><option>AND</option><option>OR</option></select>}</div>
      {rule.conditions.map((condition, index) => (
        <div key={index} className="grid grid-cols-1 gap-2 sm:grid-cols-[1fr_1fr_1fr]">
          <select aria-label={`${title} condition indicator`} value={condition.left} onChange={(e) => update(index, { left: e.target.value as Indicator })} className={inputClass}>{indicatorOptions.map((item) => <option key={item}>{item}</option>)}</select>
          <select aria-label={`${title} condition operator`} value={condition.operator} onChange={(e) => update(index, { operator: e.target.value as Operator })} className={inputClass}><option value="crosses_above">crosses above</option><option value="crosses_below">crosses below</option><option value=">">&gt;</option><option value="<">&lt;</option><option value=">=">≥</option><option value="<=">≤</option></select>
          <div className="flex gap-1"><select aria-label={`${title} right-hand side type`} value={condition.right_indicator ? "indicator" : "value"} onChange={(e) => update(index, e.target.value === "indicator" ? { right_indicator: "SMA50", right_value: "" } : { right_indicator: "", right_value: "30" })} className={`${inputClass} w-24`}><option value="indicator">Indicator</option><option value="value">Value</option></select>{condition.right_indicator ? <select aria-label={`${title} right-hand indicator`} value={condition.right_indicator} onChange={(e) => update(index, { right_indicator: e.target.value as Indicator })} className={`${inputClass} flex-1`}>{indicatorOptions.map((item) => <option key={item}>{item}</option>)}</select> : <input aria-label={`${title} comparison value`} type="number" value={condition.right_value} onChange={(e) => update(index, { right_value: e.target.value })} className={`${inputClass} min-w-0 flex-1`} />}</div>
        </div>
      ))}
      {rule.conditions.length < 5 && <button type="button" onClick={() => onChange({ ...rule, conditions: [...rule.conditions, emptyCondition()] })} className="text-[10px] font-bold text-brand-bright hover:underline">+ Add condition</button>}
    </div>
  );
}

function BacktestingContent() {
  const { accessToken } = useAuth();
  const [query, setQuery] = useState("");
  const [matches, setMatches] = useState<SearchStock[]>([]);
  const [stock, setStock] = useState<SearchStock | null>(null);
  const [startDate, setStartDate] = useState(threeYearsAgo);
  const [endDate, setEndDate] = useState(yesterday);
  const [capital, setCapital] = useState("100000");
  const [strategyType, setStrategyType] = useState<StrategyType>("golden_cross");
  const [transactionCost, setTransactionCost] = useState("0.10");
  const [slippage, setSlippage] = useState("0.05");
  const [positionPct, setPositionPct] = useState("100");
  const [compareStrategies, setCompareStrategies] = useState(false);
  const [entry, setEntry] = useState<RuleForm>({ join: "AND", conditions: [emptyCondition()] });
  const [exitRule, setExitRule] = useState<RuleForm>({ join: "OR", conditions: [{ left: "SMA20", operator: "crosses_below", right_indicator: "SMA50", right_value: "" }] });
  const [running, setRunning] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [analysis, setAnalysis] = useState("");
  const [analysisMode, setAnalysisMode] = useState("");
  const [error, setError] = useState("");
  const [tradeFilter, setTradeFilter] = useState<"ALL" | "BUY" | "SELL">("ALL");
  const [selectedTrade, setSelectedTrade] = useState<BacktestResult["trades"][number] | null>(null);

  useEffect(() => {
    if (!query.trim() || !accessToken) { setMatches([]); return; }
    const timer = setTimeout(async () => {
      try {
        const response = await fetch(`${API_URL}/api/v1/stocks/search?q=${encodeURIComponent(query)}`);
        const items = response.ok ? await response.json() : [];
        setMatches(items.slice(0, 8));
      } catch { setMatches([]); }
    }, 250);
    return () => clearTimeout(timer);
  }, [query, accessToken]);

  useEffect(() => {
    if (!accessToken) return;
    fetch(`${API_URL}/api/v1/backtesting/runs`, { headers: { Authorization: `Bearer ${accessToken}` } })
      .then((response) => response.ok ? response.json() : [])
      .then((runs: Array<{ backtest_id: string }>) => {
        if (Array.isArray(runs) && runs.length > 0) {
          return fetch(`${API_URL}/api/v1/backtesting/runs/${runs[0].backtest_id}`, { headers: { Authorization: `Bearer ${accessToken}` } })
            .then((response) => response.ok ? response.json() : null)
            .then((latest) => { if (latest) setResult(latest as BacktestResult); });
        }
        return undefined;
      })
      .catch(() => {});
  }, [accessToken]);

  const equityData = useMemo(() => result?.equity_curve || [], [result]);
  const drawdownData = useMemo(() => result?.drawdown_curve || [], [result]);
  const visibleTrades = useMemo(() => (result?.trades || []).filter((trade) => tradeFilter === "ALL" || trade.action === tradeFilter), [result, tradeFilter]);
  const customPayload = () => ({
    type: "custom",
    name: "Custom Strategy",
    entry: { join: entry.join, conditions: entry.conditions.map((condition) => ({ left: condition.left, operator: condition.operator, ...(condition.right_indicator ? { right_indicator: condition.right_indicator } : { right_value: Number(condition.right_value) }) })) },
    exit: { join: exitRule.join, conditions: exitRule.conditions.map((condition) => ({ left: condition.left, operator: condition.operator, ...(condition.right_indicator ? { right_indicator: condition.right_indicator } : { right_value: Number(condition.right_value) }) })) },
  });

  const runBacktest = async (event: FormEvent) => {
    event.preventDefault();
    setError(""); setAnalysis(""); setAnalysisMode(""); setResult(null); setSelectedTrade(null);
    if (!accessToken) { setError("Please sign in to run and save a backtest."); return; }
    if (!stock) { setError("Search for and select a stock first."); return; }
    if (!startDate || !endDate || startDate >= endDate) { setError("Start date must be earlier than end date."); return; }
    if (new Date(`${endDate}T00:00:00`) >= new Date(new Date().toDateString())) { setError("Choose a completed historical end date (before today)."); return; }
    if (!Number.isFinite(Number(capital)) || Number(capital) < 1000) { setError("Initial capital must be at least ₹1,000."); return; }
    if (strategyType === "custom" && [...entry.conditions, ...exitRule.conditions].some((condition) => !condition.right_indicator && (!condition.right_value.trim() || !Number.isFinite(Number(condition.right_value))))) { setError("Enter a valid numeric value for each custom rule."); return; }

    setRunning(true);
    try {
      const response = await fetch(`${API_URL}/api/v1/backtesting/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({
          symbol: stock.symbol,
          exchange: ["NSE", "BSE"].includes(stock.exchange) ? stock.exchange : null,
          start_date: startDate,
          end_date: endDate,
          initial_capital: Number(capital),
          strategy: strategyType === "custom" ? customPayload() : { type: strategyType },
          transaction_cost_pct: Number(transactionCost),
          slippage_pct: Number(slippage),
          position_pct: Number(positionPct),
          compare_strategies: compareStrategies,
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(errorMessage(payload));
      setResult(payload as BacktestResult);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "The backtest failed. Please retry.");
    } finally { setRunning(false); }
  };

  const requestAnalysis = async () => {
    if (!result || !accessToken) return;
    setAnalyzing(true); setError("");
    try {
      const response = await fetch(`${API_URL}/api/v1/backtesting/analyze`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({ backtest_id: result.backtest_id }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(errorMessage(payload));
      setAnalysis(payload.analysis);
      setAnalysisMode(payload.mode || "");
    } catch (failure) { setError(failure instanceof Error ? failure.message : "AI analysis failed."); }
    finally { setAnalyzing(false); }
  };

  const money = (value: unknown) => typeof value === "number" ? `₹${value.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—";
  const metric = (key: string) => result?.metrics[key];

  return (
    <div className="space-y-7">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link href="/stocks" className="mb-3 inline-flex items-center gap-1 text-[11px] font-semibold text-txt-muted hover:text-brand-bright"><ArrowLeft className="h-3 w-3" /> Stock explorer</Link>
          <div className="flex items-center gap-2"><FlaskConical className="h-6 w-6 text-ai-light" /><h1 className="text-3xl font-extrabold tracking-tight text-txt-primary">SmartStock AI — Backtesting Lab</h1></div>
          <p className="mt-2 max-w-3xl text-sm text-txt-secondary">Test strategies against actual historical market data and understand how they performed.</p>
        </div>
        <span className="rounded-full border border-financial-profit/30 bg-financial-profit/10 px-3 py-1.5 text-[10px] font-bold text-financial-profit">Historical simulation · long-only</span>
      </div>

      <form onSubmit={runBacktest} className="space-y-6 rounded-2xl border border-border bg-surface-card p-5 shadow-xl sm:p-7">
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          <div className="relative">
            <Field label="1 · Select stock">
              <input value={stock ? `${stock.symbol} — ${stock.company_name}` : query} onChange={(e) => { setStock(null); setQuery(e.target.value); }} placeholder="Search TCS, HDFC Bank…" className="rounded-xl border border-border bg-surface-main px-3 py-3 text-xs text-txt-primary outline-none focus:border-brand-primary" />
            </Field>
            {!stock && matches.length > 0 && <div className="absolute z-30 mt-1 max-h-56 w-full overflow-auto rounded-xl border border-border bg-surface-card shadow-2xl">{matches.map((item) => <button type="button" key={`${item.symbol}-${item.exchange}`} onClick={() => { setStock(item); setQuery(""); setMatches([]); }} className="flex w-full items-start justify-between gap-2 border-b border-border/50 p-3 text-left hover:bg-surface-elevated"><span><strong className="block text-xs text-txt-primary">{item.symbol}</strong><span className="text-[10px] text-txt-muted">{item.company_name}</span></span><span className="text-[9px] font-bold text-brand-bright">{item.exchange}</span></button>)}</div>}
          </div>
          <Field label="2 · Historical period"><div className="grid grid-cols-2 gap-2"><input aria-label="Start date" type="date" value={startDate} max={yesterday} onChange={(e) => setStartDate(e.target.value)} className="min-w-0 rounded-xl border border-border bg-surface-main px-2 py-3 text-xs text-txt-primary" /><input aria-label="End date" type="date" value={endDate} max={yesterday} onChange={(e) => setEndDate(e.target.value)} className="min-w-0 rounded-xl border border-border bg-surface-main px-2 py-3 text-xs text-txt-primary" /></div></Field>
          <Field label="3 · Initial capital (₹)"><input type="number" min="1000" step="1000" value={capital} onChange={(e) => setCapital(e.target.value)} className="rounded-xl border border-border bg-surface-main px-3 py-3 text-xs text-txt-primary" /></Field>
          <Field label="4 · Strategy"><select value={strategyType} onChange={(e) => setStrategyType(e.target.value as StrategyType)} className="rounded-xl border border-border bg-surface-main px-3 py-3 text-xs text-txt-primary">{Object.entries(strategyNames).map(([value, name]) => <option key={value} value={value}>{name}</option>)}</select></Field>
        </div>

        {strategyType === "custom" && <div className="grid gap-4 lg:grid-cols-2"><ConditionEditor title="Buy" rule={entry} onChange={setEntry} /><ConditionEditor title="Sell" rule={exitRule} onChange={setExitRule} /></div>}

        <div className="grid gap-5 border-t border-border pt-5 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Position size"><select value={positionPct} onChange={(e) => setPositionPct(e.target.value)} className="rounded-xl border border-border bg-surface-main px-3 py-3 text-xs text-txt-primary"><option value="100">Full available capital (100%)</option><option value="75">75% of cash</option><option value="50">50% of cash</option><option value="25">25% of cash</option></select></Field>
          <Field label="Transaction cost assumption (%)"><input type="number" min="0" max="5" step="0.01" value={transactionCost} onChange={(e) => setTransactionCost(e.target.value)} className="rounded-xl border border-border bg-surface-main px-3 py-3 text-xs text-txt-primary" /></Field>
          <Field label="Slippage assumption (%)"><input type="number" min="0" max="5" step="0.01" value={slippage} onChange={(e) => setSlippage(e.target.value)} className="rounded-xl border border-border bg-surface-main px-3 py-3 text-xs text-txt-primary" /></Field>
          <label className="flex cursor-pointer items-center gap-2 self-end rounded-xl border border-border bg-surface-main px-3 py-3 text-xs text-txt-secondary"><input type="checkbox" checked={compareStrategies} onChange={(e) => setCompareStrategies(e.target.checked)} className="accent-blue-500" /> Compare all preset strategies</label>
        </div>

        {strategyType !== "custom" && <div className="rounded-xl border border-border bg-surface-main/60 p-4 text-xs text-txt-secondary"><p className="font-bold text-txt-primary">Strategy summary · {strategyNames[strategyType]}</p><p className="mt-1">Entry: {({ golden_cross: "SMA20 crosses above SMA50", rsi_momentum: "RSI crosses above 30", macd_trend: "MACD crosses above signal", conservative_trend: "SMA50 > SMA200 and RSI 40–65", buy_hold: "Buy at first period open" } as Record<string, string>)[strategyType]}</p><p>Exit: {({ golden_cross: "SMA20 crosses below SMA50", rsi_momentum: "RSI crosses above 70", macd_trend: "MACD crosses below signal", conservative_trend: "SMA50 < SMA200", buy_hold: "Hold to final period close" } as Record<string, string>)[strategyType]}</p></div>}

        <div className="flex flex-col gap-3 border-t border-border pt-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="max-w-2xl text-[10px] leading-relaxed text-txt-muted"><Clock3 className="mr-1 inline h-3 w-3" /> Simulation assumptions only—not broker charges. Signal uses completed bar; order executes next bar open with slippage. Buy &amp; Hold enters first open. Positions liquidate at final close.</p>
          <button disabled={running} className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-primary px-6 py-3 text-xs font-extrabold text-white shadow-lg shadow-brand-primary/20 hover:bg-brand-bright disabled:cursor-wait disabled:opacity-60">{running ? <><Loader2 className="h-4 w-4 animate-spin" /> Running historical simulation…</> : <><Play className="h-4 w-4" /> Run Backtest</>}</button>
        </div>
      </form>

      {error && <div role="alert" className="flex items-start gap-2 rounded-xl border border-financial-loss/30 bg-financial-loss/10 p-4 text-xs text-financial-loss"><ShieldAlert className="h-4 w-4 shrink-0" />{error}</div>}

      {result && <div className="space-y-6">
        <section className="space-y-4 rounded-2xl border border-border bg-surface-card p-5 shadow-xl sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-xl font-extrabold text-txt-primary">Backtest Results · {result.symbol}</h2><p className="mt-1 text-[10px] text-txt-muted">{result.strategy_summary.name} · {result.data.requested_period.start} → {result.data.requested_period.end} · {result.data.candles} real daily candles</p></div><span className="flex items-center gap-1 rounded-full border border-financial-profit/20 bg-financial-profit/10 px-2.5 py-1 text-[9px] font-bold text-financial-profit"><Database className="h-3 w-3" />{result.data.provider} · HISTORICAL</span></div>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-6">{[
            ["Initial capital", money(metric("initial_capital"))], ["Final value", money(metric("final_value"))], ["Net P/L", money(metric("net_profit_loss"))], ["Total return", `${Number(metric("total_return_pct") || 0) >= 0 ? "+" : ""}${Number(metric("total_return_pct") || 0).toFixed(2)}%`], ["Max drawdown", `${Number(metric("max_drawdown_pct") || 0).toFixed(2)}%`], ["Total trades", String(metric("total_trades") ?? 0)], ["Win rate", metric("win_rate_pct") == null ? "—" : `${metric("win_rate_pct")}%`], ["Sharpe · √252", metric("sharpe_ratio") == null ? "Insufficient data" : Number(metric("sharpe_ratio")).toFixed(2)], ["CAGR", metric("cagr_pct") == null ? "Insufficient period" : `${metric("cagr_pct")}%`], ["Volatility", metric("daily_volatility_pct") == null ? "—" : `${metric("daily_volatility_pct")}%`], ["Profit factor", metric("profit_factor") == null ? "—" : metric("profit_factor")], ["Costs + slippage", `${result.assumptions.transaction_cost_pct}% + ${result.assumptions.slippage_pct}%`],
          ].map(([label, value]) => <div key={label} className="rounded-xl border border-border bg-surface-main p-3"><span className="text-[9px] font-bold uppercase tracking-wide text-txt-muted">{label}</span><p className="mt-1 text-sm font-extrabold text-txt-primary">{value}</p></div>)}</div>
          <div className="grid gap-3 text-[10px] text-txt-muted sm:grid-cols-2"><p>Max drawdown: peak {money(metric("drawdown_peak_value"))} ({metric("drawdown_peak_date")}) → trough {money(metric("drawdown_trough_value"))} ({metric("drawdown_trough_date")}).</p><p>Execution: next-bar open · Source: {result.data.source} · Retrieved {new Date(result.data.retrieved_at).toLocaleString()}</p></div>
        </section>

        <div className="grid gap-6 xl:grid-cols-2">
          <section className="rounded-2xl border border-border bg-surface-card p-5 shadow-xl"><div className="mb-4 flex items-center justify-between"><div><h3 className="font-bold text-txt-primary">Equity Curve</h3><p className="text-[10px] text-txt-muted">Strategy vs same-asset Buy &amp; Hold and NIFTY 50 price index when available</p></div><span className="text-[9px] font-bold text-brand-bright">₹ INR</span></div><div className="h-72"><ResponsiveContainer width="100%" height="100%"><AreaChart data={equityData}><CartesianGrid strokeDasharray="3 3" stroke="#263552" /><XAxis dataKey="date" tick={{ fill: "#94A3B8", fontSize: 9 }} minTickGap={30} /><YAxis tick={{ fill: "#94A3B8", fontSize: 9 }} tickFormatter={(v) => `₹${Math.round(v / 1000)}k`} /><Tooltip labelStyle={{ color: "#CBD5E1" }} contentStyle={{ backgroundColor: "#151F35", borderColor: "#263552", fontSize: 10 }} formatter={(v: any) => money(Number(v))} /><Area type="monotone" dataKey="portfolio_value" name="Strategy" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.16} dot={false} isAnimationActive={false} /><Area type="monotone" dataKey="buy_hold_value" name="Buy & Hold" stroke="#10B981" fill="none" dot={false} isAnimationActive={false} /><Area type="monotone" dataKey="benchmark_value" name="NIFTY 50 index proxy" stroke="#A78BFA" fill="none" dot={false} isAnimationActive={false} />{equityData.map((point) => result.trades.filter((trade) => trade.timestamp.slice(0, 10) === point.date).map((trade) => <ReferenceDot key={`${trade.trade_id}-${point.date}`} x={point.date} y={point.portfolio_value} r={5} fill={trade.action === "BUY" ? "#10B981" : "#EF4444"} stroke="#0B1020" onClick={() => setSelectedTrade(trade)} />))}</AreaChart></ResponsiveContainer></div><div className="mt-3 flex flex-wrap gap-2">{result.trades.map((trade) => <button key={trade.trade_id} onClick={() => setSelectedTrade(trade)} className={`rounded-full px-2 py-1 text-[9px] font-bold ${trade.action === "BUY" ? "bg-financial-profit/10 text-financial-profit" : "bg-financial-loss/10 text-financial-loss"}`}>{trade.action} {trade.timestamp.slice(0, 10)}</button>)}</div></section>
          <section className="rounded-2xl border border-border bg-surface-card p-5 shadow-xl"><div className="mb-4"><h3 className="font-bold text-txt-primary">Drawdown Curve</h3><p className="text-[10px] text-txt-muted">Peak-to-trough portfolio decline through time</p></div><div className="h-72"><ResponsiveContainer width="100%" height="100%"><AreaChart data={drawdownData}><CartesianGrid strokeDasharray="3 3" stroke="#263552" /><XAxis dataKey="date" tick={{ fill: "#94A3B8", fontSize: 9 }} minTickGap={30} /><YAxis tick={{ fill: "#94A3B8", fontSize: 9 }} tickFormatter={(v) => `${v}%`} /><Tooltip labelStyle={{ color: "#CBD5E1" }} contentStyle={{ backgroundColor: "#151F35", borderColor: "#263552", fontSize: 10 }} formatter={(v: any) => [`${Number(v).toFixed(2)}%`, "Drawdown"]} /><Area type="monotone" dataKey="drawdown_pct" stroke="#EF4444" fill="#EF4444" fillOpacity={0.22} isAnimationActive={false} /></AreaChart></ResponsiveContainer></div></section>
        </div>

        {selectedTrade && <div className="rounded-xl border border-brand-primary/30 bg-brand-primary/5 p-4 text-xs text-txt-secondary"><div className="flex items-center justify-between"><strong className="text-txt-primary">{selectedTrade.action} · {selectedTrade.timestamp.slice(0, 10)} · {selectedTrade.quantity} shares @ {money(selectedTrade.execution_price)}</strong><button onClick={() => setSelectedTrade(null)} className="text-txt-muted">Dismiss</button></div><p className="mt-1">Gross {money(selectedTrade.gross_value)} · costs {money(selectedTrade.transaction_cost)} · realized P/L {money(selectedTrade.realized_pnl)} · {selectedTrade.reason}</p></div>}

        <section className="overflow-hidden rounded-2xl border border-border bg-surface-card shadow-xl"><div className="flex flex-wrap items-center justify-between gap-3 border-b border-border p-5"><div><h3 className="font-bold text-txt-primary">Trade History</h3><p className="text-[10px] text-txt-muted">{result.trades.length} executed orders · whole shares only</p></div><select value={tradeFilter} onChange={(e) => setTradeFilter(e.target.value as typeof tradeFilter)} className="rounded-lg border border-border bg-surface-main px-3 py-2 text-xs text-txt-primary"><option value="ALL">All trades</option><option value="BUY">Buy</option><option value="SELL">Sell</option></select></div><div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-[10px]"><thead className="bg-surface-main text-txt-muted"><tr>{["Date", "Action", "Execution", "Qty", "Gross", "Costs", "Realized P/L", "Reason"].map((head) => <th key={head} className="px-4 py-3 font-bold uppercase">{head}</th>)}</tr></thead><tbody>{visibleTrades.map((trade) => <tr key={trade.trade_id} onClick={() => setSelectedTrade(trade)} className="cursor-pointer border-t border-border/70 text-txt-secondary hover:bg-surface-elevated"><td className="px-4 py-3">{new Date(trade.timestamp).toLocaleDateString()}</td><td className={`px-4 py-3 font-extrabold ${trade.action === "BUY" ? "text-financial-profit" : "text-financial-loss"}`}>{trade.action}</td><td className="px-4 py-3">{money(trade.execution_price)}</td><td className="px-4 py-3">{trade.quantity}</td><td className="px-4 py-3">{money(trade.gross_value)}</td><td className="px-4 py-3">{money(trade.transaction_cost + trade.slippage_cost)}</td><td className="px-4 py-3">{money(trade.realized_pnl)}</td><td className="px-4 py-3">{trade.reason}</td></tr>)}</tbody></table>{visibleTrades.length === 0 && <p className="p-8 text-center text-xs text-txt-muted">No executed trades for this filter.</p>}</div></section>

        <section className="rounded-2xl border border-border bg-surface-card p-5 shadow-xl"><div className="flex flex-wrap items-center justify-between gap-3"><div><h3 className="flex items-center gap-2 font-bold text-txt-primary"><Activity className="h-4 w-4 text-ai-light" />Benchmark comparison</h3><p className="mt-1 text-[10px] text-txt-muted">Strategy return vs same-stock Buy &amp; Hold</p></div><span className="text-xs font-bold text-txt-primary">NIFTY 50 {result.comparison.nifty50_return_pct == null ? "unavailable" : `${result.comparison.nifty50_return_pct.toFixed(2)}%`}</span></div><div className="mt-4 grid gap-3 sm:grid-cols-3"><div className="rounded-xl bg-surface-main p-3"><p className="text-[9px] text-txt-muted">Strategy</p><strong className="text-sm text-brand-bright">{result.comparison.strategy_return_pct.toFixed(2)}%</strong></div><div className="rounded-xl bg-surface-main p-3"><p className="text-[9px] text-txt-muted">Buy &amp; Hold</p><strong className="text-sm text-financial-profit">{result.comparison.buy_hold_return_pct.toFixed(2)}%</strong><p className="text-[9px] text-txt-muted">Outperformance {result.comparison.outperformance_vs_buy_hold_pct_points.toFixed(2)} pp</p></div><div className="rounded-xl bg-surface-main p-3"><p className="text-[9px] text-txt-muted">NIFTY 50</p><strong className="text-sm text-ai-light">{result.comparison.nifty50_return_pct == null ? "Unavailable" : `${result.comparison.nifty50_return_pct.toFixed(2)}%`}</strong><p className="text-[9px] text-txt-muted">{result.comparison.outperformance_vs_nifty50_pct_points == null ? result.comparison.nifty50_unavailable_reason : `${result.comparison.outperformance_vs_nifty50_pct_points.toFixed(2)} pp relative`}</p></div></div></section>

        {result.strategy_comparison.length > 0 && <section className="overflow-x-auto rounded-2xl border border-border bg-surface-card p-5 shadow-xl"><h3 className="mb-3 font-bold text-txt-primary">Strategy comparison · best historical result highlighted</h3><table className="w-full min-w-[580px] text-left text-[10px]"><thead className="text-txt-muted"><tr>{["Strategy", "Return", "Max DD", "Sharpe", "Win rate", "Trades"].map((x) => <th key={x} className="px-3 py-2">{x}</th>)}</tr></thead><tbody>{result.strategy_comparison.map((item, i) => <tr key={item.strategy} className={`border-t border-border ${i === 0 ? "bg-financial-profit/5 text-financial-profit" : "text-txt-secondary"}`}><td className="px-3 py-2 font-bold">{item.strategy}{i === 0 ? " · Best historical result" : ""}</td><td className="px-3 py-2">{item.return_pct.toFixed(2)}%</td><td className="px-3 py-2">{item.max_drawdown_pct.toFixed(2)}%</td><td className="px-3 py-2">{item.sharpe_ratio == null ? "—" : item.sharpe_ratio.toFixed(2)}</td><td className="px-3 py-2">{item.win_rate_pct == null ? "—" : `${item.win_rate_pct}%`}</td><td className="px-3 py-2">{item.total_trades}</td></tr>)}</tbody></table></section>}

        <section className="rounded-2xl border border-ai-violet/30 bg-gradient-to-br from-surface-card to-ai-violet/5 p-5 shadow-xl"><div className="flex flex-wrap items-center justify-between gap-3"><div><h3 className="flex items-center gap-2 font-bold text-txt-primary"><BrainCircuit className="h-4 w-4 text-ai-light" /> SmartStock AI Analysis</h3><p className="mt-1 text-[10px] text-txt-muted">Explanations use saved, server-calculated metrics; they never calculate the backtest.</p></div><button onClick={requestAnalysis} disabled={analyzing} className="inline-flex items-center gap-2 rounded-lg border border-ai-violet/40 bg-ai-violet/10 px-4 py-2 text-[10px] font-bold text-ai-light disabled:opacity-50">{analyzing ? <Loader2 className="h-3 w-3 animate-spin" /> : <BrainCircuit className="h-3 w-3" />}{analyzing ? "Analyzing…" : "Explain results"}</button></div>{analysis ? <><p className="mt-3 text-[9px] font-bold uppercase tracking-wider text-ai-light">{analysisMode === "AI explanation of server-calculated metrics" ? "AI provider analysis" : "Deterministic metrics explanation · AI provider not configured"}</p><p className="mt-2 whitespace-pre-wrap text-xs leading-relaxed text-txt-secondary">{analysis}</p></> : <p className="mt-3 text-[10px] text-txt-muted">Use Explain Results for a data-grounded explanation. A configured AI provider supplies free-form analysis; otherwise the app returns a deterministic summary.</p>}<p className="mt-4 flex items-center gap-1 text-[9px] text-warning"><ShieldAlert className="h-3 w-3" />Past backtest performance does not guarantee future results. Not financial advice.</p></section>
      </div>}
    </div>
  );
}

export default function BacktestingPage() {
  return <ProtectedRoute><BacktestingContent /></ProtectedRoute>;
}
