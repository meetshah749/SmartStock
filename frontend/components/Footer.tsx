import React from "react";
import { ShieldAlert, Info } from "lucide-react";

export function Footer() {
  return (
    <footer className="w-full border-t border-border bg-surface-secondary text-txt-muted text-xs py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col gap-6">
        
        {/* Mandatory Regulatory & Risk Disclaimer */}
        <div className="p-4 rounded-xl bg-surface-card border border-border flex items-start gap-3 text-txt-secondary leading-relaxed">
          <ShieldAlert className="w-5 h-5 text-warning shrink-0 mt-0.5" />
          <div className="flex flex-col gap-1 text-[11px]">
            <span className="font-bold text-txt-primary uppercase tracking-wider">Product Positioning & Risk Disclaimer</span>
            <p>
              SmartStock AI is a financial market intelligence, education, stock analysis, and virtual trading platform.
              SmartStock AI is <strong>not</strong> a stock exchange, registered broker, investment adviser, or licensed financial planner.
              All trading features provided on this environment are strictly <strong>simulated virtual trades</strong> using demo wallet allocations (₹500.00 demo balance) and do not connect to real stock market exchanges or real funds.
              AI-generated predictions are probabilistic statistical estimates for education and backtesting purposes only and carry no guaranteed financial return.
            </p>
          </div>
        </div>

        {/* Copyright & Links */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-border/50 text-[11px]">
          <p>© {new Date().getFullYear()} SmartStock AI Platform. Production-Ready Financial Intelligence System.</p>
          <div className="flex items-center gap-6">
            <span className="hover:text-txt-primary cursor-pointer transition-colors">Privacy Policy</span>
            <span className="hover:text-txt-primary cursor-pointer transition-colors">Terms of Service</span>
            <span className="hover:text-txt-primary cursor-pointer transition-colors">Risk Disclaimer</span>
            <span className="hover:text-txt-primary cursor-pointer transition-colors font-mono">v1.0.0-M1</span>
          </div>
        </div>

      </div>
    </footer>
  );
}
