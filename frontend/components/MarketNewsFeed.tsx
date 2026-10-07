"use client";

import React, { useEffect, useState } from "react";
import { Newspaper, ExternalLink, TrendingUp, TrendingDown, Minus, RefreshCw, Filter } from "lucide-react";

interface NewsArticle {
  id: string;
  title: string;
  publisher: string;
  published_at: string;
  summary: string;
  url: string;
  ticker_symbol: string;
  category: string;
  sentiment: "BULLISH" | "BEARISH" | "NEUTRAL";
  sentiment_score: number;
}

export function MarketNewsFeed({ tickerSymbol }: { tickerSymbol?: string }) {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");

  const fetchNews = async () => {
    setLoading(true);
    try {
      const endpoint = tickerSymbol
        ? `http://localhost:8000/api/v1/stocks/${tickerSymbol}/news`
        : `http://localhost:8000/api/v1/news`;
      const res = await fetch(endpoint);
      if (res.ok) {
        setArticles(await res.json());
      }
    } catch {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNews();
  }, [tickerSymbol]);

  const categories = ["ALL", "CORPORATE", "TECH", "EARNINGS", "MACRO", "GLOBAL", "MARKET"];

  const filteredArticles =
    selectedCategory === "ALL"
      ? articles
      : articles.filter((a) => a.category.toUpperCase() === selectedCategory);

  return (
    <div className="p-6 rounded-2xl bg-surface-card border border-border space-y-6 shadow-xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-primary/10 text-brand-bright flex items-center justify-center">
            <Newspaper className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-txt-primary">
              {tickerSymbol ? `${tickerSymbol} Market News & Sentiment` : "Financial News & Sentiment Engine"}
            </h3>
            <p className="text-xs text-txt-muted">Real-time market headlines with AI sentiment classification</p>
          </div>
        </div>

        <button
          onClick={fetchNews}
          className="p-2 rounded-lg bg-surface-main border border-border hover:border-brand-primary text-txt-muted hover:text-txt-primary transition-colors text-xs font-semibold flex items-center gap-1.5"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh News
        </button>
      </div>

      {/* Category Filters */}
      {!tickerSymbol && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
          <Filter className="w-3.5 h-3.5 text-txt-muted shrink-0" />
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded-lg font-semibold uppercase tracking-wider text-[11px] whitespace-nowrap transition-colors ${
                selectedCategory === cat
                  ? "bg-brand-primary text-white"
                  : "bg-surface-main text-txt-muted hover:text-txt-primary border border-border"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      )}

      {/* Articles Stream */}
      {loading ? (
        <div className="py-8 text-center text-xs text-txt-muted">
          <RefreshCw className="w-5 h-5 text-brand-bright animate-spin mx-auto mb-2" />
          Fetching latest financial news...
        </div>
      ) : filteredArticles.length === 0 ? (
        <div className="py-8 text-center text-xs text-txt-muted">No news articles found for this category.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredArticles.map((article) => {
            const isBullish = article.sentiment === "BULLISH";
            const isBearish = article.sentiment === "BEARISH";

            return (
              <div
                key={article.id}
                className="p-4 rounded-xl bg-surface-main/80 border border-border/70 hover:border-brand-primary transition-all flex flex-col justify-between gap-3 group"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] uppercase font-extrabold px-2 py-0.5 rounded bg-surface-card border border-border text-brand-bright">
                      {article.ticker_symbol}
                    </span>

                    <span
                      className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded flex items-center gap-1 ${
                        isBullish
                          ? "bg-financial-profit/20 text-financial-profit border border-financial-profit/30"
                          : isBearish
                          ? "bg-financial-loss/20 text-financial-loss border border-financial-loss/30"
                          : "bg-surface-card text-txt-muted border border-border"
                      }`}
                    >
                      {isBullish ? <TrendingUp className="w-3 h-3" /> : isBearish ? <TrendingDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
                      {article.sentiment}
                    </span>
                  </div>

                  <h4 className="font-bold text-xs text-txt-primary group-hover:text-brand-bright transition-colors line-clamp-2">
                    {article.title}
                  </h4>

                  <p className="text-[11px] text-txt-muted line-clamp-2 leading-relaxed">{article.summary}</p>
                </div>

                <div className="flex items-center justify-between text-[10px] text-txt-muted pt-2 border-t border-border/40">
                  <span className="font-semibold text-txt-secondary">{article.publisher}</span>
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-brand-bright hover:underline font-bold"
                  >
                    Read Full Article <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
