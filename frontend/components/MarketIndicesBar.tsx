"use client";

import React, { useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Clock } from "lucide-react";

interface IndexData {
  symbol: string;
  name: string;
  exchange: string;
  price: number;
  change: number;
  change_percent: number;
  currency: string;
  data_status: string;
}

export function MarketIndicesBar() {
  const [indices, setIndices] = useState<IndexData[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/v1/stocks/indices")
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setIndices(data))
      .catch(() => {});
  }, []);

  if (indices.length === 0) {
    return (
      <div className="w-full h-12 bg-surface-card border-y border-border flex items-center justify-center text-xs text-txt-muted animate-pulse">
        Loading Market Indices...
      </div>
    );
  }

  return (
    <div className="w-full bg-surface-card border-y border-border overflow-x-auto py-2.5 px-4 scrollbar-none">
      <div className="max-w-7xl mx-auto flex items-center gap-6 text-xs font-numeric min-w-max">
        <div className="flex items-center gap-1.5 text-[10px] uppercase font-bold text-txt-muted border-r border-border pr-4">
          <Clock className="w-3 h-3 text-warning" />
          <span>MARKET TICKER</span>
        </div>

        {indices.map((idx) => {
          const isPositive = idx.change >= 0;
          return (
            <div key={idx.symbol} className="flex items-center gap-2">
              <span className="font-bold text-txt-primary">{idx.name}</span>
              <span className="font-mono text-txt-secondary">
                {idx.currency === "INR" ? "₹" : "$"}
                {idx.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </span>
              <div
                className={`flex items-center gap-0.5 text-[11px] font-bold px-1.5 py-0.5 rounded ${
                  isPositive
                    ? "bg-financial-profit/15 text-financial-profit"
                    : "bg-financial-loss/15 text-financial-loss"
                }`}
              >
                {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                <span>
                  {isPositive ? "+" : ""}
                  {idx.change_percent}%
                </span>
              </div>
              <span className="text-[9px] uppercase px-1 py-0.5 rounded bg-surface-elevated border border-border text-txt-muted">
                {idx.data_status}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
