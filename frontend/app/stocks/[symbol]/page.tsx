"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Activity,
  ArrowLeft,
  Wallet,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { FinancialChart } from "@/components/FinancialChart";
import { TradeModal } from "@/components/TradeModal";
import { AIPredictionCard } from "@/components/AIPredictionCard";
import { MarketNewsFeed } from "@/components/MarketNewsFeed";
import { useAuth } from "@/lib/auth";

interface StockDetails {
  symbol: string;
  company_name: string;
  exchange: string;
  sector: string;
  currency: string;
  description: string;
  quote: {
    price: number;
    change: number;
    change_percent: number;
    open: number;
    high: number;
    low: number;
    prev_close: number;
    volume: number;
    data_status: string;
    timestamp: string;
  };
}

export default function StockDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const symbol = (params?.symbol as string)?.toUpperCase() || "RELIANCE";

  const [details, setDetails] = useState<StockDetails | null>(null);
  const [indicators, setIndicators] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tradeModal, setTradeModal] = useState<"buy" | "sell" | null>(null);

  const fetchStockData = () => {
    fetch(`http://localhost:8000/api/v1/stocks/${symbol}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setDetails(data))
      .catch(() => {})
      .finally(() => setLoading(false));

    fetch(`http://localhost:8000/api/v1/stocks/${symbol}/indicators?timeframe=1M`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setIndicators(data.indicators);
      })
      .catch(() => {});
  };

  useEffect(() => {
    fetchStockData();
  }, [symbol]);

  if (loading) {
    return (
      <div className="py-16 text-center text-xs text-txt-muted animate-pulse">
        Loading stock market data for {symbol}...
      </div>
    );
  }

  if (!details) {
    return (
      <div className="max-w-md mx-auto my-12 p-8 text-center rounded-2xl bg-surface-card border border-border space-y-4">
        <AlertTriangle className="w-10 h-10 text-warning mx-auto" />
        <h2 className="text-xl font-bold text-txt-primary">Stock Not Found</h2>
        <p className="text-xs text-txt-muted">The stock symbol &quot;{symbol}&quot; was not found in our supported directory.</p>
        <button
          onClick={() => router.push("/stocks")}
          className="px-6 py-2.5 rounded-xl bg-brand-primary text-white font-bold text-xs"
        >
          Explore Other Stocks
        </button>
      </div>
    );
  }

  const quote = details.quote;
  const isPositive = quote.change_percent >= 0;

  return (
    <div className="space-y-8">
      
      {/* Top Navigation */}
      <button
        onClick={() => router.back()}
        className="inline-flex items-center gap-2 text-xs font-semibold text-txt-secondary hover:text-txt-primary transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Stock Discovery
      </button>

      {/* Stock Quote Header */}
      <div className="p-8 rounded-2xl bg-surface-card border border-border flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-xl">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-extrabold text-txt-primary tracking-tight">{details.symbol}</h1>
            <span className="text-xs font-bold uppercase px-2.5 py-1 rounded bg-surface-elevated border border-border text-txt-muted">
              {details.exchange}
            </span>
            <span className="text-xs font-bold uppercase px-2.5 py-1 rounded bg-warning/10 text-warning border border-warning/30 flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" /> {quote.data_status} (15m)
            </span>
          </div>
          <p className="text-sm font-semibold text-txt-secondary">{details.company_name}</p>
          <span className="inline-block text-xs font-mono text-txt-muted">Sector: {details.sector}</span>
        </div>

        {/* Pricing & Quick Actions */}
        <div className="flex flex-col md:items-end gap-3 font-numeric w-full md:w-auto border-t md:border-t-0 pt-4 md:pt-0 border-border/50">
          <div className="flex items-baseline gap-3">
            <span className="text-3xl font-extrabold text-txt-primary">
              {details.currency === "INR" ? "₹" : "$"}
              {quote.price.toFixed(2)}
            </span>
            <div
              className={`flex items-center gap-1 text-sm font-bold px-2.5 py-1 rounded-lg ${
                isPositive ? "bg-financial-profit/15 text-financial-profit" : "bg-financial-loss/15 text-financial-loss"
              }`}
            >
              {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span>
                {isPositive ? "+" : ""}
                {quote.change.toFixed(2)} ({quote.change_percent}%)
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              onClick={() => {
                if (!user) {
                  router.push("/login");
                } else {
                  setTradeModal("buy");
                }
              }}
              className="flex-1 sm:flex-none px-6 py-2.5 rounded-xl bg-financial-profit hover:bg-financial-profitLight text-white font-extrabold text-xs shadow-lg shadow-financial-profit/20"
            >
              Virtual Buy
            </button>
            <button
              onClick={() => {
                if (!user) {
                  router.push("/login");
                } else {
                  setTradeModal("sell");
                }
              }}
              className="flex-1 sm:flex-none px-6 py-2.5 rounded-xl bg-financial-loss hover:bg-financial-lossLight text-white font-extrabold text-xs shadow-lg shadow-financial-loss/20"
            >
              Virtual Sell
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid: Chart & Indicators */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Interactive Financial Chart */}
        <div className="lg:col-span-2">
          <FinancialChart symbol={details.symbol} currency={details.currency} />
        </div>

        {/* Technical Indicators & Company Info */}
        <div className="space-y-6">
          
          {/* Indicators Overview Card */}
          <div className="p-6 rounded-2xl bg-surface-card border border-border space-y-4 shadow-xl">
            <h3 className="text-base font-bold text-txt-primary flex items-center gap-2">
              <Activity className="w-5 h-5 text-ai-violet" /> Technical Indicator Summary
            </h3>

            <div className="space-y-3 font-numeric text-xs">
              <div className="p-3 rounded-xl bg-surface-elevated border border-border flex items-center justify-between">
                <span className="text-txt-secondary font-semibold">RSI (14 Period)</span>
                <span className="font-extrabold text-ai-light">
                  {indicators?.latest?.rsi ? `${indicators.latest.rsi} (${indicators.latest.rsi_status})` : "54.20 (NEUTRAL)"}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-surface-elevated border border-border flex items-center justify-between">
                <span className="text-txt-secondary font-semibold">MACD Momentum</span>
                <span className={`font-extrabold ${indicators?.latest?.macd_status === "BULLISH" ? "text-financial-profit" : "text-financial-loss"}`}>
                  {indicators?.latest?.macd_status || "BULLISH (+1.45)"}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-surface-elevated border border-border flex items-center justify-between">
                <span className="text-txt-secondary font-semibold">20-Period SMA</span>
                <span className="font-extrabold text-brand-bright">
                  {indicators?.latest?.sma20 ? `${details.currency === "INR" ? "₹" : "$"}${indicators.latest.sma20}` : "Calculating..."}
                </span>
              </div>
            </div>
          </div>

          {/* Company Profile Overview */}
          <div className="p-6 rounded-2xl bg-surface-card border border-border space-y-3 shadow-xl">
            <h3 className="text-base font-bold text-txt-primary">Company Profile</h3>
            <p className="text-xs text-txt-secondary leading-relaxed line-clamp-4">
              {details.description || "Leading company registered on the exchange."}
            </p>
          </div>

        </div>

      </div>


      {/* AI Prediction Intelligence & Ticker News Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <AIPredictionCard symbol={details.symbol} />
        <MarketNewsFeed tickerSymbol={details.symbol} />
      </div>

      {/* Trade Modal */}
      {tradeModal && (
        <TradeModal
          symbol={details.symbol}
          companyName={details.company_name}
          price={quote.price}
          currency={details.currency}
          orderType={tradeModal}
          onClose={() => setTradeModal(null)}
          onSuccess={fetchStockData}
        />
      )}

    </div>
  );
}
