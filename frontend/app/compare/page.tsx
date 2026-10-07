"use client";

import React, { useState } from "react";
import { ArrowRightLeft, BrainCircuit, Gauge, ShieldCheck, Sparkles, TrendingDown, TrendingUp } from "lucide-react";

interface StockComparisonResult {
  preferred_stock: string;
  decision: string;
  confidence: number;
  summary: string;
  rationale: string[];
  disclaimer: string;
  stocks: Array<{
    symbol: string;
    price: number;
    change_percent: number;
    rsi: number;
    momentum_5d: number;
    sma20: number;
    sma50: number;
    volatility: number;
    score: number;
    recommendation: string;
    summary: string;
  }>;
}

const defaultDecisionTone = (decision: string) => {
  if (decision === "BUY") return "bg-financial-profit/15 text-financial-profit border-financial-profit/30";
  if (decision === "HOLD") return "bg-warning/10 text-warning border-warning/30";
  return "bg-financial-loss/15 text-financial-loss border-financial-loss/30";
};

export default function CompareStocksPage() {
  const [symbolA, setSymbolA] = useState("RELIANCE");
  const [symbolB, setSymbolB] = useState("TCS");
  const [result, setResult] = useState<StockComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const compareStocks = async (event?: React.FormEvent) => {
    event?.preventDefault();
    const first = symbolA.trim().toUpperCase();
    const second = symbolB.trim().toUpperCase();

    if (!first || !second) {
      setError("Please enter two valid stock symbols to compare.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams({ symbol_a: first, symbol_b: second });
      const response = await fetch(`http://localhost:8000/api/v1/stocks/compare?${params.toString()}`);
      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload?.detail || "Unable to compare these stocks right now.");
      }

      setResult(payload);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const preferred = result?.stocks?.find((stock) => stock.symbol === result.preferred_stock);
  const alt = result?.stocks?.find((stock) => stock.symbol !== result?.preferred_stock);

  return (
    <div className="space-y-8">
      <div className="rounded-2xl bg-gradient-to-br from-surface-card via-surface-elevated to-surface-card border border-border p-8 shadow-2xl">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-ai-violet/30 bg-ai-violet/10 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-ai-light">
              <Sparkles className="h-3.5 w-3.5" /> AI Stock Comparator
            </div>
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight text-txt-primary">Compare Two Stocks</h1>
              <p className="mt-2 max-w-2xl text-sm text-txt-secondary">
                Use live market data and technical momentum signals to identify which stock looks stronger for a short-term buy or hold decision.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-border bg-surface-main px-3 py-2 text-xs text-txt-muted">
            <ShieldCheck className="h-4 w-4 text-financial-profit" />
            Research-only AI signal
          </div>
        </div>
      </div>

      <form onSubmit={compareStocks} className="rounded-2xl border border-border bg-surface-card p-6 shadow-xl">
        <div className="grid gap-4 md:grid-cols-[1fr_auto_1fr_auto] md:items-end">
          <div className="space-y-2">
            <label className="text-[10px] font-bold uppercase tracking-[0.14em] text-txt-muted">Stock A</label>
            <input
              value={symbolA}
              onChange={(e) => setSymbolA(e.target.value)}
              className="w-full rounded-xl border border-border bg-surface-elevated px-4 py-3 text-sm font-semibold text-txt-primary outline-none ring-0 transition focus:border-brand-primary"
              placeholder="RELIANCE"
            />
          </div>

          <div className="flex items-center justify-center pb-3 md:pb-0">
            <div className="flex h-11 w-11 items-center justify-center rounded-full border border-brand-primary/30 bg-brand-primary/10 text-brand-bright">
              <ArrowRightLeft className="h-4 w-4" />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-[10px] font-bold uppercase tracking-[0.14em] text-txt-muted">Stock B</label>
            <input
              value={symbolB}
              onChange={(e) => setSymbolB(e.target.value)}
              className="w-full rounded-xl border border-border bg-surface-elevated px-4 py-3 text-sm font-semibold text-txt-primary outline-none ring-0 transition focus:border-brand-primary"
              placeholder="TCS"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="rounded-xl bg-brand-primary px-5 py-3 text-xs font-bold uppercase tracking-[0.12em] text-white shadow-lg shadow-brand-primary/20 transition hover:bg-brand-bright disabled:opacity-60"
          >
            {loading ? "Comparing..." : "Compare"}
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded-xl border border-financial-loss/30 bg-financial-loss/10 px-4 py-3 text-sm text-financial-loss">
            {error}
          </div>
        )}
      </form>

      {result && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-border bg-surface-card p-6 shadow-xl">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-txt-muted">AI Recommendation</p>
                <h2 className="mt-2 text-2xl font-extrabold text-txt-primary">{result.preferred_stock} is preferred</h2>
                <p className="mt-2 max-w-3xl text-sm text-txt-secondary">{result.summary}</p>
              </div>

              <div className="flex flex-col items-start gap-2 lg:items-end">
                <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-bold ${defaultDecisionTone(result.decision)}`}>
                  {result.decision}
                </span>
                <span className="flex items-center gap-2 rounded-full border border-border bg-surface-elevated px-3 py-1 text-xs font-semibold text-txt-secondary">
                  <Gauge className="h-3.5 w-3.5 text-ai-light" />
                  Confidence {result.confidence.toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            {result.stocks.map((stock) => {
              const isPreferred = stock.symbol === result.preferred_stock;
              const trendIsPositive = stock.change_percent >= 0;

              return (
                <div
                  key={stock.symbol}
                  className={`rounded-2xl border p-5 shadow-xl ${isPreferred ? "border-brand-primary/40 bg-brand-primary/5" : "border-border bg-surface-card"}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-2xl font-extrabold text-txt-primary">{stock.symbol}</h3>
                        {isPreferred && (
                          <span className="rounded-full bg-brand-primary/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.12em] text-brand-bright">
                            Preferred
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-xs uppercase tracking-[0.14em] text-txt-muted">{stock.recommendation}</p>
                    </div>

                    <div className={`flex items-center gap-1 rounded-lg px-2 py-1 text-sm font-bold ${trendIsPositive ? "bg-financial-profit/15 text-financial-profit" : "bg-financial-loss/15 text-financial-loss"}`}>
                      {trendIsPositive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                      {trendIsPositive ? "+" : ""}{stock.change_percent.toFixed(2)}%
                    </div>
                  </div>

                  <div className="mt-5 flex items-baseline justify-between border-t border-border/50 pt-4">
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-txt-muted">Current Price</p>
                      <p className="mt-1 text-3xl font-extrabold text-txt-primary font-numeric">₹{stock.price.toFixed(2)}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-txt-muted">Score</p>
                      <p className="mt-1 text-2xl font-extrabold text-ai-light font-numeric">{stock.score}</p>
                    </div>
                  </div>

                  <div className="mt-5 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-xl border border-border bg-surface-elevated p-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-txt-muted">RSI</p>
                      <p className="mt-2 text-lg font-extrabold text-txt-primary font-numeric">{stock.rsi.toFixed(1)}</p>
                    </div>
                    <div className="rounded-xl border border-border bg-surface-elevated p-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-txt-muted">5D Momentum</p>
                      <p className="mt-2 text-lg font-extrabold text-txt-primary font-numeric">{stock.momentum_5d.toFixed(2)}%</p>
                    </div>
                    <div className="rounded-xl border border-border bg-surface-elevated p-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-txt-muted">SMA 20</p>
                      <p className="mt-2 text-lg font-extrabold text-txt-primary font-numeric">₹{stock.sma20.toFixed(2)}</p>
                    </div>
                    <div className="rounded-xl border border-border bg-surface-elevated p-3">
                      <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-txt-muted">SMA 50</p>
                      <p className="mt-2 text-lg font-extrabold text-txt-primary font-numeric">₹{stock.sma50.toFixed(2)}</p>
                    </div>
                  </div>

                  <div className="mt-4 rounded-xl border border-border bg-surface-elevated p-3 text-xs text-txt-secondary leading-relaxed">
                    {stock.summary}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="rounded-2xl border border-border bg-surface-card p-6 shadow-xl">
            <div className="flex items-center gap-2 text-ai-light">
              <BrainCircuit className="h-5 w-5" />
              <h3 className="text-lg font-extrabold text-txt-primary">Decision Rationale</h3>
            </div>
            <ul className="mt-4 space-y-3">
              {result.rationale.map((point, index) => (
                <li key={index} className="flex gap-3 rounded-xl border border-border bg-surface-elevated px-4 py-3 text-sm text-txt-secondary">
                  <span className="mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-brand-primary/15 text-[10px] font-bold text-brand-bright">
                    {index + 1}
                  </span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>

            <div className="mt-5 rounded-xl border border-border bg-surface-elevated px-4 py-3 text-xs text-txt-muted">
              {result.disclaimer}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
