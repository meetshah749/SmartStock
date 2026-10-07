"use client";

import React, { useState } from "react";
import { X, Wallet, ShieldCheck, AlertCircle, CheckCircle2, ArrowRight } from "lucide-react";
import { useAuth } from "@/lib/auth";

interface TradeModalProps {
  symbol: string;
  companyName: string;
  price: number;
  currency: string;
  orderType: "buy" | "sell";
  onClose: () => void;
  onSuccess: () => void;
}

export function TradeModal({
  symbol,
  companyName,
  price,
  currency,
  orderType,
  onClose,
  onSuccess,
}: TradeModalProps) {
  const { user, accessToken, refreshSession } = useAuth();
  const [quantity, setQuantity] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execPricePaise = Math.round(price * 100);
  const totalAmountRupees = price * quantity;
  const totalAmountPaise = execPricePaise * quantity;

  const availablePaise = user?.wallet_balance_paise || 50000;
  const hasSufficientBalance =
    orderType === "buy" ? availablePaise >= totalAmountPaise : true;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!accessToken) {
      setError("Please log in to execute virtual trades");
      return;
    }

    if (orderType === "buy" && !hasSufficientBalance) {
      setError("Insufficient virtual wallet balance to place this order.");
      return;
    }

    setSubmitting(true);

    try {
      const endpoint = `http://localhost:8000/api/v1/orders/${orderType}`;
      const res = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ symbol, quantity }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Trade execution failed");
      }

      await refreshSession();
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to execute order");
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-md p-6 rounded-2xl bg-surface-card border border-border shadow-2xl space-y-4 relative overflow-hidden">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-border/50 pb-3">
          <div className="flex items-center gap-2">
            <span
              className={`text-sm font-extrabold uppercase px-2.5 py-0.5 rounded ${
                orderType === "buy"
                  ? "bg-financial-profit/20 text-financial-profit"
                  : "bg-financial-loss/20 text-financial-loss"
              }`}
            >
              VIRTUAL {orderType.toUpperCase()}
            </span>
            <span className="text-sm font-extrabold text-txt-primary">{symbol}</span>
          </div>

          <button onClick={onClose} className="text-txt-muted hover:text-txt-primary">
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-financial-loss/10 border border-financial-loss/30 text-financial-loss text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Demo Balance Bar */}
        <div className="p-3 rounded-xl bg-surface-elevated border border-border flex items-center justify-between text-xs font-numeric">
          <div className="flex items-center gap-2 text-txt-muted">
            <Wallet className="w-4 h-4 text-financial-profit" />
            <span>Available Balance:</span>
          </div>
          <span className="font-bold text-financial-profit">
            ₹{(availablePaise / 100).toFixed(2)}
          </span>
        </div>

        {/* Order Details Form */}
        <form onSubmit={handleSubmit} className="space-y-4 font-numeric">
          <div className="space-y-1">
            <span className="text-xs text-txt-muted font-medium">{companyName}</span>
            <div className="flex justify-between items-baseline text-xs text-txt-secondary">
              <span>Market Price:</span>
              <span className="font-bold text-txt-primary">
                {currency === "INR" ? "₹" : "$"}{price.toFixed(2)}
              </span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-txt-secondary mb-1">Quantity of Shares</label>
            <input
              type="number"
              min={1}
              max={1000}
              required
              value={quantity}
              onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
              className="w-full px-3.5 py-2.5 rounded-lg bg-surface-main border border-border text-txt-primary font-bold text-sm focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div className="p-3.5 rounded-xl bg-surface-main border border-border/80 space-y-1.5 text-xs">
            <div className="flex justify-between text-txt-secondary">
              <span>Estimated Order Value:</span>
              <span className="font-bold text-txt-primary">
                {currency === "INR" ? "₹" : "$"}{totalAmountRupees.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between text-[11px] text-txt-muted font-mono">
              <span>Paise Accounting:</span>
              <span>{totalAmountPaise.toLocaleString()} Paise</span>
            </div>
          </div>

          {/* Legal Compliance Banner */}
          <div className="p-3 rounded-lg bg-brand-primary/10 border border-brand-primary/20 text-[11px] text-brand-bright flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 shrink-0" />
            <span>SIMULATED VIRTUAL ORDER — NOT A REAL EXCHANGE TRADE</span>
          </div>

          <button
            type="submit"
            disabled={submitting || (orderType === "buy" && !hasSufficientBalance)}
            className={`w-full py-3 rounded-xl text-white font-extrabold text-sm shadow-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50 ${
              orderType === "buy"
                ? "bg-financial-profit hover:bg-financial-profitLight shadow-financial-profit/25"
                : "bg-financial-loss hover:bg-financial-lossLight shadow-financial-loss/25"
            }`}
          >
            {submitting ? "Executing Order..." : `Confirm Virtual ${orderType.toUpperCase()}`}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

      </div>
    </div>
  );
}
