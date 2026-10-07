# SmartStock AI — System Architecture Specification

## 1. Executive Summary

SmartStock AI is a high-availability, production-grade financial market intelligence and virtual trading system. It provides real-time/delayed market quotes, interactive technical charts, AI-driven stock prediction models with explainability, backtesting engines, and a simulated ₹500 demo wallet balance system.

## 2. Core Architectural Principles

1. **Strict Data Boundary**: Virtual trading actions are strictly isolated from real broker orders. Virtual wallet balances are stored as integer paise (`₹500.00 = 50000 paise`) to prevent floating-point rounding errors.
2. **Pluggable Market Data Provider**: Market data fetching relies on an abstract interface (`MarketDataProvider`) allowing runtime hot-swapping between Polygon, Alpha Vantage, Yahoo Finance, or internal mock stream providers.
3. **Event-Driven & Cached Data Pipeline**:
   ```
   External Market Data Provider
              ↓
     Background Collector
              ↓
    Normalization Engine
              ↓
   Redis Cache Layer (Quotes/Tickers) + PostgreSQL (Historical Archives)
              ↓
   FastAPI Event Stream (WebSockets / SSE)
              ↓
   Next.js 14 Client App (React Query + Lightweight Charts)
   ```
4. **Explainable AI (XAI)**: Machine learning models (XGBoost / LightGBM) produce directional predictions (`UP`, `DOWN`, `NEUTRAL`) along with calibrated confidence scores, version IDs, and feature attribution (SHAP values).

## 3. Technology Stack Detail

- **Frontend**: Next.js 14+ App Router, TypeScript, Tailwind CSS, shadcn/ui primitives, Lucide Icons, Recharts, Lightweight Charts.
- **Backend API**: Python 3.11+, FastAPI, Pydantic v2, Async SQLAlchemy 2.0, Alembic migrations, Structlog.
- **Data Persistence**: PostgreSQL 16 (Relational models & wallet ledgers), Redis 7 (Quote caching & token blacklist).
- **Security**: Argon2id / bcrypt password hashing, JWT Access Tokens (RS256/HS256) with short lifetimes, Rotating Refresh Tokens, CORS lockdown, Rate limiting.
