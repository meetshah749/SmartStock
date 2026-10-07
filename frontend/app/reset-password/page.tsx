"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { KeyRound, CheckCircle2, AlertCircle, ArrowRight } from "lucide-react";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const t = searchParams.get("token");
    if (t) setToken(t);
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setSubmitting(true);

    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: newPassword }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Reset failed");
      }

      const data = await res.json();
      setMessage(data.message);
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } catch (err: any) {
      setError(err.message || "Failed to reset password");
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
        <h1 className="text-2xl font-bold tracking-tight text-txt-primary">Set New Password</h1>
        <p className="text-xs text-txt-muted">Provide your reset token and enter a strong new password.</p>
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
          <label className="block text-xs font-semibold text-txt-secondary mb-1">Reset Token</label>
          <input
            type="text"
            required
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Reset token string"
            className="w-full px-3.5 py-2.5 rounded-lg bg-surface-main border border-border font-mono text-xs text-txt-primary focus:outline-none focus:border-brand-primary transition-colors"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-txt-secondary mb-1">New Password (8+ chars)</label>
          <input
            type="password"
            required
            minLength={8}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="••••••••••••"
            className="w-full px-3.5 py-2.5 rounded-lg bg-surface-main border border-border text-txt-primary text-sm focus:outline-none focus:border-brand-primary transition-colors"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-3 rounded-xl bg-brand-primary hover:bg-brand-bright text-white font-bold text-sm shadow-lg shadow-brand-primary/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {submitting ? "Resetting Password..." : "Update Password"}
        </button>
      </form>

      <div className="mt-6 pt-6 border-t border-border/50 text-center text-xs text-txt-muted">
        <Link href="/login" className="font-bold text-brand-bright hover:underline">
          Back to Login
        </Link>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-txt-muted">Loading Reset Form...</div>}>
      <ResetPasswordForm />
    </Suspense>
  );
}
