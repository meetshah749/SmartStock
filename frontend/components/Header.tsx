"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { TrendingUp, Sparkles, Wallet, User as UserIcon, LogOut, ChevronDown, Layers, History, ShieldCheck } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";
import { useAuth } from "@/lib/auth";

export function Header() {
  const { user, logout } = useAuth();
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  useEffect(() => {
    const checkApi = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/v1/health", { cache: "no-store" });
        if (res.ok) {
          setBackendStatus("online");
        } else {
          setBackendStatus("offline");
        }
      } catch {
        setBackendStatus("offline");
      }
    };
    checkApi();
    const interval = setInterval(checkApi, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-surface-main/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Logo & Identity */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-deep via-brand-primary to-ai-violet flex items-center justify-center shadow-lg shadow-brand-primary/20 group-hover:scale-105 transition-transform duration-200">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-lg tracking-tight text-txt-primary">SmartStock</span>
              <span className="text-xs font-semibold px-1.5 py-0.5 rounded bg-ai-violet/20 text-ai-light border border-ai-violet/30 flex items-center gap-1">
                <Sparkles className="w-3 h-3" /> AI
              </span>
            </div>
            <span className="text-[10px] uppercase tracking-wider font-semibold text-txt-muted">Financial Intelligence</span>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-txt-secondary">
          <Link href="/" className="hover:text-txt-primary transition-colors">
            Dashboard
          </Link>
          <Link href="/stocks" className="hover:text-txt-primary transition-colors">
            Explore Stocks
          </Link>
          <Link href="/compare" className="hover:text-txt-primary transition-colors">
            Compare Stocks
          </Link>
          {user && (
            <>
              <Link href="/portfolio" className="hover:text-txt-primary transition-colors">
                Portfolio
              </Link>
              <Link href="/backtesting" className="hover:text-txt-primary transition-colors">
                Backtesting Lab
              </Link>
              <Link href="/wallet" className="hover:text-txt-primary transition-colors">
                Wallet Ledger
              </Link>
              <Link href="/onboarding" className="hover:text-txt-primary transition-colors">
                Onboarding
              </Link>
              <Link href="/profile" className="hover:text-txt-primary transition-colors">
                Profile
              </Link>
              {user.is_admin && (
                <Link href="/admin" className="text-ai-light font-bold flex items-center gap-1 hover:text-white px-2 py-0.5 rounded bg-ai-violet/20 border border-ai-violet/30 transition-colors">
                  <ShieldCheck className="w-3.5 h-3.5 text-ai-light" /> Admin Panel
                </Link>
              )}
            </>
          )}
        </nav>

        {/* Right Action Bar */}
        <div className="flex items-center gap-4">
          
          {/* Authenticated User Demo Wallet Balance Link */}
          {user ? (
            <Link
              href="/wallet"
              className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-card border border-border hover:border-brand-primary transition-colors"
            >
              <Wallet className="w-4 h-4 text-financial-profit" />
              <div className="flex flex-col">
                <span className="text-[10px] uppercase font-bold text-txt-muted">Demo Balance</span>
                <span className="text-xs font-bold text-financial-profit font-numeric">
                  ₹{(user.wallet_balance_paise / 100).toFixed(2)}
                </span>
              </div>
              <span className="text-[9px] uppercase font-semibold px-1.5 py-0.5 rounded bg-brand-primary/10 text-brand-bright border border-brand-primary/20">VIRTUAL</span>
            </Link>
          ) : (
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-card border border-border">
              <Wallet className="w-4 h-4 text-brand-bright" />
              <div className="flex flex-col">
                <span className="text-[10px] uppercase font-bold text-txt-muted">Sign Up Bonus</span>
                <span className="text-xs font-bold text-brand-bright font-numeric">₹500.00 Free Demo</span>
              </div>
            </div>
          )}

          {/* System API Status */}
          <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-full bg-surface-card border border-border text-xs font-medium">
            <span className="relative flex h-2 w-2">
              <span
                className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                  backendStatus === "online"
                    ? "bg-financial-profit"
                    : backendStatus === "offline"
                    ? "bg-financial-loss"
                    : "bg-financial-warning"
                }`}
              />
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  backendStatus === "online"
                    ? "bg-financial-profit"
                    : backendStatus === "offline"
                    ? "bg-financial-loss"
                    : "bg-financial-warning"
                }`}
              />
            </span>
            <span className="text-txt-secondary text-[11px] font-semibold uppercase tracking-wider">
              {backendStatus === "online" ? "API Online" : backendStatus === "offline" ? "API Offline" : "Checking"}
            </span>
          </div>

          {/* Theme Switcher */}
          <ThemeToggle />

          {/* User Auth Buttons or Profile Menu */}
          {user ? (
            <div className="relative">
              <button
                onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-card border border-border hover:border-brand-primary transition-colors text-xs font-medium text-txt-primary"
              >
                <div className="w-6 h-6 rounded-full bg-brand-primary/20 text-brand-bright flex items-center justify-center font-bold">
                  {user.full_name[0].toUpperCase()}
                </div>
                <span className="max-w-[100px] truncate">{user.full_name}</span>
                <ChevronDown className="w-3.5 h-3.5 text-txt-muted" />
              </button>

              {userDropdownOpen && (
                <div className="absolute right-0 mt-2 w-52 rounded-xl bg-surface-card border border-border shadow-xl p-2 flex flex-col gap-1 z-50">
                  <div className="px-3 py-2 border-b border-border/50 flex flex-col">
                    <span className="text-xs font-bold text-txt-primary truncate">{user.full_name}</span>
                    <span className="text-[10px] text-txt-muted truncate">{user.email}</span>
                  </div>
                  <Link
                    href="/portfolio"
                    onClick={() => setUserDropdownOpen(false)}
                    className="px-3 py-2 rounded-lg text-xs font-medium text-txt-secondary hover:text-txt-primary hover:bg-surface-elevated flex items-center gap-2 transition-colors"
                  >
                    <Layers className="w-3.5 h-3.5" /> Virtual Portfolio
                  </Link>
                  <Link
                    href="/wallet"
                    onClick={() => setUserDropdownOpen(false)}
                    className="px-3 py-2 rounded-lg text-xs font-medium text-txt-secondary hover:text-txt-primary hover:bg-surface-elevated flex items-center gap-2 transition-colors"
                  >
                    <History className="w-3.5 h-3.5" /> Wallet Ledger
                  </Link>
                  <Link
                    href="/profile"
                    onClick={() => setUserDropdownOpen(false)}
                    className="px-3 py-2 rounded-lg text-xs font-medium text-txt-secondary hover:text-txt-primary hover:bg-surface-elevated flex items-center gap-2 transition-colors"
                  >
                    <UserIcon className="w-3.5 h-3.5" /> Profile & Settings
                  </Link>
                  {user.is_admin && (
                    <Link
                      href="/admin"
                      onClick={() => setUserDropdownOpen(false)}
                      className="px-3 py-2 rounded-lg text-xs font-bold text-ai-light hover:bg-ai-violet/20 flex items-center gap-2 transition-colors"
                    >
                      <ShieldCheck className="w-3.5 h-3.5 text-ai-violet" /> Admin Control Panel
                    </Link>
                  )}
                  <button
                    onClick={() => {
                      setUserDropdownOpen(false);
                      logout();
                    }}
                    className="px-3 py-2 rounded-lg text-xs font-medium text-financial-loss hover:bg-financial-loss/10 flex items-center gap-2 transition-colors w-full text-left"
                  >
                    <LogOut className="w-3.5 h-3.5" /> Log Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-txt-secondary hover:text-txt-primary transition-colors"
              >
                Log In
              </Link>
              <Link
                href="/register"
                className="px-3.5 py-1.5 rounded-lg text-xs font-bold bg-brand-primary text-white hover:bg-brand-bright shadow-md shadow-brand-primary/20 transition-all"
              >
                Get Started
              </Link>
            </div>
          )}

        </div>

      </div>
    </header>
  );
}
