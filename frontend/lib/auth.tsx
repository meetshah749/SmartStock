"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  is_admin: boolean;
  created_at: string;
  wallet_balance_paise: number;
  wallet_balance_rupees: number;
}

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  loading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  registerUser: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Rehydrate session from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem("smartstock_access_token");
    const storedUser = localStorage.getItem("smartstock_user");

    if (storedToken && storedUser) {
      try {
        setAccessToken(storedToken);
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem("smartstock_access_token");
        localStorage.removeItem("smartstock_user");
      }
    }
    setLoading(false);
  }, []);

  const login = async (email: string, pass: string) => {
    const res = await fetch("http://localhost:8000/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password: pass }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Login failed");
    }

    const data = await res.json();
    setAccessToken(data.access_token);
    setUser(data.user);
    localStorage.setItem("smartstock_access_token", data.access_token);
    localStorage.setItem("smartstock_refresh_token", data.refresh_token);
    localStorage.setItem("smartstock_user", JSON.stringify(data.user));
  };

  const registerUser = async (payload: any) => {
    const res = await fetch("http://localhost:8000/api/v1/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Registration failed");
    }

    const data = await res.json();
    setAccessToken(data.access_token);
    setUser(data.user);
    localStorage.setItem("smartstock_access_token", data.access_token);
    localStorage.setItem("smartstock_refresh_token", data.refresh_token);
    localStorage.setItem("smartstock_user", JSON.stringify(data.user));
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem("smartstock_refresh_token");
    if (refreshToken) {
      try {
        await fetch("http://localhost:8000/api/v1/auth/logout", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch {
        // Silent catch for logout network errors
      }
    }
    setUser(null);
    setAccessToken(null);
    localStorage.removeItem("smartstock_access_token");
    localStorage.removeItem("smartstock_refresh_token");
    localStorage.removeItem("smartstock_user");
  };

  const refreshSession = async () => {
    const storedRefresh = localStorage.getItem("smartstock_refresh_token");
    if (!storedRefresh) return;

    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: storedRefresh }),
      });

      if (res.ok) {
        const data = await res.json();
        setAccessToken(data.access_token);
        setUser(data.user);
        localStorage.setItem("smartstock_access_token", data.access_token);
        localStorage.setItem("smartstock_refresh_token", data.refresh_token);
        localStorage.setItem("smartstock_user", JSON.stringify(data.user));
      } else {
        logout();
      }
    } catch {
      // Keep offline cache if server temporarily unavailable
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        loading,
        login,
        registerUser,
        logout,
        refreshSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
