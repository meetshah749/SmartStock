"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { User as UserIcon, ShieldCheck, Wallet, Save, CheckCircle2, AlertCircle } from "lucide-react";

function ProfileContent() {
  const { user, accessToken } = useAuth();

  const [phoneNumber, setPhoneNumber] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("beginner");
  const [preferredMarket, setPreferredMarket] = useState("NSE");
  const [bio, setBio] = useState("");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) {
      setLoading(false);
      return;
    }

    fetch("http://localhost:8000/api/v1/users/me/profile", {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
      .then((res) => {
        if (res.ok) return res.json();
        throw new Error("Failed to load profile");
      })
      .then((data) => {
        if (data.phone_number) setPhoneNumber(data.phone_number);
        if (data.experience_level) setExperienceLevel(data.experience_level);
        if (data.preferred_market) setPreferredMarket(data.preferred_market);
        if (data.bio) setBio(data.bio);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [accessToken]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessToken) return;

    setSaving(true);
    setMessage(null);
    setError(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/users/me/profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          phone_number: phoneNumber,
          experience_level: experienceLevel,
          preferred_market: preferredMarket,
          bio,
        }),
      });

      if (!res.ok) throw new Error("Failed to save profile changes");

      setMessage("Profile details saved successfully.");
    } catch (err: any) {
      setError(err.message || "Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      
      {/* Header Banner */}
      <div className="p-8 rounded-2xl bg-surface-card border border-border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 shadow-xl">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-brand-primary to-ai-violet text-white flex items-center justify-center font-extrabold text-2xl shadow-lg">
            {user?.full_name?.[0]?.toUpperCase() || "U"}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-extrabold text-txt-primary">{user?.full_name}</h1>
              {user?.is_verified ? (
                <span className="px-2 py-0.5 rounded bg-financial-profit/20 text-financial-profit text-[10px] font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> VERIFIED
                </span>
              ) : (
                <a href="/verify-email" className="px-2 py-0.5 rounded bg-warning/20 text-warning text-[10px] font-bold">
                  UNVERIFIED (Verify Now)
                </a>
              )}
            </div>
            <p className="text-xs text-txt-muted font-mono">{user?.email}</p>
          </div>
        </div>

        {/* Demo Wallet Card */}
        <div className="px-4 py-3 rounded-xl bg-surface-elevated border border-border flex items-center gap-3">
          <Wallet className="w-6 h-6 text-financial-profit" />
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-txt-muted uppercase">Virtual Demo Wallet</span>
            <span className="text-lg font-extrabold text-financial-profit font-numeric">
              ₹{user ? (user.wallet_balance_paise / 100).toFixed(2) : "500.00"}
            </span>
          </div>
        </div>
      </div>

      {message && (
        <div className="p-4 rounded-lg bg-financial-profit/10 border border-financial-profit/30 text-financial-profit text-xs flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-financial-loss/10 border border-financial-loss/30 text-financial-loss text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Form Grid */}
      <form onSubmit={handleSave} className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Main Details */}
        <div className="md:col-span-2 p-6 rounded-2xl bg-surface-card border border-border space-y-4">
          <h2 className="text-base font-bold text-txt-primary mb-2 flex items-center gap-2">
            <UserIcon className="w-5 h-5 text-brand-bright" /> Profile Information
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-txt-secondary mb-1">Phone Number (Optional)</label>
              <input
                type="text"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="+91 98765 43210"
                className="w-full px-3.5 py-2.5 rounded-lg bg-surface-main border border-border text-txt-primary text-xs focus:outline-none focus:border-brand-primary"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-txt-secondary mb-1">Preferred Stock Market</label>
              <select
                value={preferredMarket}
                onChange={(e) => setPreferredMarket(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg bg-surface-main border border-border text-txt-primary text-xs focus:outline-none focus:border-brand-primary"
              >
                <option value="NSE">NSE (National Stock Exchange of India)</option>
                <option value="BSE">BSE (Bombay Stock Exchange)</option>
                <option value="US">US Markets (NASDAQ / NYSE)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-txt-secondary mb-1">Market Experience Level</label>
            <select
              value={experienceLevel}
              onChange={(e) => setExperienceLevel(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-lg bg-surface-main border border-border text-txt-primary text-xs focus:outline-none focus:border-brand-primary"
            >
              <option value="beginner">Beginner — Learning Basics</option>
              <option value="intermediate">Intermediate — Chart & Trend Analysis</option>
              <option value="advanced">Advanced — Indicators & Algorithmic Backtests</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-txt-secondary mb-1">Bio / Investment Focus</label>
            <textarea
              rows={3}
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Tell us about your trading strategy or learning goals..."
              className="w-full px-3.5 py-2.5 rounded-lg bg-surface-main border border-border text-txt-primary text-xs focus:outline-none focus:border-brand-primary"
            />
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 rounded-xl bg-brand-primary hover:bg-brand-bright text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-brand-primary/20 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {saving ? "Saving Changes..." : "Save Profile Details"}
            </button>
          </div>
        </div>

        {/* Legal Consent Audit Sidebar */}
        <div className="p-6 rounded-2xl bg-surface-card border border-border space-y-4">
          <h2 className="text-base font-bold text-txt-primary flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-financial-profit" /> Consent & Audit Status
          </h2>

          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-lg bg-surface-elevated border border-border flex items-center justify-between">
              <span className="text-txt-secondary">Terms of Service</span>
              <span className="font-bold text-financial-profit flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Accepted
              </span>
            </div>

            <div className="p-3 rounded-lg bg-surface-elevated border border-border flex items-center justify-between">
              <span className="text-txt-secondary">Privacy Policy</span>
              <span className="font-bold text-financial-profit flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Accepted
              </span>
            </div>

            <div className="p-3 rounded-lg bg-surface-elevated border border-border flex items-center justify-between">
              <span className="text-txt-secondary">Risk Disclaimer</span>
              <span className="font-bold text-financial-profit flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Acknowledged
              </span>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-brand-primary/10 border border-brand-primary/20 text-[11px] text-txt-muted leading-relaxed">
            Legal consent audit logs capture registration IP and timestamp verification to satisfy financial intelligence compliance standards.
          </div>
        </div>

      </form>

    </div>
  );
}

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileContent />
    </ProtectedRoute>
  );
}
