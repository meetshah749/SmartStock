"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ShieldCheck,
  Users,
  TrendingUp,
  CreditCard,
  DollarSign,
  Activity,
  UserCheck,
  UserX,
  Shield,
  Edit3,
  RefreshCw,
  Search,
  Check,
  AlertCircle,
} from "lucide-react";
import { useAuth } from "@/lib/auth";

interface SystemAnalytics {
  total_users: number;
  active_users: number;
  admin_users: number;
  total_orders_executed: number;
  total_platform_trading_volume_rupees: number;
  total_demo_wallets_issued_rupees: number;
}

interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  is_admin: boolean;
  created_at: string;
  wallet_balance_rupees: number;
}

interface SystemOrder {
  order_id: string;
  user_id: string;
  user_email: string;
  ticker_symbol: string;
  order_type: string;
  side: string;
  quantity: number;
  price_rupees: number;
  status: string;
  created_at: string;
}

export default function AdminDashboardPage() {
  const router = useRouter();
  const { user, accessToken, loading } = useAuth();

  const [analytics, setAnalytics] = useState<SystemAnalytics | null>(null);
  const [usersList, setUsersList] = useState<AdminUser[]>([]);
  const [ordersList, setOrdersList] = useState<SystemOrder[]>([]);
  const [fetching, setFetching] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // Wallet adjustment modal state
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [adjustAmount, setAdjustAmount] = useState<string>("500");
  const [adjustMode, setAdjustMode] = useState<"set" | "add">("set");
  const [adjusting, setAdjusting] = useState(false);
  const [actionMsg, setActionMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    if (!loading && (!user || !user.is_admin)) {
      router.push("/");
      return;
    }

    if (user && user.is_admin && accessToken) {
      loadAdminData();
    }
  }, [user, loading, accessToken]);

  const loadAdminData = async () => {
    setFetching(true);
    setActionMsg(null);
    try {
      const headers = { Authorization: `Bearer ${accessToken}` };

      const [resAnalytics, resUsers, resOrders] = await Promise.all([
        fetch("http://localhost:8000/api/v1/admin/analytics", { headers }),
        fetch("http://localhost:8000/api/v1/admin/users", { headers }),
        fetch("http://localhost:8000/api/v1/admin/orders", { headers }),
      ]);

      if (resAnalytics.ok) setAnalytics(await resAnalytics.json());
      if (resUsers.ok) setUsersList(await resUsers.json());
      if (resOrders.ok) setOrdersList(await resOrders.json());
    } catch (e: any) {
      setActionMsg({ type: "error", text: "Failed to connect to Admin API." });
    } finally {
      setFetching(false);
    }
  };

  const handleToggleActive = async (targetUser: AdminUser) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/admin/users/${targetUser.id}/toggle-active`, {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Action failed");

      setActionMsg({ type: "success", text: data.message });
      loadAdminData();
    } catch (err: any) {
      setActionMsg({ type: "error", text: err.message });
    }
  };

  const handleToggleAdmin = async (targetUser: AdminUser) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/admin/users/${targetUser.id}/toggle-admin`, {
        method: "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Action failed");

      setActionMsg({ type: "success", text: data.message });
      loadAdminData();
    } catch (err: any) {
      setActionMsg({ type: "error", text: err.message });
    }
  };

  const handleAdjustWallet = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    setAdjusting(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/admin/users/${selectedUser.id}/adjust-wallet`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          amount_rupees: parseFloat(adjustAmount),
          mode: adjustMode,
          reason: "Admin manual balance adjustment",
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to adjust balance");

      setActionMsg({ type: "success", text: `Updated ${selectedUser.full_name}'s balance to ₹${data.new_balance_rupees}` });
      setSelectedUser(null);
      loadAdminData();
    } catch (err: any) {
      setActionMsg({ type: "error", text: err.message });
    } finally {
      setAdjusting(false);
    }
  };

  if (loading || fetching) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <RefreshCw className="w-8 h-8 text-ai-light animate-spin mx-auto mb-4" />
        <p className="text-sm font-semibold text-txt-muted">Loading Admin Command Center...</p>
      </div>
    );
  }

  const filteredUsers = usersList.filter(
    (u) =>
      u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.full_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-ai-violet/20 via-surface-card to-surface-card border border-ai-violet/30 shadow-2xl relative overflow-hidden">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-ai-violet flex items-center justify-center shadow-lg shadow-ai-violet/30 text-white">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight text-txt-primary">Admin Command Center</h1>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-ai-violet text-white">SUPERUSER</span>
            </div>
            <p className="text-xs text-txt-muted mt-0.5">Manage platform users, view system analytics, grant admin powers, and control demo balances.</p>
          </div>
        </div>

        <button
          onClick={loadAdminData}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-surface-main border border-border hover:border-brand-primary text-xs font-semibold text-txt-primary transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5 text-txt-muted" /> Refresh Metrics
        </button>
      </div>

      {actionMsg && (
        <div
          className={`p-4 rounded-xl border text-xs font-semibold flex items-center justify-between ${
            actionMsg.type === "success"
              ? "bg-financial-profit/10 border-financial-profit/30 text-financial-profit"
              : "bg-financial-loss/10 border-financial-loss/30 text-financial-loss"
          }`}
        >
          <div className="flex items-center gap-2">
            {actionMsg.type === "success" ? <Check className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
            <span>{actionMsg.text}</span>
          </div>
          <button onClick={() => setActionMsg(null)} className="text-xs underline">Dismiss</button>
        </div>
      )}

      {/* Analytics Grid */}
      {analytics && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="p-5 rounded-2xl bg-surface-card border border-border flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-txt-muted uppercase tracking-wider">Total Registered Users</span>
              <div className="text-2xl font-bold font-numeric text-txt-primary mt-1">{analytics.total_users}</div>
              <span className="text-[11px] text-financial-profit font-semibold">{analytics.active_users} Active ({analytics.admin_users} Admins)</span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-brand-primary/10 text-brand-bright flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-surface-card border border-border flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-txt-muted uppercase tracking-wider">Total Virtual Trades Executed</span>
              <div className="text-2xl font-bold font-numeric text-txt-primary mt-1">{analytics.total_orders_executed}</div>
              <span className="text-[11px] text-txt-muted font-semibold">Orders Executed</span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-ai-violet/10 text-ai-light flex items-center justify-center">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-surface-card border border-border flex items-center justify-between">
            <div>
              <span className="text-xs font-semibold text-txt-muted uppercase tracking-wider">Platform Demo Capital Issued</span>
              <div className="text-2xl font-bold font-numeric text-financial-profit mt-1">₹{analytics.total_demo_wallets_issued_rupees.toLocaleString("en-IN")}</div>
              <span className="text-[11px] text-txt-muted font-semibold">Total Virtual Rupees</span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-financial-profit/10 text-financial-profit flex items-center justify-center">
              <CreditCard className="w-5 h-5" />
            </div>
          </div>
        </div>
      )}

      {/* User Management Section */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-txt-primary">User Management & Privilege Control</h2>
            <p className="text-xs text-txt-muted">View all platform users, grant/revoke admin status, edit virtual balances, or ban accounts.</p>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-txt-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search user by name or email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 rounded-lg bg-surface-card border border-border text-xs text-txt-primary focus:outline-none focus:border-brand-primary"
            />
          </div>
        </div>

        <div className="rounded-2xl bg-surface-card border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-main border-b border-border text-txt-muted font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">User</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Account Status</th>
                  <th className="px-4 py-3">Demo Wallet Balance</th>
                  <th className="px-4 py-3">Registered On</th>
                  <th className="px-4 py-3 text-right">Admin Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50 text-txt-primary font-medium">
                {filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-txt-muted">No users found.</td>
                  </tr>
                ) : (
                  filteredUsers.map((u) => (
                    <tr key={u.id} className="hover:bg-surface-main/50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="font-bold text-txt-primary">{u.full_name}</div>
                        <div className="text-[11px] text-txt-muted">{u.email}</div>
                      </td>

                      <td className="px-4 py-3">
                        {u.is_admin ? (
                          <span className="px-2 py-0.5 rounded bg-ai-violet/20 text-ai-light font-bold text-[10px] uppercase border border-ai-violet/30 flex items-center gap-1 w-max">
                            <ShieldCheck className="w-3 h-3" /> Admin
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-surface-main text-txt-muted font-semibold text-[10px] uppercase border border-border w-max">
                            Standard User
                          </span>
                        )}
                      </td>

                      <td className="px-4 py-3">
                        {u.is_active ? (
                          <span className="px-2 py-0.5 rounded bg-financial-profit/10 text-financial-profit font-semibold text-[10px] uppercase border border-financial-profit/20">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-financial-loss/10 text-financial-loss font-semibold text-[10px] uppercase border border-financial-loss/20">
                            Banned
                          </span>
                        )}
                      </td>

                      <td className="px-4 py-3 font-bold font-numeric text-financial-profit">
                        ₹{u.wallet_balance_rupees.toLocaleString("en-IN")}
                      </td>

                      <td className="px-4 py-3 text-txt-muted text-[11px]">
                        {new Date(u.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })}
                      </td>

                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => setSelectedUser(u)}
                            className="px-2.5 py-1 rounded bg-surface-main border border-border hover:border-brand-primary text-txt-secondary hover:text-txt-primary text-[11px] font-semibold transition-colors flex items-center gap-1"
                          >
                            <Edit3 className="w-3 h-3 text-brand-bright" /> Wallet
                          </button>

                          <button
                            onClick={() => handleToggleAdmin(u)}
                            className={`px-2.5 py-1 rounded text-[11px] font-semibold border transition-colors flex items-center gap-1 ${
                              u.is_admin
                                ? "bg-ai-violet/10 text-ai-light border-ai-violet/30 hover:bg-ai-violet/20"
                                : "bg-surface-main text-txt-secondary border-border hover:border-ai-violet"
                            }`}
                          >
                            <Shield className="w-3 h-3" /> {u.is_admin ? "Revoke Admin" : "Make Admin"}
                          </button>

                          <button
                            onClick={() => handleToggleActive(u)}
                            className={`px-2 py-1 rounded text-[11px] font-semibold border transition-colors flex items-center gap-1 ${
                              u.is_active
                                ? "bg-financial-loss/10 text-financial-loss border-financial-loss/30 hover:bg-financial-loss/20"
                                : "bg-financial-profit/10 text-financial-profit border-financial-profit/30 hover:bg-financial-profit/20"
                            }`}
                          >
                            {u.is_active ? <UserX className="w-3 h-3" /> : <UserCheck className="w-3 h-3" />}
                            {u.is_active ? "Ban" : "Unban"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Audit Log Section */}
      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-bold text-txt-primary">System-wide Order Audit Stream</h2>
          <p className="text-xs text-txt-muted">Real-time log of all virtual trades placed across the entire platform.</p>
        </div>

        <div className="rounded-2xl bg-surface-card border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-main border-b border-border text-txt-muted font-semibold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Trader Email</th>
                  <th className="px-4 py-3">Ticker</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Quantity</th>
                  <th className="px-4 py-3">Execution Price</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/50 text-txt-primary font-medium">
                {ordersList.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-txt-muted">No orders placed on platform yet.</td>
                  </tr>
                ) : (
                  ordersList.map((ord) => (
                    <tr key={ord.order_id} className="hover:bg-surface-main/50 transition-colors">
                      <td className="px-4 py-3 font-semibold text-txt-primary">{ord.user_email}</td>
                      <td className="px-4 py-3 font-bold text-brand-bright">{ord.ticker_symbol}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                            ord.side === "BUY" ? "bg-financial-profit/20 text-financial-profit" : "bg-financial-loss/20 text-financial-loss"
                          }`}
                        >
                          {ord.side}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-numeric">{ord.quantity}</td>
                      <td className="px-4 py-3 font-numeric font-bold">₹{ord.price_rupees.toLocaleString("en-IN")}</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded bg-surface-main border border-border text-[10px] uppercase font-semibold text-txt-secondary">
                          {ord.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-txt-muted text-[11px]">
                        {new Date(ord.created_at).toLocaleString("en-IN")}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Wallet Adjustment Modal */}
      {selectedUser && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-surface-card border border-border rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-base font-bold text-txt-primary">Adjust Demo Wallet Balance</h3>
              <button onClick={() => setSelectedUser(null)} className="text-txt-muted hover:text-txt-primary">✕</button>
            </div>

            <p className="text-xs text-txt-muted">
              Target User: <strong className="text-txt-primary">{selectedUser.full_name}</strong> ({selectedUser.email})<br />
              Current Balance: <span className="text-financial-profit font-bold">₹{selectedUser.wallet_balance_rupees}</span>
            </p>

            <form onSubmit={handleAdjustWallet} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-txt-secondary mb-1">Adjustment Mode</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setAdjustMode("set")}
                    className={`py-2 text-xs font-bold rounded-lg border transition-colors ${
                      adjustMode === "set" ? "bg-brand-primary text-white border-brand-primary" : "bg-surface-main text-txt-muted border-border"
                    }`}
                  >
                    Set Exact Balance
                  </button>
                  <button
                    type="button"
                    onClick={() => setAdjustMode("add")}
                    className={`py-2 text-xs font-bold rounded-lg border transition-colors ${
                      adjustMode === "add" ? "bg-brand-primary text-white border-brand-primary" : "bg-surface-main text-txt-muted border-border"
                    }`}
                  >
                    Credit / Add Funds
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-txt-secondary mb-1">Amount in ₹ Rupees</label>
                <input
                  type="number"
                  min="0"
                  step="10"
                  required
                  value={adjustAmount}
                  onChange={(e) => setAdjustAmount(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-surface-main border border-border text-sm font-numeric text-txt-primary focus:outline-none focus:border-brand-primary"
                />
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedUser(null)}
                  className="flex-1 py-2 rounded-lg border border-border text-xs font-semibold text-txt-secondary hover:text-txt-primary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={adjusting}
                  className="flex-1 py-2 rounded-lg bg-brand-primary text-white font-bold text-xs hover:bg-brand-bright shadow-lg shadow-brand-primary/20"
                >
                  {adjusting ? "Updating..." : "Confirm Adjustment"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
