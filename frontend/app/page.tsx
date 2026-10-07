"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  ShieldCheck,
  Zap,
  Sparkles,
  Server,
  Wallet,
  BrainCircuit,
  ArrowUpRight,
  Search,
} from "lucide-react";
import { MarketIndicesBar } from "@/components/MarketIndicesBar";
import { StockSearch } from "@/components/StockSearch";
import { MarketNewsFeed } from "@/components/MarketNewsFeed";

interface HealthData {
  status: string;
  app_name: string;
  environment: string;
  timestamp: string;
  components: {
    database: { status: string; details: string };
    redis: { status: string; details: string };
    market_data_provider: { status: string; details: string };
  };
}

export default function HomePage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/health")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setHealth(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col gap-8">
      
      {/* Live Market Indices Ticker Bar */}
      <MarketIndicesBar />

      {/* Hero Header */}
      <div className="p-8 rounded-2xl bg-gradient-to-br from-surface-card via-surface-elevated to-surface-card border border-border relative overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-brand-primary/10 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-64 h-64 bg-ai-violet/10 rounded-full blur-2xl pointer-events-none" />
        
        <div className="relative z-10 max-w-3xl flex flex-col gap-5">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-primary/10 border border-brand-primary/20 text-brand-bright text-xs font-semibold w-fit">
            <Zap className="w-3.5 h-3.5" />
            <span>Milestone 3 — Market Engine & Financial Charts Online</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-txt-primary leading-tight">
            Financial Intelligence & <br className="hidden sm:inline" />
            <span className="bg-gradient-to-r from-brand-bright via-brand-primary to-ai-light bg-clip-text text-transparent">
              Virtual Stock Trading Platform
            </span>
          </h1>

          <p className="text-txt-secondary text-sm sm:text-base leading-relaxed">
            Explore stock quotes, technical indicators (RSI, MACD, SMA), interactive price charts, explainable AI predictions, and practice risk-free virtual trading with your ₹500 demo wallet balance.
          </p>

          {/* Instant Stock Search */}
          <div className="pt-2">
            <StockSearch />
          </div>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Link
              href="/stocks"
              className="px-5 py-2.5 rounded-xl bg-brand-primary hover:bg-brand-bright text-white font-bold text-xs shadow-lg shadow-brand-primary/25 transition-all flex items-center gap-2"
            >
              Explore Stock Directory <ArrowUpRight className="w-4 h-4" />
            </Link>
            <Link
              href="/compare"
              className="px-5 py-2.5 rounded-xl border border-ai-violet/40 bg-ai-violet/10 hover:bg-ai-violet/20 text-ai-light font-bold text-xs shadow-lg shadow-ai-violet/10 transition-all flex items-center gap-2"
            >
              Compare Stocks <ArrowUpRight className="w-4 h-4" />
            </Link>
            <Link
              href="/backtesting"
              className="px-5 py-2.5 rounded-xl border border-border bg-surface-card hover:border-ai-violet/50 text-txt-secondary font-bold text-xs transition-all flex items-center gap-2"
            >
              Backtesting Lab <ArrowUpRight className="w-4 h-4" />
            </Link>
            <div className="flex items-center gap-2 text-xs font-medium text-txt-muted bg-surface-main/80 px-3 py-2 rounded-lg border border-border">
              <ShieldCheck className="w-4 h-4 text-financial-profit" />
              <span>Virtual Demo Wallet (₹500)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Popular Stocks Shortcuts & System Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Market Discovery Shortcut Card */}
        <div className="p-6 rounded-xl bg-surface-card border border-border flex flex-col justify-between gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-brand-primary/10 text-brand-bright">
                <Search className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-txt-primary">Stock Discovery</h3>
                <span className="text-xs text-txt-muted">NSE, BSE & NASDAQ</span>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase bg-warning/20 text-warning">
              DELAYED (15M)
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1.5 border-b border-border/40">
              <span className="text-txt-muted">Popular Equities:</span>
              <span className="font-bold text-txt-primary">RELIANCE, TCS, INFY, AAPL</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-border/40">
              <span className="text-txt-muted">Timeframe Series:</span>
              <span className="font-bold text-txt-primary">1D, 1W, 1M, 3M, 6M, 1Y, 5Y</span>
            </div>
          </div>

          <Link
            href="/stocks"
            className="text-xs font-semibold text-brand-bright hover:underline inline-flex items-center gap-1"
          >
            Browse Supported Equities <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Demo Wallet & Virtual Trading */}
        <div className="p-6 rounded-xl bg-surface-card border border-border flex flex-col justify-between gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-financial-profit/10 text-financial-profit">
                <Wallet className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-txt-primary">Virtual Trading Engine</h3>
                <span className="text-xs text-txt-muted">Milestone 4 Ready</span>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase bg-brand-primary/20 text-brand-bright">
              SIMULATED
            </span>
          </div>

          <div className="p-4 rounded-lg bg-surface-elevated border border-border flex flex-col gap-1">
            <span className="text-xs text-txt-muted font-medium">Initial User Demo Allocation</span>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-extrabold text-financial-profit font-numeric">₹500.00</span>
              <span className="text-xs font-mono text-txt-muted">50,000 Paise</span>
            </div>
          </div>

          <p className="text-xs text-txt-secondary">
            Monetary accounting uses exact integer paise values without floating point drift.
          </p>
        </div>

        {/* Technical Indicators & AI */}
        <div className="p-6 rounded-xl bg-surface-card border border-border flex flex-col justify-between gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-ai-violet/10 text-ai-light">
                <BrainCircuit className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-txt-primary">Technical Analysis</h3>
                <span className="text-xs text-txt-muted">Calculated Indicators</span>
              </div>
            </div>
            <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase bg-ai-violet/20 text-ai-light">
              RSI / MACD / SMA
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1.5 border-b border-border/40">
              <span className="text-txt-muted font-medium">Relative Strength Index:</span>
              <span className="font-bold text-ai-light">RSI 14 Period</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-border/40">
              <span className="text-txt-muted font-medium">Moving Averages:</span>
              <span className="font-bold text-brand-bright">SMA 20 / SMA 50</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-txt-muted font-medium">Trend Convergence:</span>
              <span className="font-bold text-financial-profit">MACD Histogram</span>
            </div>
          </div>

        </div>

      </div>

      {/* Integrated Financial News & Market Sentiment Section */}
      <MarketNewsFeed />

    </div>
  );
}
