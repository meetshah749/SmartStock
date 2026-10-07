"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Search, TrendingUp, TrendingDown, Clock, X } from "lucide-react";

interface SearchResult {
  symbol: string;
  company_name: string;
  exchange: string;
  price: number;
  currency: string;
  change_percent: number;
  data_status: string;
}

export function StockSearch() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setOpen(false);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/api/v1/stocks/search?q=${encodeURIComponent(query)}`);
        if (res.ok) {
          const data = await res.json();
          setResults(data);
          setOpen(true);
        }
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  // Click outside listener
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (symbol: string) => {
    setOpen(false);
    setQuery("");
    router.push(`/stocks/${symbol}`);
  };

  return (
    <div ref={dropdownRef} className="relative w-full max-w-xl">
      <div className="relative flex items-center">
        <Search className="w-4 h-4 text-txt-muted absolute left-3.5 pointer-events-none" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.trim() && setOpen(true)}
          placeholder="Search stocks by symbol, company, or sector (e.g. RELIANCE, TCS, AAPL, NVDA)..."
          className="w-full pl-10 pr-8 py-3 rounded-xl bg-surface-card border border-border text-txt-primary text-xs sm:text-sm focus:outline-none focus:border-brand-primary shadow-lg transition-colors placeholder:text-txt-muted"
        />
        {query && (
          <button
            onClick={() => setQuery("")}
            className="absolute right-3 text-txt-muted hover:text-txt-primary"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Autocomplete Dropdown */}
      {open && (
        <div className="absolute top-full left-0 right-0 mt-2 rounded-xl bg-surface-card border border-border shadow-2xl overflow-hidden z-50 max-h-80 overflow-y-auto">
          {loading ? (
            <div className="p-4 text-center text-xs text-txt-muted">Searching market quotes...</div>
          ) : results.length === 0 ? (
            <div className="p-4 text-center text-xs text-txt-muted">No stock matches found for &quot;{query}&quot;</div>
          ) : (
            <div className="divide-y divide-border/50">
              {results.map((stock) => {
                const isPositive = stock.change_percent >= 0;
                return (
                  <button
                    key={stock.symbol}
                    onClick={() => handleSelect(stock.symbol)}
                    className="w-full p-3 flex items-center justify-between hover:bg-surface-elevated text-left transition-colors font-numeric"
                  >
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-sm text-txt-primary">{stock.symbol}</span>
                        <span className="text-[10px] uppercase px-1.5 py-0.5 rounded bg-surface-main text-txt-muted border border-border">
                          {stock.exchange}
                        </span>
                      </div>
                      <span className="text-xs text-txt-muted truncate max-w-xs">{stock.company_name}</span>
                    </div>

                    <div className="flex flex-col items-end">
                      <span className="font-bold text-sm text-txt-primary">
                        {stock.currency === "INR" ? "₹" : "$"}
                        {stock.price.toFixed(2)}
                      </span>
                      <div className="flex items-center gap-1 text-xs">
                        <span
                          className={`font-semibold flex items-center ${
                            isPositive ? "text-financial-profit" : "text-financial-loss"
                          }`}
                        >
                          {isPositive ? "+" : ""}
                          {stock.change_percent}%
                        </span>
                        <span className="text-[9px] uppercase px-1 rounded bg-warning/10 text-warning font-mono">
                          {stock.data_status}
                        </span>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
