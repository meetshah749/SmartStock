"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Mail, CheckCircle2, AlertCircle, ArrowRight } from "lucide-react";
import { useAuth } from "@/lib/auth";

export default function VerifyEmailPage() {
  const { user } = useAuth();
  const [code, setCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setSubmitting(true);

    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/verify-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: user?.email, code }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Verification failed");
      }

      const data = await res.json();
      setMessage(data.message);
    } catch (err: any) {
      setError(err.message || "Failed to verify code");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto my-12 p-8 rounded-2xl bg-surface-card border border-border shadow-2xl relative overflow-hidden">
      <div className="flex flex-col items-center text-center gap-2 mb-8">
        <div className="w-12 h-12 rounded-xl bg-brand-primary/10 text-brand-bright flex items-center justify-center mb-2">
          <Mail className="w-6 h-6" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-txt-primary">Verify Email Address</h1>
        <p className="text-xs text-txt-muted">
          Enter the 6-digit verification code sent to <strong className="text-txt-primary">{user?.email || "your registered email"}</strong>.
        </p>
      </div>

      {message && (
        <div className="p-4 mb-6 rounded-lg bg-financial-profit/10 border border-financial-profit/30 text-financial-profit text-xs flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {error && (
        <div className="p-3 mb-6 rounded-lg bg-financial-loss/10 border border-financial-loss/30 text-financial-loss text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-txt-secondary mb-1">6-Digit Code</label>
          <input
            type="text"
            required
            maxLength={6}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="123456"
            className="w-full px-3.5 py-3 rounded-lg bg-surface-main border border-border text-txt-primary text-center font-mono text-xl tracking-widest focus:outline-none focus:border-brand-primary transition-colors"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-3 rounded-xl bg-brand-primary hover:bg-brand-bright text-white font-bold text-sm shadow-lg shadow-brand-primary/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {submitting ? "Verifying..." : "Confirm Verification"}
        </button>
      </form>

      <div className="mt-6 pt-6 border-t border-border/50 text-center text-xs text-txt-muted">
        <Link href="/" className="font-bold text-brand-bright hover:underline">
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
}
