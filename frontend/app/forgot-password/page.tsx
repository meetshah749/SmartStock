"use client";

import React, { useState } from "react";
import Link from "next/link";
import { KeyRound, CheckCircle2, AlertCircle, ArrowRight } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [devToken, setDevToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setDevToken(null);
    setSubmitting(true);

    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Request failed");
      }

      const data = await res.json();
      setMessage(data.message);
      if (data.dev_reset_token) {
        setDevToken(data.dev_reset_token);
      }
    } catch (err: any) {
      setError(err.message || "Failed to process forgot password request");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto my-12 p-8 rounded-2xl bg-surface-card border border-border shadow-2xl relative overflow-hidden">
      <div className="flex flex-col items-center text-center gap-2 mb-8">
        <div className="w-12 h-12 rounded-xl bg-brand-primary/10 text-brand-bright flex items-center justify-center mb-2">
          <KeyRound className="w-6 h-6" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-txt-primary">Recover Password</h1>
        <p className="text-xs text-txt-muted">Enter your registered email address to receive password reset instructions.</p>
      </div>

      {message && (
        <div className="p-4 mb-6 rounded-lg bg-financial-profit/10 border border-financial-profit/30 text-financial-profit text-xs flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {devToken && (
        <div className="p-3 mb-6 rounded-lg bg-ai-violet/10 border border-ai-violet/30 text-xs flex flex-col gap-2">
          <span className="font-bold text-ai-light">Development Reset Link Token:</span>
          <code className="p-2 rounded bg-surface-main text-brand-bright text-[11px] font-mono break-all">{devToken}</code>
          <Link
            href={`/reset-password?token=${devToken}`}
            className="text-xs font-bold text-brand-bright hover:underline inline-flex items-center gap-1"
          >
            Proceed to Reset Password Page <ArrowRight className="w-3.5 h-3.5" />
          </Link>
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
          <label className="block text-xs font-semibold text-txt-secondary mb-1">Email Address</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="trader@example.com"
            className="w-full px-3.5 py-2.5 rounded-lg bg-surface-main border border-border text-txt-primary text-sm focus:outline-none focus:border-brand-primary transition-colors"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-3 rounded-xl bg-brand-primary hover:bg-brand-bright text-white font-bold text-sm shadow-lg shadow-brand-primary/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {submitting ? "Sending..." : "Send Reset Token"}
        </button>
      </form>

      <div className="mt-6 pt-6 border-t border-border/50 text-center text-xs text-txt-muted">
        Remembered your password?{" "}
        <Link href="/login" className="font-bold text-brand-bright hover:underline">
          Log In
        </Link>
      </div>
    </div>
  );
}
