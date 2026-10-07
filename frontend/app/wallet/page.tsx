"use client";

import React, { useEffect, useState } from "react";
import { Wallet, ShieldCheck, ArrowDownLeft, ArrowUpRight, History, Download, RefreshCw } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { ProtectedRoute } from "@/components/ProtectedRoute";

interface LedgerEntry {
  id: string;
  amount_paise: number;
  amount_rupees: number;
  balance_before_paise: number;
  balance_before_rupees: number;
  balance_after_paise: number;
  balance_after_rupees: number;
  transaction_type: string;
  reference_id?: string;
  created_at: string;
}

function WalletContent() {
  const { user, accessToken } = useAuth();
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchLedger = () => {
    if (!accessToken) return;
    setLoading(true);

    fetch("http://localhost:8000/api/v1/wallet/ledger", {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setLedger(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchLedger();
  }, [accessToken]);

  const exportCSV = () => {
    if (ledger.length === 0) return;

    const headers = ["Timestamp", "Transaction Type", "Amount (INR)", "Balance Before", "Balance After", "Reference ID"];
    const rows = ledger.map((e) => [
      new Date(e.created_at).toLocaleString(),
      e.transaction_type,
      e.amount_rupees,
      e.balance_before_rupees,
      e.balance_after_rupees,
      e.reference_id || "",
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `SmartStock_Wallet_Ledger_${user?.id?.slice(0, 8) || "statement"}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-8">
      
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-txt-primary tracking-tight">Virtual Wallet & Audit Ledger</h1>
          <p className="text-xs text-txt-muted mt-1">
            Bank-grade precision virtual ledger. All credit and debit transactions are recorded in an immutable ledger.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchLedger}
            className="px-4 py-2 rounded-xl bg-surface-card border border-border text-txt-secondary hover:text-txt-primary text-xs font-bold flex items-center gap-2"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
          <button
            onClick={exportCSV}
            className="px-4 py-2 rounded-xl bg-brand-primary text-white text-xs font-bold flex items-center gap-2 shadow-md shadow-brand-primary/20"
          >
            <Download className="w-3.5 h-3.5" /> Export Statement (CSV)
          </button>
        </div>
      </div>

      {/* Wallet Balance Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 font-numeric">
        
        <div className="p-6 rounded-2xl bg-surface-card border border-border flex flex-col gap-1 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-txt-muted uppercase">Available Demo Cash</span>
            <Wallet className="w-5 h-5 text-financial-profit" />
          </div>
          <div className="text-3xl font-extrabold text-financial-profit">
            ₹{user ? (user.wallet_balance_paise / 100).toLocaleString("en-IN") : "500"}
          </div>
          <span className="text-[11px] font-mono text-txt-muted">
            INR Virtual Demo Balance
          </span>
        </div>

        <div className="p-6 rounded-2xl bg-surface-card border border-border flex flex-col gap-1 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-txt-muted uppercase">Initial Demo Bonus</span>
            <ShieldCheck className="w-5 h-5 text-brand-bright" />
          </div>
          <div className="text-3xl font-extrabold text-brand-bright">₹500</div>
          <span className="text-[11px] font-mono text-txt-muted">₹500 Granted at Sign Up</span>
        </div>

        <div className="p-6 rounded-2xl bg-surface-card border border-border flex flex-col gap-1 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-txt-muted uppercase">Ledger Transactions</span>
            <History className="w-5 h-5 text-ai-violet" />
          </div>
          <div className="text-3xl font-extrabold text-txt-primary">{ledger.length}</div>
          <span className="text-[11px] font-mono text-txt-muted">Immutable Audit Records</span>
        </div>

      </div>

      {/* Wallet Ledger Table */}
      <div className="p-6 rounded-2xl bg-surface-card border border-border space-y-4 shadow-xl">
        <h2 className="text-base font-bold text-txt-primary flex items-center gap-2">
          <History className="w-5 h-5 text-ai-light" /> Transaction Audit Ledger
        </h2>

        {loading ? (
          <div className="py-8 text-center text-xs text-txt-muted animate-pulse">
            Loading ledger history...
          </div>
        ) : ledger.length === 0 ? (
          <div className="py-8 text-center text-xs text-txt-muted">
            No transaction ledger records found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-numeric">
              <thead>
                <tr className="border-b border-border text-txt-muted text-[11px] uppercase">
                  <th className="pb-3 font-semibold">Timestamp</th>
                  <th className="pb-3 font-semibold">Type</th>
                  <th className="pb-3 font-semibold">Amount</th>
                  <th className="pb-3 font-semibold">Before</th>
                  <th className="pb-3 font-semibold">After</th>
                  <th className="pb-3 font-semibold text-right">Reference ID</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50">
                {ledger.map((entry) => {
                  const isCredit = entry.amount_paise >= 0;
                  return (
                    <tr key={entry.id} className="hover:bg-surface-elevated transition-colors">
                      <td className="py-3.5 text-txt-secondary font-mono text-[11px]">
                        {new Date(entry.created_at).toLocaleString()}
                      </td>
                      <td className="py-3.5">
                        <span className="font-extrabold text-txt-primary">{entry.transaction_type}</span>
                      </td>
                      <td className="py-3.5">
                        <span
                          className={`font-bold flex items-center gap-0.5 ${
                            isCredit ? "text-financial-profit" : "text-financial-loss"
                          }`}
                        >
                          {isCredit ? (
                            <ArrowDownLeft className="w-3.5 h-3.5" />
                          ) : (
                            <ArrowUpRight className="w-3.5 h-3.5" />
                          )}
                          {isCredit ? "+" : ""}₹{entry.amount_rupees.toFixed(2)}
                        </span>
                      </td>
                      <td className="py-3.5 text-txt-muted">₹{entry.balance_before_rupees.toFixed(2)}</td>
                      <td className="py-3.5 font-bold text-txt-primary">₹{entry.balance_after_rupees.toFixed(2)}</td>
                      <td className="py-3.5 text-right font-mono text-[10px] text-txt-muted">
                        {entry.reference_id || "N/A"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}

export default function WalletPage() {
  return (
    <ProtectedRoute>
      <WalletContent />
    </ProtectedRoute>
  );
}
