# SmartStock AI 📈🤖

**SmartStock AI** is a serious, production-oriented financial market intelligence and virtual trading platform built with Next.js 14+, FastAPI, PostgreSQL, Redis, and modern AI/ML pipelines.

---

## 🌟 Key Features

* **Market Intelligence**: Explore stock quotes, technical indicators, financial news, and AI-driven sentiment analysis.
* **Virtual Trading Platform**: Practice trading risk-free with a ₹500.00 demo wallet balance using precise integer paise accounting (`50000 paise`).
* **Design Token Theme System**: Modern **Midnight Finance** dark mode (default) and **Clean Market** light mode with high-contrast numerical typography.
* **AI Prediction & Explainability**: Predict stock movements (UP/DOWN/NEUTRAL) with clear feature attribution, model versioning, and strict risk disclaimers.
* **Backtesting Engine**: Evaluate trading strategies against historical price data with drawdown, Sharpe ratio, and win-rate analysis.
* **Event-Driven Architecture**: Structured event logging, background workers, and wallet ledger audit trails.

---

## 🏗 System Architecture

The project is structured as a production monorepo:

```
SmartStock-AI/
├── frontend/        # Next.js 14+ (App Router, Tailwind CSS, TypeScript, theme system)
├── backend/         # FastAPI, SQLAlchemy, Alembic, Pydantic v2, Pytest
├── ml/              # Machine learning training & feature engineering pipelines
├── infra/           # Dockerfiles & container configs
├── docs/            # Architecture, database schema, and payment specifications
└── docker-compose.yml
```

---

## 🚀 Quickstart (Local Development)

### 1. Prerequisites
- Node.js 18+ & npm 9+
- Python 3.11+
- PostgreSQL & Redis (or Docker Compose)

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend API will be live at `http://localhost:8000`. OpenAPI docs available at `http://localhost:8000/docs`.

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend will be live at `http://localhost:3000`.

### Optional: Generative AI Assistant
The floating stock assistant can explain common market concepts and use available quote/history data without an AI credential. To enable free-form generative responses, set `AI_API_KEY` in `backend/.env` for local development, or in the root `.env` when using Docker Compose (optionally set `AI_BASE_URL` and `AI_MODEL` for an OpenAI-compatible API). Keep the key on the backend; never add it to a `NEXT_PUBLIC_*` variable. The assistant's risk-profile watchlist is an educational volatility screen, not a personalized suitability assessment or a buy recommendation.

### 4. Running with Docker Compose
```bash
docker-compose up --build
```

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Type Check
```bash
cd frontend
npm run type-check
```

---

## 🔒 Security & Legal Boundaries

* **Virtual Trading Only**: Virtual orders do not represent real stock exchange trades and do not involve real money.
* **Not Financial Advice**: AI predictions are probabilistic models for educational purposes and include mandatory risk disclaimers.
* **Monetary Precision**: All wallet balances are calculated server-side in integer paise to eliminate floating-point currency rounding errors.

---

## 📄 Documentation

- [Architecture Overview](file:///c:/Users/USER/Desktop/SmartStock/docs/architecture.md)
- [Database Schema Specification](file:///c:/Users/USER/Desktop/SmartStock/docs/database.md)

---

## 📜 License

Private Commercial Product Blueprint. All rights reserved.
