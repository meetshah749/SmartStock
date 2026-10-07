"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, Compass, ShieldCheck, Wallet, ArrowRight, ArrowLeft, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { ProtectedRoute } from "@/components/ProtectedRoute";

function OnboardingContent() {
  const router = useRouter();
  const { user, accessToken } = useAuth();

  const [step, setStep] = useState(1);
  const [experienceLevel, setExperienceLevel] = useState("beginner");
  const [tradingGoals, setTradingGoals] = useState("Education & Strategy Practice");
  const [riskTolerance, setRiskTolerance] = useState("medium");
  const [submitting, setSubmitting] = useState(false);

  const handleComplete = async () => {
    setSubmitting(true);
    try {
      if (accessToken) {
        await fetch("http://localhost:8000/api/v1/onboarding", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            experience_level: experienceLevel,
            trading_goals: tradingGoals,
            risk_tolerance: riskTolerance,
          }),
        });
      }
      router.push("/");
    } catch {
      router.push("/");
    }
  };

  return (
    <div className="max-w-2xl mx-auto my-6 p-8 rounded-2xl bg-surface-card border border-border shadow-2xl relative overflow-hidden">
      
      {/* Progress Bar */}
      <div className="w-full bg-surface-elevated h-2 rounded-full mb-8 overflow-hidden">
        <div
          className="bg-gradient-to-r from-brand-primary to-ai-violet h-full transition-all duration-300"
          style={{ width: `${(step / 4) * 100}%` }}
        />
      </div>

      {/* Step 1: Experience Level */}
      {step === 1 && (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-brand-primary/10 text-brand-bright">
              <Compass className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs font-bold text-brand-bright uppercase tracking-wider">Step 1 of 4</span>
              <h2 className="text-xl font-extrabold text-txt-primary">What is your stock market experience?</h2>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { id: "beginner", title: "Beginner", desc: "First time exploring markets & virtual trading" },
              { id: "intermediate", title: "Intermediate", desc: "Understand basic charts & price trends" },
              { id: "advanced", title: "Advanced", desc: "Experienced with technical indicators & backtesting" },
            ].map((opt) => (
              <button
                key={opt.id}
                onClick={() => setExperienceLevel(opt.id)}
                className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between ${
                  experienceLevel === opt.id
                    ? "border-brand-primary bg-brand-primary/10 text-txt-primary shadow-lg"
                    : "border-border bg-surface-main text-txt-secondary hover:border-brand-primary/50"
                }`}
              >
                <div>
                  <h3 className="font-bold text-sm mb-1">{opt.title}</h3>
                  <p className="text-xs text-txt-muted">{opt.desc}</p>
                </div>
                {experienceLevel === opt.id && <CheckCircle2 className="w-4 h-4 text-brand-bright mt-3" />}
              </button>
            ))}
          </div>

          <div className="flex justify-end pt-4">
            <button
              onClick={() => setStep(2)}
              className="px-6 py-2.5 rounded-xl bg-brand-primary hover:bg-brand-bright text-white font-bold text-sm flex items-center gap-2"
            >
              Continue <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Trading Goals */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-ai-violet/10 text-ai-light">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs font-bold text-ai-light uppercase tracking-wider">Step 2 of 4</span>
              <h2 className="text-xl font-extrabold text-txt-primary">What is your main financial platform goal?</h2>
            </div>
          </div>

          <div className="space-y-3">
            {[
              "Education & Strategy Practice",
              "AI Prediction & Sentiment Analysis",
              "Historical Backtesting Evaluation",
              "Simulated Virtual Portfolio Management",
            ].map((goal) => (
              <button
                key={goal}
                onClick={() => setTradingGoals(goal)}
                className={`w-full p-4 rounded-xl border text-left transition-all flex items-center justify-between ${
                  tradingGoals === goal
                    ? "border-ai-violet bg-ai-violet/10 text-txt-primary shadow-lg"
                    : "border-border bg-surface-main text-txt-secondary hover:border-ai-violet/50"
                }`}
              >
                <span className="font-semibold text-sm">{goal}</span>
                {tradingGoals === goal && <CheckCircle2 className="w-4 h-4 text-ai-light" />}
              </button>
            ))}
          </div>

          <div className="flex justify-between pt-4">
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2.5 rounded-xl bg-surface-elevated text-txt-secondary hover:text-txt-primary text-sm flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
            <button
              onClick={() => setStep(3)}
              className="px-6 py-2.5 rounded-xl bg-brand-primary hover:bg-brand-bright text-white font-bold text-sm flex items-center gap-2"
            >
              Continue <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Risk Awareness */}
      {step === 3 && (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-financial-warning/10 text-financial-warning">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xs font-bold text-financial-warning uppercase tracking-wider">Step 3 of 4</span>
              <h2 className="text-xl font-extrabold text-txt-primary">Set Your Risk Tolerance Profile</h2>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { id: "low", title: "Conservative", desc: "Focus on capital preservation & low volatility stocks" },
              { id: "medium", title: "Moderate", desc: "Balanced growth with controlled risk exposure" },
              { id: "high", title: "Aggressive", desc: "High growth potential with higher price fluctuation" },
            ].map((risk) => (
              <button
                key={risk.id}
                onClick={() => setRiskTolerance(risk.id)}
                className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between ${
                  riskTolerance === risk.id
                    ? "border-financial-warning bg-financial-warning/10 text-txt-primary shadow-lg"
                    : "border-border bg-surface-main text-txt-secondary hover:border-financial-warning/50"
                }`}
              >
                <div>
                  <h3 className="font-bold text-sm mb-1">{risk.title}</h3>
                  <p className="text-xs text-txt-muted">{risk.desc}</p>
                </div>
                {riskTolerance === risk.id && <CheckCircle2 className="w-4 h-4 text-financial-warning mt-3" />}
              </button>
            ))}
          </div>

          <div className="flex justify-between pt-4">
            <button
              onClick={() => setStep(2)}
              className="px-4 py-2.5 rounded-xl bg-surface-elevated text-txt-secondary hover:text-txt-primary text-sm flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
            <button
              onClick={() => setStep(4)}
              className="px-6 py-2.5 rounded-xl bg-brand-primary hover:bg-brand-bright text-white font-bold text-sm flex items-center gap-2"
            >
              Continue <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Demo Wallet Summary */}
      {step === 4 && (
        <div className="space-y-6 text-center">
          <div className="w-16 h-16 rounded-2xl bg-financial-profit/10 text-financial-profit flex items-center justify-center mx-auto mb-2">
            <Wallet className="w-8 h-8" />
          </div>

          <div>
            <span className="text-xs font-bold text-financial-profit uppercase tracking-wider">Onboarding Complete</span>
            <h2 className="text-2xl font-extrabold text-txt-primary mt-1">Your Demo Wallet is Active!</h2>
            <p className="text-xs text-txt-muted max-w-md mx-auto mt-2">
              We have credited your account with an initial virtual balance to practice virtual stock purchases safely.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-surface-elevated border border-border max-w-sm mx-auto flex flex-col gap-2">
            <span className="text-xs text-txt-muted font-medium">Virtual Demo Allocation</span>
            <div className="text-3xl font-extrabold text-financial-profit font-numeric">₹500.00</div>
            <span className="text-xs font-mono text-txt-muted">50,000 Integer Paise</span>
          </div>

          <div className="flex justify-between pt-4">
            <button
              onClick={() => setStep(3)}
              className="px-4 py-2.5 rounded-xl bg-surface-elevated text-txt-secondary hover:text-txt-primary text-sm flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
            <button
              onClick={handleComplete}
              disabled={submitting}
              className="px-8 py-3 rounded-xl bg-financial-profit hover:bg-financial-profitLight text-white font-extrabold text-sm shadow-lg shadow-financial-profit/25 flex items-center gap-2"
            >
              {submitting ? "Finishing..." : "Enter SmartStock AI Dashboard"}
              <CheckCircle2 className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

    </div>
  );
}

export default function OnboardingPage() {
  return (
    <ProtectedRoute>
      <OnboardingContent />
    </ProtectedRoute>
  );
}
