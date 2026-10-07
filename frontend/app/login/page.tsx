"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { TrendingUp, AlertCircle, ArrowRight, Lock } from "lucide-react";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      await login(email, password);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Invalid credentials");
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto my-12 p-8 rounded-2xl bg-surface-card border border-border shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 w-48 h-48 bg-brand-primary/10 rounded-full blur-2xl pointer-events-none" />

      {/* Header Identity */}
      <div className="flex flex-col items-center text-center gap-2 mb-8">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-brand-deep to-ai-violet flex items-center justify-center shadow-lg shadow-brand-primary/20 mb-2">
          <Lock className="w-6 h-6 text-white" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-txt-primary">Welcome Back</h1>
        <p className="text-xs text-txt-muted">Log in to access your financial dashboard, watchlists, and virtual trading portfolio.</p>
      </div>

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

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs font-semibold text-txt-secondary">Password</label>
            <Link href="/forgot-password" className="text-xs font-semibold text-brand-bright hover:underline">
              Forgot Password?
            </Link>
          </div>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••••••"
            className="w-full px-3.5 py-2.5 rounded-lg bg-surface-main border border-border text-txt-primary text-sm focus:outline-none focus:border-brand-primary transition-colors"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-3 mt-4 rounded-xl bg-brand-primary hover:bg-brand-bright text-white font-bold text-sm shadow-lg shadow-brand-primary/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {submitting ? "Signing In..." : "Log In to Account"}
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>

      <div className="mt-6 pt-6 border-t border-border/50 text-center text-xs text-txt-muted">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="font-bold text-brand-bright hover:underline">
          Create Free Account
        </Link>
      </div>
    </div>
  );
}
