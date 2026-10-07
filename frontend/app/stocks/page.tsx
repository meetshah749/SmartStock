"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { TrendingUp, TrendingDown, ArrowUpRight, Database, Globe2 } from "lucide-react";
import { StockSearch } from "@/components/StockSearch";
import { MarketIndicesBar } from "@/components/MarketIndicesBar";

interface StockQuote {
  symbol: string;
  company_name: string;
  exchange: string;
  sector: string;
  price?: number;
  currency?: string;
  change?: number;
  change_percent?: number;
  data_status?: string;
  industry?: string;
  listing_exchanges?: string[];
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export default function ExploreStocksPage() {
  const [stocks, setStocks] = useState<StockQuote[]>([]);
  const [filterExchange, setFilterExchange] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API_URL}/api/v1/stocks/universe`).then((res) => res.ok ? res.json() : []),
      fetch(`${API_URL}/api/v1/stocks`).then((res) => res.ok ? res.json() : []),
    ])
      .then(([directory, quotes]) => {
        const quotesBySymbol = new Map((quotes as StockQuote[]).map((quote) => [quote.symbol, quote]));
        setStocks((directory as StockQuote[]).map((stock) => ({ ...stock, ...quotesBySymbol.get(stock.symbol) })));
      })
      .catch(() => setStocks([]))
      .finally(() => setLoading(false));
  }, []);

  const filteredStocks = stocks.filter((s) =>
    filterExchange === "ALL" ? true : (s.listing_exchanges || [s.exchange]).includes(filterExchange)
  );

  return (
    <div className="space-y-8">
      
      {/* Ticker Bar */}
      <MarketIndicesBar />

      {/* Hero Search Header */}
      <div className="flex flex-col items-center text-center gap-4 py-4">
        <h1 className="text-3xl font-extrabold text-txt-primary tracking-tight">Explore Stock Market Intelligence</h1>
        <p className="text-xs sm:text-sm text-txt-muted max-w-xl">
          Browse a broad directory of popular NSE/BSE companies. Use search to find additional exchange-listed shares, including international tickers; open any listing for its latest available quote and history.
        </p>

        <StockSearch />
        <div className="flex flex-wrap justify-center gap-2 text-[10px] text-txt-muted">
          <span className="inline-flex items-center gap-1 rounded-full border border-border bg-surface-card px-2.5 py-1"><Database className="h-3 w-3 text-brand-bright" /> 100+ curated Indian equities</span>
          <span className="inline-flex items-center gap-1 rounded-full border border-border bg-surface-card px-2.5 py-1"><Globe2 className="h-3 w-3 text-ai-light" /> Search provider-supported listings</span>
        </div>
      </div>

      {/* Filter Tabs & Catalog */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <div className="flex items-center gap-2">
            {["ALL", "NSE", "BSE"].map((ex) => (
              <button
                key={ex}
                onClick={() => setFilterExchange(ex)}
                className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  filterExchange === ex
                    ? "bg-brand-primary text-white shadow-md shadow-brand-primary/20"
                    : "bg-surface-card text-txt-muted hover:text-txt-primary border border-border"
                }`}
              >
                {ex === "ALL" ? "All Markets" : ex}
              </button>
            ))}
          </div>

          <span className="text-xs font-mono text-txt-muted">
            Showing {filteredStocks.length} Supported Equities
          </span>
        </div>

        {/* Stock Grid */}
        {loading ? (
          <div className="py-12 text-center text-xs text-txt-muted animate-pulse">Loading stock catalog...</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
            {filteredStocks.map((s) => {
              const isPositive = (s.change_percent ?? 0) >= 0;
              return (
                <Link
                  key={s.symbol}
                  href={`/stocks/${s.symbol}`}
                  className="p-6 rounded-2xl bg-surface-card border border-border hover:border-brand-primary transition-all duration-200 flex flex-col justify-between gap-4 group shadow-lg"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-lg text-txt-primary group-hover:text-brand-bright transition-colors">
                          {s.symbol}
                        </span>
                        <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-surface-elevated border border-border text-txt-muted">
                          {(s.listing_exchanges || [s.exchange]).filter(Boolean).join(" / ")}
                        </span>
                      </div>
                      <span className="text-xs text-txt-muted truncate max-w-[180px] block mt-0.5">
                        {s.company_name}
                      </span>
                    </div>

                    <ArrowUpRight className="w-5 h-5 text-txt-muted group-hover:text-brand-bright transition-colors" />
                  </div>

                  <div className="flex items-baseline justify-between pt-2 border-t border-border/50 font-numeric">
                    <div className="flex flex-col">
                      <span className="text-xs text-txt-muted uppercase font-semibold">Current Price</span>
                      {typeof s.price === "number" ? (
                        <span className="text-xl font-extrabold text-txt-primary">
                          {s.currency === "INR" ? "₹" : "$"}{s.price.toFixed(2)}
                        </span>
                      ) : (
                        <span className="mt-1 text-[10px] font-semibold text-brand-bright">Open for live quote</span>
                      )}
                    </div>

                    <div className="flex flex-col items-end">
                      <span className="text-xs text-txt-muted uppercase font-semibold">24h Change</span>
                      <div
                        className={`flex items-center gap-1 text-sm font-bold ${
                          (s.change_percent ?? 0) >= 0 ? "text-financial-profit" : "text-financial-loss"
                        }`}
                      >
                        {typeof s.change_percent === "number" ? (
                          <>
                            {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                            <span>{isPositive ? "+" : ""}{s.change_percent}%</span>
                          </>
                        ) : <span className="text-txt-muted">Quote on open</span>}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[10px] font-mono text-txt-muted pt-1">
                    <span>Sector: {s.sector}</span>
                    <span className="px-1.5 py-0.5 rounded bg-warning/10 text-warning border border-warning/20">
                      {s.data_status || "QUOTE ON DEMAND"}
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
}
