"use client";

import React, { FormEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Bot, ChevronDown, MessageCircle, RotateCcw, Send, ShieldCheck, Sparkles, TrendingUp, UserRound, X } from "lucide-react";

type RiskProfile = "conservative" | "balanced" | "growth";
type Horizon = "short" | "medium" | "long";
type Role = "user" | "assistant";

interface StockSnapshot {
  symbol: string;
  company_name: string;
  description?: string | null;
  exchange?: string | null;
  sector?: string | null;
  industry?: string | null;
  price: number;
  currency: string;
  change_percent: number;
  open?: number | null;
  high?: number | null;
  low?: number | null;
  prev_close?: number | null;
  volume?: number | null;
  rsi_14?: number | null;
  sma20?: number | null;
  sma50?: number | null;
  one_month_change_percent: number | null;
  one_year_change_percent?: number | null;
  observed_one_year_high?: number | null;
  observed_one_year_low?: number | null;
  history_points?: number;
  annual_history_points?: number;
  timestamp?: string | null;
  market_status?: string | null;
  daily_volatility_percent?: number | null;
  fundamentals?: {
    metrics?: Record<string, number | null>;
    source?: string;
    retrieved_at?: string;
  } | null;
  volatility_band: string;
  data_status: string;
  source: string;
}

interface StockComparison {
  period: string;
  one_month_performance_leader: string | null;
  one_year_performance_leader: string | null;
  lower_observed_volatility: string | null;
  note: string;
}

interface ChatMessage {
  role: Role;
  content: string;
  stocks?: StockSnapshot[];
  comparison?: StockComparison | null;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const starters = [
  "Explain RSI in simple terms",
  "What should I know about TCS?",
  "Compare RELIANCE and INFY",
];

function readableApiError(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    const messages = value.map((item) => {
      if (typeof item === "string") return item;
      if (item && typeof item === "object") {
        const record = item as Record<string, unknown>;
        const path = Array.isArray(record.loc) ? record.loc.filter((part) => part !== "body").join(" → ") : "";
        const message = typeof record.msg === "string" ? record.msg : typeof record.message === "string" ? record.message : "Invalid request";
        return path ? `${path}: ${message}` : message;
      }
      return "Invalid request";
    });
    return messages.filter(Boolean).join("; ");
  }
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    for (const key of ["detail", "message", "error_description", "error"]) {
      if (record[key] !== undefined && record[key] !== value) {
        const message = readableApiError(record[key]);
        if (message) return message;
      }
    }
    try {
      return JSON.stringify(value);
    } catch {
      return "The server returned an unreadable error.";
    }
  }
  return "The server returned an unexpected response.";
}

export function StockAssistant() {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [llmConfigured, setLlmConfigured] = useState<boolean | null>(null);
  const [riskProfile, setRiskProfile] = useState<RiskProfile | null>(null);
  const [horizon, setHorizon] = useState<Horizon | "">("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Hi! Ask me about stocks, markets, or general topics. I can use SmartStock's available quotes and history for supported tickers; broad open-ended answers use the configured AI model when enabled. Choose a risk lens if you want an educational discussion framed around your stated preference.",
    },
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading, open]);

  const askAssistant = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    const history = messages.map(({ role, content }) => ({ role, content }));
    setMessages((current) => [...current, { role: "user", content: trimmed }]);
    setDraft("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/v1/assistant/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: trimmed,
          conversation: history.slice(-8),
          risk_profile: riskProfile,
          investment_horizon: horizon || null,
        }),
      });
      const responseText = await response.text();
      let payload: Record<string, unknown> = {};
      if (responseText) {
        try {
          payload = JSON.parse(responseText) as Record<string, unknown>;
        } catch {
          payload = { detail: responseText };
        }
      }
      if (!response.ok) {
        throw new Error(readableApiError(payload.detail ?? payload));
      }
      if (typeof payload.reply !== "string" || !payload.reply.trim()) {
        throw new Error("The assistant returned an empty reply. Please try again.");
      }
      setLlmConfigured(Boolean(payload.llm_configured));
      setMessages((current) => [...current, {
        role: "assistant",
        content: payload.reply as string,
        stocks: Array.isArray(payload.stocks) ? payload.stocks as StockSnapshot[] : [],
        comparison: payload.comparison && typeof payload.comparison === "object" ? payload.comparison as StockComparison : null,
      }]);
    } catch (error) {
      const message = error instanceof Error ? error.message : readableApiError(error);
      setMessages((current) => [...current, {
        role: "assistant",
        content: `${message} Please check the backend connection and try again.`,
      }]);
    } finally {
      setLoading(false);
    }
  };

  const submitMessage = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void askAssistant(draft);
  };

  const clearConversation = () => {
    setMessages([{
      role: "assistant",
      content: "Conversation cleared. What stock or market concept can I help you explore?",
    }]);
  };

  return (
    <div className="fixed bottom-5 right-5 z-[70] flex flex-col items-end gap-3">
      {open && (
        <section
          aria-label="SmartStock AI assistant"
          className="flex h-[min(680px,calc(100dvh-6rem))] w-[min(410px,calc(100vw-2rem))] flex-col overflow-hidden rounded-2xl border border-border bg-surface-main shadow-2xl shadow-black/40"
        >
          <header className="flex items-center justify-between border-b border-border bg-gradient-to-r from-surface-card to-surface-elevated px-4 py-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-ai-violet/30 bg-ai-violet/15 text-ai-light">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-sm font-extrabold text-txt-primary">SmartStock Assistant</h2>
                <p className="flex items-center gap-1.5 text-[10px] text-txt-muted">
                  <span className={`h-1.5 w-1.5 rounded-full ${llmConfigured ? "bg-financial-profit" : "bg-warning"}`} />
                  {llmConfigured === null ? "Stock & general questions" : llmConfigured ? "General AI · live stock context" : "Stock help · basic mode"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={clearConversation}
                aria-label="Clear conversation"
                title="Clear conversation"
                className="rounded-lg p-2 text-txt-muted transition hover:bg-surface-main hover:text-txt-primary"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close assistant"
                className="rounded-lg p-2 text-txt-muted transition hover:bg-surface-main hover:text-txt-primary"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </header>

          <div className="border-b border-border bg-surface-card/70 px-4 py-3">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-txt-muted">Risk lens (optional)</span>
              <select
                aria-label="Investment time horizon"
                value={horizon}
                onChange={(event) => setHorizon(event.target.value as Horizon | "")}
                className="max-w-[145px] rounded-lg border border-border bg-surface-elevated px-2 py-1.5 text-[10px] font-semibold text-txt-secondary outline-none focus:border-brand-primary"
              >
                <option value="">Time horizon</option>
                <option value="short">Under 1 year</option>
                <option value="medium">1–5 years</option>
                <option value="long">Over 5 years</option>
              </select>
            </div>
            <div className="mt-2 grid grid-cols-3 gap-1.5">
              {(["conservative", "balanced", "growth"] as const).map((profile) => (
                <button
                  key={profile}
                  type="button"
                  aria-pressed={riskProfile === profile}
                  onClick={() => setRiskProfile((current) => current === profile ? null : profile)}
                  className={`rounded-lg border px-2 py-1.5 text-[10px] font-bold capitalize transition ${
                    riskProfile === profile
                      ? "border-ai-violet/50 bg-ai-violet/15 text-ai-light"
                      : "border-border bg-surface-main text-txt-muted hover:text-txt-primary"
                  }`}
                >
                  {profile}
                </button>
              ))}
            </div>
            {llmConfigured === false && (
              <p className="mt-2 rounded-lg border border-warning/25 bg-warning/5 px-2.5 py-2 text-[10px] leading-relaxed text-txt-muted">
                Broad open-ended answers need a model provider. Add a server-side AI_API_KEY to enable general AI chat; stock explanations and supported market-data lookups still work here.
              </p>
            )}
          </div>

          <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
            {messages.map((message, index) => (
              <div key={`${index}-${message.role}`} className={`flex items-start gap-2.5 ${message.role === "user" ? "flex-row-reverse" : ""}`}>
                <div className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${
                  message.role === "assistant" ? "bg-ai-violet/15 text-ai-light" : "bg-brand-primary/15 text-brand-bright"
                }`}>
                  {message.role === "assistant" ? <Bot className="h-4 w-4" /> : <UserRound className="h-4 w-4" />}
                </div>
                <div className={`max-w-[84%] space-y-2 ${message.role === "user" ? "items-end" : "items-start"}`}>
                  <div className={`rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed ${
                    message.role === "assistant"
                      ? "rounded-tl-md border border-border bg-surface-card text-txt-secondary"
                      : "rounded-tr-md bg-brand-primary text-white"
                  }`}>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                  {message.stocks && message.stocks.length > 0 && (
                    <div className="grid w-full gap-2 sm:grid-cols-2">
                      {message.stocks.map((stock) => (
                        <div key={stock.symbol} className="rounded-xl border border-border bg-surface-card p-3">
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <span className="text-xs font-extrabold text-txt-primary">{stock.symbol}</span>
                              <p className="mt-0.5 text-[9px] leading-snug text-txt-muted">{stock.company_name}</p>
                            </div>
                            <span className={`shrink-0 text-[9px] font-bold ${stock.change_percent >= 0 ? "text-financial-profit" : "text-financial-loss"}`}>
                              {stock.change_percent >= 0 ? "+" : ""}{stock.change_percent.toFixed(2)}%
                            </span>
                          </div>
                          <p className="mt-2 text-base font-extrabold text-txt-primary">
                            {stock.currency === "INR" ? "₹" : "$"}{stock.price.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </p>
                          <p className="text-[9px] text-txt-muted">{stock.exchange} · {stock.sector} · {stock.data_status}</p>
                          {stock.description && <p className="mt-2 line-clamp-3 text-[9px] leading-relaxed text-txt-secondary">{stock.description}</p>}
                          {stock.fundamentals?.metrics && Object.keys(stock.fundamentals.metrics).length > 0 && (
                            <div className="mt-2 rounded-lg border border-border bg-surface-main p-2">
                              <p className="mb-1 text-[9px] font-extrabold uppercase tracking-wide text-ai-light">Available fundamentals</p>
                              <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[9px]">
                                {Object.entries(stock.fundamentals.metrics).map(([key, value]) => {
                                  if (value == null) return null;
                                  const label = key.replaceAll("_", " ");
                                  const isPercent = ["dividend_yield", "revenue_growth", "profit_margin", "return_on_equity"].includes(key);
                                  const isMoney = ["market_cap", "revenue", "net_income"].includes(key);
                                  const formatted = isPercent
                                    ? `${(value * 100).toFixed(2)}%`
                                    : isMoney
                                      ? `${stock.currency} ${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`
                                      : value.toLocaleString("en-IN", { maximumFractionDigits: 2 });
                                  return (
                                    <React.Fragment key={key}>
                                      <span className="capitalize text-txt-muted">{label}</span>
                                      <span className="text-right font-semibold text-txt-secondary">{formatted}</span>
                                    </React.Fragment>
                                  );
                                })}
                              </div>
                              {stock.fundamentals.source && <p className="mt-1 text-[8px] text-txt-muted">Provider: {stock.fundamentals.source}</p>}
                            </div>
                          )}
                          <div className="mt-2 grid grid-cols-2 gap-x-2 gap-y-1 border-t border-border pt-2 text-[9px]">
                            <span className="text-txt-muted">1M return</span>
                            <span className="text-right font-semibold text-txt-secondary">{stock.one_month_change_percent == null ? "—" : `${stock.one_month_change_percent > 0 ? "+" : ""}${stock.one_month_change_percent.toFixed(2)}%`}</span>
                            <span className="text-txt-muted">1Y return</span>
                            <span className="text-right font-semibold text-txt-secondary">{stock.one_year_change_percent == null ? "—" : `${stock.one_year_change_percent > 0 ? "+" : ""}${stock.one_year_change_percent.toFixed(2)}%`}</span>
                            <span className="text-txt-muted">1Y close range</span>
                            <span className="text-right font-semibold text-txt-secondary">{stock.observed_one_year_low == null || stock.observed_one_year_high == null ? "—" : `${stock.observed_one_year_low.toFixed(2)}–${stock.observed_one_year_high.toFixed(2)}`}</span>
                            <span className="text-txt-muted">Day range · open</span>
                            <span className="text-right font-semibold text-txt-secondary">{stock.low == null || stock.high == null || stock.open == null ? "—" : `${stock.low.toFixed(2)}–${stock.high.toFixed(2)} · ${stock.open.toFixed(2)}`}</span>
                            <span className="text-txt-muted">RSI-14 · SMA20 / SMA50</span>
                            <span className="text-right font-semibold text-txt-secondary">{stock.rsi_14 == null ? "—" : stock.rsi_14.toFixed(1)} · {stock.sma20 == null ? "—" : stock.sma20.toFixed(2)} / {stock.sma50 == null ? "—" : stock.sma50.toFixed(2)}</span>
                            <span className="text-txt-muted">Volatility</span>
                            <span className="text-right font-semibold text-txt-secondary">{stock.daily_volatility_percent == null ? stock.volatility_band : `${stock.daily_volatility_percent.toFixed(2)}% · ${stock.volatility_band}`}</span>
                            <span className="text-txt-muted">Volume</span>
                            <span className="text-right font-semibold text-txt-secondary">{stock.volume == null ? "—" : stock.volume.toLocaleString("en-IN")}</span>
                          </div>
                          <Link href={`/stocks/${stock.symbol}`} className="mt-2 inline-flex text-[9px] font-bold text-brand-bright hover:underline">
                            Open full {stock.symbol} dashboard →
                          </Link>
                          <p className="mt-2 text-[8px] leading-relaxed text-txt-muted">Source: {stock.source}{stock.timestamp ? ` · ${new Date(stock.timestamp).toLocaleString()}` : ""}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {message.comparison && (
                    <div className="w-full rounded-xl border border-brand-primary/25 bg-brand-primary/5 p-3">
                      <p className="text-[10px] font-extrabold uppercase tracking-wide text-brand-bright">Side-by-side · {message.comparison.period}</p>
                      <div className="mt-2 grid grid-cols-1 gap-1.5 text-[10px] text-txt-secondary">
                        <p>Stronger observed 1M return: <strong className="text-txt-primary">{message.comparison.one_month_performance_leader || "Insufficient data"}</strong></p>
                        <p>Stronger observed 1Y return: <strong className="text-txt-primary">{message.comparison.one_year_performance_leader || "Insufficient data"}</strong></p>
                        <p>Lower observed volatility: <strong className="text-txt-primary">{message.comparison.lower_observed_volatility || "Insufficient data"}</strong></p>
                      </div>
                      <p className="mt-2 text-[9px] leading-relaxed text-txt-muted">{message.comparison.note}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {messages.length === 1 && !loading && (
              <div className="space-y-2 pl-9">
                <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-txt-muted">Try asking</p>
                <div className="flex flex-wrap gap-2">
                  {starters.map((starter) => (
                    <button
                      key={starter}
                      type="button"
                      onClick={() => void askAssistant(starter)}
                      className="rounded-full border border-border bg-surface-card px-2.5 py-1.5 text-[10px] font-medium text-txt-secondary transition hover:border-ai-violet/50 hover:text-ai-light"
                    >
                      {starter}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {loading && (
              <div className="flex items-center gap-2 pl-9 text-[11px] text-txt-muted">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ai-light" /> Checking available market context…
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="border-t border-border bg-surface-card/70 p-3">
            <form onSubmit={submitMessage} className="flex items-end gap-2 rounded-xl border border-border bg-surface-main p-2 focus-within:border-brand-primary">
              <textarea
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    void askAssistant(draft);
                  }
                }}
                rows={1}
                maxLength={1000}
                placeholder="Ask about a stock or market term…"
                aria-label="Your question"
                className="max-h-24 min-h-9 flex-1 resize-none bg-transparent px-2 py-2 text-xs text-txt-primary outline-none placeholder:text-txt-muted"
              />
              <button
                type="submit"
                disabled={loading || !draft.trim()}
                aria-label="Send message"
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-primary text-white transition hover:bg-brand-bright disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
            <p className="mt-2 flex items-center justify-center gap-1 text-center text-[9px] leading-relaxed text-txt-muted">
              <ShieldCheck className="h-3 w-3 shrink-0" /> Educational only. Not personalized financial advice.
            </p>
          </div>
        </section>
      )}

      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        aria-label={open ? "Close SmartStock assistant" : "Open SmartStock assistant"}
        aria-expanded={open}
        className="group flex h-14 items-center gap-2.5 rounded-full border border-ai-violet/40 bg-gradient-to-r from-brand-primary to-ai-violet px-4 text-white shadow-xl shadow-ai-violet/30 transition hover:-translate-y-0.5 hover:shadow-ai-violet/45"
      >
        {open ? <ChevronDown className="h-5 w-5" /> : <MessageCircle className="h-5 w-5 transition group-hover:scale-110" />}
        <span className="text-xs font-extrabold">Ask SmartStock AI</span>
      </button>
    </div>
  );
}
