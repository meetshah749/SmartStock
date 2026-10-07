"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ShieldCheck, TrendingUp, Sparkles, AlertCircle, ArrowRight, Check } from "lucide-react";
import { useAuth } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const { registerUser } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [terms, setTerms] = useState(false);
  const [privacy, setPrivacy] = useState(false);
  const [risk, setRisk] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!terms || !privacy || !risk) {
      setError("You must acknowledge all legal terms, privacy policies, and risk disclaimers.");
      return;
    }

    setSubmitting(true);
    try {
      await registerUser({
        full_name: fullName,
        email,
        password,
        terms_of_service: terms,
        privacy_policy: privacy,
        risk_disclaimer: risk,
      });
      router.push("/onboarding");
    } catch (err: any) {
      setError(err.message || "Registration failed");
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto my-8 p-8 rounded-2xl bg-surface-card border border-border shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 w-48 h-48 bg-brand-primary/10 rounded-full blur-2xl pointer-events-none" />

      {/* Header Identity */}
      <div className="flex flex-col items-center text-center gap-2 mb-8">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-brand-deep to-ai-violet flex items-center justify-center shadow-lg shadow-brand-primary/20 mb-2">
          <TrendingUp className="w-6 h-6 text-white" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-txt-primary">Create Your Account</h1>
        <p className="text-xs text-txt-muted">Join SmartStock AI to explore market intelligence & practice virtual trading with a ₹500 demo wallet.</p>
      </div>

      {error && (
        <div className="p-3 mb-6 rounded-lg bg-financial-loss/10 border border-financial-loss/30 text-financial-loss text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-txt-secondary mb-1">Full Name</label>
          <input
            type="text"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="John Doe"
            className="w-full px-3.5 py-2.5 rounded-lg bg-surface-main border border-border text-txt-primary text-sm focus:outline-none focus:border-brand-primary transition-colors"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-txt-secondary mb-1">Work or Personal Email</label>
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
          <label className="block text-xs font-semibold text-txt-secondary mb-1">Password (8+ chars)</label>
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••••••"
            className="w-full px-3.5 py-2.5 rounded-lg bg-surface-main border border-border text-txt-primary text-sm focus:outline-none focus:border-brand-primary transition-colors"
          />
        </div>

        {/* Legal Consent Checkboxes */}
        <div className="space-y-2.5 pt-2 text-xs text-txt-secondary">
          <label className="flex items-start gap-2.5 cursor-pointer">
            <input
              type="checkbox"
              checked={terms}
              onChange={(e) => setTerms(e.target.checked)}
              className="mt-0.5 rounded border-border text-brand-primary focus:ring-brand-primary"
            />
            <span>I accept the <strong className="text-txt-primary">Terms of Service</strong>.</span>
          </label>

          <label className="flex items-start gap-2.5 cursor-pointer">
            <input
              type="checkbox"
              checked={privacy}
              onChange={(e) => setPrivacy(e.target.checked)}
              className="mt-0.5 rounded border-border text-brand-primary focus:ring-brand-primary"
            />
            <span>I accept the <strong className="text-txt-primary">Privacy Policy</strong>.</span>
          </label>

          <label className="flex items-start gap-2.5 cursor-pointer">
            <input
              type="checkbox"
              checked={risk}
              onChange={(e) => setRisk(e.target.checked)}
              className="mt-0.5 rounded border-border text-brand-primary focus:ring-brand-primary"
            />
            <span>I acknowledge that SmartStock AI provides simulated virtual trading & educational analysis.</span>
          </label>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-3 mt-4 rounded-xl bg-brand-primary hover:bg-brand-bright text-white font-bold text-sm shadow-lg shadow-brand-primary/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {submitting ? "Creating Account..." : "Create Free Account"}
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>

      <div className="mt-6 pt-6 border-t border-border/50 text-center text-xs text-txt-muted">
        Already have an account?{" "}
        <Link href="/login" className="font-bold text-brand-bright hover:underline">
          Log In
        </Link>
      </div>
    </div>
  );
}
