"use client";

import React, { useEffect, useState } from "react";
import { Sparkles, TrendingUp, TrendingDown, Minus, Info, AlertTriangle, ShieldAlert, Target, RefreshCw } from "lucide-react";

interface FeatureAttribution {
  name: string;
  impact: string;
  direction: "BULLISH" | "BEARISH" | "NEUTRAL";
  description: string;
}

interface AIPredictionPayload {
  symbol: string;
  current_price: number;
  signal: "BULLISH" | "BEARISH" | "NEUTRAL";
  confidence_percent: number;
  score: number;
  technical_indicators: {
    rsi_14: number;
    sma_20: number;
    sma_50: number;
    momentum_5d_percent: number;
    volatility_percent: number;
  };
  price_targets: {
    target_1d: number;
    target_5d: number;
    target_30d: number;
  };
  feature_attributions: FeatureAttribution[];
  disclaimer: string;
  generated_at: string;
}

export function AIPredictionCard({ symbol }: { symbol: string }) {
  const [prediction, setPrediction] = useState<AIPredictionPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedHorizon, setSelectedHorizon] = useState<"1d" | "5d" | "30d">("5d");

  const fetchPrediction = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/stocks/${symbol}/prediction`);
      if (!res.ok) throw new Error("Could not load AI prediction model.");
      const data = await res.json();
      setPrediction(data);
    } catch (err: any) {
      setError(err.message || "Failed to load prediction.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrediction();
  }, [symbol]);

  if (loading) {
    return (
      <div className="p-6 rounded-2xl bg-surface-card border border-border flex items-center justify-center gap-3">
        <RefreshCw className="w-5 h-5 text-ai-light animate-spin" />
        <span className="text-xs font-semibold text-txt-muted">Running Quant ML Prediction Model...</span>
      </div>
    );
  }

  if (error || !prediction) {
    return (
      <div className="p-4 rounded-2xl bg-surface-card border border-border text-xs text-txt-muted text-center">
        <span>AI prediction currently offline for {symbol}.</span>
      </div>
    );
  }

  const isBullish = prediction.signal === "BULLISH";
  const isBearish = prediction.signal === "BEARISH";

  const targetPrice =
    selectedHorizon === "1d"
      ? prediction.price_targets.target_1d
      : selectedHorizon === "5d"
      ? prediction.price_targets.target_5d
      : prediction.price_targets.target_30d;

  const pctDiff = (((targetPrice - prediction.current_price) / prediction.current_price) * 100).toFixed(2);

  return (
    <div className="p-6 rounded-2xl bg-gradient-to-br from-surface-card via-surface-elevated to-surface-card border border-ai-violet/30 shadow-2xl relative overflow-hidden space-y-6">
      <div className="absolute top-0 right-0 w-48 h-48 bg-ai-violet/10 rounded-full blur-3xl pointer-events-none" />

      {/* Card Header Identity */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-ai-violet/20 border border-ai-violet/40 flex items-center justify-center text-ai-light">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-base text-txt-primary">SmartStock AI Prediction Engine</h3>
              <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded bg-ai-violet/20 text-ai-light border border-ai-violet/30">
                XAI MODEL
              </span>
            </div>
            <p className="text-[11px] text-txt-muted">Quantitative Machine Learning Signal & Feature Attribution Breakdown</p>
          </div>
        </div>

        <button
          onClick={fetchPrediction}
          className="p-2 rounded-lg bg-surface-main border border-border hover:border-brand-primary text-txt-muted hover:text-txt-primary transition-colors"
          title="Recalculate AI Prediction"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Signal Badge & Confidence Meter Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Signal Direction Badge */}
        <div
          className={`p-4 rounded-xl border flex flex-col justify-between gap-2 ${
            isBullish
              ? "bg-financial-profit/10 border-financial-profit/30 text-financial-profit"
              : isBearish
              ? "bg-financial-loss/10 border-financial-loss/30 text-financial-loss"
              : "bg-surface-main border-border text-txt-secondary"
          }`}
        >
          <span className="text-[11px] font-bold uppercase tracking-wider opacity-80">Predicted Direction</span>
          <div className="flex items-center gap-2 text-xl font-extrabold">
            {isBullish ? (
              <TrendingUp className="w-6 h-6" />
            ) : isBearish ? (
              <TrendingDown className="w-6 h-6" />
            ) : (
              <Minus className="w-6 h-6" />
            )}
            <span>{prediction.signal}</span>
          </div>
          <span className="text-[10px] opacity-75">Based on multi-factor technical indicators</span>
        </div>

        {/* Model Confidence Meter */}
        <div className="p-4 rounded-xl bg-surface-main border border-border flex flex-col justify-between gap-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-txt-muted">Model Confidence</span>
            <span className="text-xs font-bold text-brand-bright">{prediction.confidence_percent}%</span>
          </div>
          <div className="w-full bg-surface-card h-2.5 rounded-full overflow-hidden border border-border/50">
            <div
              className="bg-gradient-to-r from-brand-primary to-ai-light h-full rounded-full transition-all duration-500"
              style={{ width: `${prediction.confidence_percent}%` }}
            />
          </div>
          <span className="text-[10px] text-txt-muted">Statistical probability index</span>
        </div>

        {/* Price Target Projection */}
        <div className="p-4 rounded-xl bg-surface-main border border-border flex flex-col justify-between gap-2 font-numeric">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-txt-muted">Target Horizon</span>
            <div className="flex gap-1 text-[10px] font-bold">
              {(["1d", "5d", "30d"] as const).map((h) => (
                <button
                  key={h}
                  onClick={() => setSelectedHorizon(h)}
                  className={`px-1.5 py-0.5 rounded uppercase transition-colors ${
                    selectedHorizon === h ? "bg-brand-primary text-white" : "bg-surface-card text-txt-muted hover:text-txt-primary"
                  }`}
                >
                  {h}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-xl font-extrabold text-txt-primary">₹{targetPrice.toLocaleString("en-IN")}</span>
            <span className={`text-xs font-bold ${Number(pctDiff) >= 0 ? "text-financial-profit" : "text-financial-loss"}`}>
              {Number(pctDiff) >= 0 ? "+" : ""}{pctDiff}%
            </span>
          </div>
          <span className="text-[10px] text-txt-muted">Estimated baseline target price</span>
        </div>
      </div>

      {/* Explainable AI (XAI) Feature Importance Attributions */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold text-txt-primary uppercase tracking-wider flex items-center gap-1.5">
          <Target className="w-4 h-4 text-ai-violet" /> Key Technical Drivers & Feature Importance
        </h4>

        <div className="space-y-2">
          {prediction.feature_attributions.map((factor, idx) => (
            <div key={idx} className="p-3 rounded-xl bg-surface-main/80 border border-border/60 flex flex-col gap-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-txt-primary">{factor.name}</span>
                <span
                  className={`font-mono font-bold px-1.5 py-0.5 rounded text-[10px] ${
                    factor.direction === "BULLISH"
                      ? "bg-financial-profit/20 text-financial-profit"
                      : factor.direction === "BEARISH"
                      ? "bg-financial-loss/20 text-financial-loss"
                      : "bg-surface-card text-txt-muted"
                  }`}
                >
                  {factor.impact}
                </span>
              </div>
              <p className="text-[11px] text-txt-muted">{factor.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Regulatory Legal Disclaimer */}
      <div className="p-3 rounded-xl bg-warning/10 border border-warning/30 text-warning text-[11px] flex items-start gap-2">
        <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
        <span>{prediction.disclaimer}</span>
      </div>
    </div>
  );
}
