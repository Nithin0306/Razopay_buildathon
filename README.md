# AI Revenue Recovery Agent (Razorpay Buildathon — Track 3)

> **A closed-loop autonomous AI agent system that intercepts failed Razorpay transactions, diagnoses root causes using Gemini 2.5 Flash, evaluates deterministic safety policy guardrails, and executes automated revenue recovery.**

---

## 🌟 Executive Summary & Profit Value Proposition

Every failed checkout or subscription renewal represents lost profit. **AI Revenue Recovery Agent** bridges the gap between payment failure detection and revenue recovery:

1. **Instant Webhook Interception**: Listens to `payment.failed`, `subscription.pending`, `subscription.halted`, and `invoice.payment_failed` events in real-time.
2. **AI Root Cause Diagnosis**: Leverages Google Gemini 2.5 Flash via LangGraph to parse error codes, raw gateway steps, customer history, and transaction amounts.
3. **Deterministic Policy Gate Guardrail**: Hardcoded safety layer enforcing regulatory constraints (Fraud checks, 3-attempt customer intervention caps, LLM confidence thresholds) before any API call is made.
4. **Autonomous Razorpay Execution**: Automatically generates custom Razorpay Payment Links, resumes halted subscriptions, or schedules off-peak gateway retries using the official `razorpay` Python SDK.
5. **Next.js Command Center**: High-impact dark mode dashboard featuring live profit saved metrics (`₹ Recovered`), interactive Recharts timelines, real-time audit stream, and an embedded Webhook Simulator for hackathon judging.

---

## 📐 Architecture & Workflow Diagram

```mermaid
flowchart TD
    subgraph Ingestion ["1. Webhook Ingestion Layer"]
        RP[Razorpay Webhook] -->|HMAC-SHA256 Sig Check| API[FastAPI Webhook Router]
        API -->|Async Event Dispatch| DB[(PostgreSQL / SQLite DB)]
    end

    subgraph Agent ["2. LangGraph AI Agent & Policy Engine"]
        API -->|Background Task| Node1[Diagnose Node: Gemini 2.5 Flash]
        Node1 -->|JSON Root Cause & Confidence| Node2[Strategize Node: Recovery Policy Selector]
        Node2 --> Gate{Deterministic Policy Gate}
        
        Gate -->|Passed Safety Guardrails| Node3[Execute Node: Razorpay Action Wrapper]
        Gate -->|Blocked: Fraud / Cap / Low Confidence| Node4[Escalate Node: Support Log]
    end

    subgraph Execution ["3. Execution & Metric Closure"]
        Node3 -->|Create Link / Resume Sub| RZ_API[Razorpay Official Python SDK]
        RZ_API -->|Customer Pays Link| HookSuccess[payment_link.paid Webhook]
        HookSuccess -->|Update Status → RECOVERED| Audit[(Audit Log & Profit Metrics)]
    end

    subgraph CommandCenter ["4. Next.js Command Center"]
        Audit -->|REST API /api/metrics| Dashboard[Next.js Command Center Dashboard]
    end
```

---

## 🚀 Step-by-Step Setup & Execution Guide

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional, for PostgreSQL database)
- Gemini API Key (`GEMINI_API_KEY`) from [Google AI Studio](https://aistudio.google.com/)
- Razorpay API Test Credentials from [Razorpay Dashboard](https://dashboard.razorpay.com/)

### Clean Backend Restart Flow
Use this flow when you want to restart the backend from scratch with the local Postgres container:

```bash
# 1) Remove any stale backend container if it already exists
docker rm -f backend-api-1

# 2) Start the database container used by backend/.env
docker start recovery_postgres

# 3) Run migrations from the backend virtualenv
cd backend
./venv/bin/alembic upgrade head

# 4) Start the backend API
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If you need to fully reset the database container too, use:

```bash
docker rm -f recovery_postgres
```

Notes:
- `docker rm -f backend-api-1` is the command to delete the stale backend container before starting again.
- The backend reads its database URL from `backend/.env`, which points to `recovery_postgres` on `localhost:5432`.

---

### Step 1: Database Setup & Migration

Choose one of the database options below:

#### Option A: PostgreSQL via Docker (Recommended for Production)
```bash
# Start PostgreSQL container
docker run --name recovery_postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=recovery_agent \
  -p 5432:5432 \
  -d postgres:15

# Set in backend/.env:
# DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/recovery_agent
```

#### Option B: Zero-Config SQLite (Default for Quick Testing)
```env
# Set in backend/.env:
DATABASE_URL=sqlite+aiosqlite:///./recovery_agent.db
```

#### Apply Alembic Migrations
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run migrations to initialize tables
alembic upgrade head
```

---

### Step 2: Environment Configuration (`backend/.env`)

Configure your `backend/.env` file:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/recovery_agent

# Razorpay API Credentials
RAZORPAY_KEY_ID=rzp_test_TY3gaQRSsLD3lq
RAZORPAY_KEY_SECRET=uyKuUXURCds3S0gNr257ph3J
RAZORPAY_WEBHOOK_SECRET=track3

# Google Gemini API Key
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere

# Application
ENVIRONMENT=development
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:3000
```

---

### Step 3: Run FastAPI Backend Server

```bash
cd backend
source venv/bin/activate

# Start backend server on port 8000
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Step 4: Live Webhook Tunnel via Ngrok

Expose your local backend server to receive live Razorpay webhooks:

```bash
# In a new terminal tab:
ngrok http 8000
```

1. Copy the public forwarding URL (e.g., `https://xxxx.ngrok-free.dev`).
2. Go to **Razorpay Dashboard** → **Account & Settings** → **Webhooks** → **Add New Webhook**.
3. Set Webhook URL: `https://xxxx.ngrok-free.dev/webhooks/razorpay`
4. Set Secret: `track3`
5. Select active events: `payment.failed`, `payment_link.paid`, `payment.captured`, `invoice.paid`.

---

### Step 5: Start Next.js Command Center Dashboard

```bash
cd frontend

# Install dependencies and launch dev server
npm install
npm run dev
```

Open **`http://localhost:3000`** in your browser to view the **AI Revenue Recovery Command Center**.

---

### Step 6: Interactive Webhook Simulator & Test Suite

You can trigger simulated failure events directly from the dashboard UI or via the CLI:

```bash
cd backend
source venv/bin/activate

# Run all CLI simulation test scenarios:
python simulate.py --all

# Run individual diagnostic test suites:
python test_phase5_diagnosis.py
```

---

## 🛡️ Deterministic Policy Gate Guardrail Rules

To ensure safety and compliance, the agent uses a **hardcoded Python policy gate layer** that overrides any potential LLM hallucination:

| Guardrail Rule | Condition | Policy Gate Output | Action Taken |
|---|---|---|---|
| **Rule 1: Fraud & Security Interception** | `error_source = 'fraud' \| 'risk'` | `BLOCKED_MANUAL_REVIEW` | Escalates to human support queue |
| **Rule 2: Customer Intervention Cap** | Customer total interventions ≥ 3 | `BLOCKED_INTERVENTION_CAP` | Suppresses messaging; logs escalation |
| **Rule 3: LLM Low Confidence** | Gemini confidence score < 0.70 | `BLOCKED_LOW_CONFIDENCE` | Escalates to human team |

---

## ❓ Troubleshooting & FAQs

### 1. `[Errno 98] Address already in use`
This means `uvicorn` or another process is already running on port `8000`. Stop the existing process:
```bash
# Find and terminate process on port 8000:
fuser -k 8000/tcp
```
Then restart `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`.

### 2. `Invalid Razorpay Webhook Signature`
When testing from the UI Webhook Simulator, the signature header sends `dummy_sig`, which is automatically accepted in `development` mode. For real Razorpay webhooks, ensure `RAZORPAY_WEBHOOK_SECRET` in `backend/.env` matches the secret configured in your Razorpay Dashboard.

---

## 🛠️ Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── agent/            # LangGraph State Graph & LLM Diagnostic Nodes
│   │   │   ├── graph.py      # LangGraph workflow definition & runner
│   │   │   ├── nodes.py      # Diagnose, Strategize, and Execute nodes
│   │   │   ├── policy_gate.py# Deterministic Python Guardrails
│   │   │   └── state.py      # AgentState schema
│   │   ├── routers/          # FastAPI routes (webhooks.py, metrics.py)
│   │   ├── tools/            # Razorpay SDK Singleton & Recovery Executors
│   │   ├── database.py       # Async SQLAlchemy engine & session manager
│   │   ├── models.py         # DB Schemas (Transaction, Customer, AuditLog)
│   │   └── main.py           # FastAPI application entrypoint
│   ├── simulate.py           # CLI Webhook & Recovery Simulator
│   ├── test_phase5_diagnosis.py # Automated Diagnostic Test Suites
│   └── requirements.txt
│
└── frontend/
    ├── app/                  # Next.js App Router Page & Layout
    │   ├── components/       # HeroProfitCards, RevenueChart, SimulatorPanel, AuditLogTable, PolicyRulesCard
    │   ├── globals.css       # Custom styling & dark theme tokens
    │   └── page.tsx          # Command Center Dashboard
    ├── lib/                  # API client & mock fallback handlers
    ├── types/                # TypeScript interfaces
    └── package.json
```

---

## 🎯 Tech Stack Summary

- **AI & LLM Orchestration**: Python 3.11+, LangGraph, Google Gemini 2.5 Flash API
- **Backend Framework**: FastAPI, AsyncIO, Pydantic v2
- **Database & Persistence**: SQLite / PostgreSQL, SQLAlchemy 2.0 (Async), Alembic
- **Razorpay Integration**: Official `razorpay` Python SDK (v2.0.1) with dual Live / High-Fidelity Simulation support
- **Frontend Dashboard**: Next.js 16 (App Router), React 19, Recharts, Lucide Icons, Tailwind CSS v4
