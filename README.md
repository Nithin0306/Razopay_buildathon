# AI Revenue Recovery Agent (Razorpay Buildathon — Track 3)

> **A closed-loop autonomous AI agent system that intercepts failed Razorpay transactions, diagnoses root causes using an LLM, evaluates deterministic safety policy guardrails, and executes automated revenue recovery.**

## 🎥 Video Pitch

Watch the project walkthrough and five-minute demo: [AI Revenue Recovery Agent video pitch](https://drive.google.com/file/d/1ORxKVlAUJrRI2jaGrOAJVOiAgkxYEY2L/view?usp=sharing)

## 💡 The Product in One Minute

Payment failure is not the end of a transaction; it is a decision point. This project turns that moment into an automated, explainable recovery workflow:

1. A Razorpay failure webhook arrives at the FastAPI backend.
2. The system stores the customer, transaction, and original gateway payload.
3. The configured AI/LLM diagnoses the likely root cause and suggests a recovery strategy. If the AI provider is unavailable, deterministic heuristics keep the workflow testable.
4. A Python policy gate checks fraud risk, customer intervention history, and confidence before any automated recovery action is allowed.
5. The approved action is executed through a normalized recovery tool and written to the audit log.
6. A later success webhook can close the loop by changing the transaction to `RECOVERED` and updating recovered revenue.

The result is a system that is designed to recover good transactions quickly while deliberately sending risky or uncertain transactions to a human.

---

## 🌟 Executive Summary & Profit Value Proposition

Every failed checkout or subscription renewal represents lost profit. **AI Revenue Recovery Agent** bridges the gap between payment failure detection and revenue recovery:

1. **Instant Webhook Interception**: Listens to `payment.failed`, `subscription.pending`, `subscription.halted`, and `invoice.payment_failed` events in real-time.
2. **AI Root Cause Diagnosis**: Uses an LLM through LangGraph to parse error codes, raw gateway steps, customer history, and transaction amounts.
3. **Deterministic Policy Gate Guardrail**: Hardcoded safety layer enforcing regulatory constraints (Fraud checks, 3-attempt customer intervention caps, LLM confidence thresholds) before any API call is made.
4. **Autonomous Razorpay Execution**: Automatically generates custom Razorpay Payment Links, resumes halted subscriptions, or schedules off-peak gateway retries using the official `razorpay` Python SDK.
5. **Next.js Command Center**: High-impact dark mode dashboard featuring live profit saved metrics (`₹ Recovered`), interactive Recharts timelines, real-time audit stream, and an embedded Webhook Simulator for hackathon judging.

### What Is Demonstrably Working

| Capability | Working behavior |
|---|---|
| Webhook ingestion | Accepts payment, subscription, invoice, and payment-link events through FastAPI routes. |
| Root-cause diagnosis | Identifies insufficient funds, expired cards, bank or network failures, fraud, and unknown failures. |
| Recovery strategy | Generates a payment link, schedules a retry, attempts a subscription action where applicable, or escalates. |
| Safety enforcement | Blocks fraud or risk sources, three-or-more prior interventions, and confidence below 70%. |
| Persistence | Stores transactions, customers, raw payloads, agent reasoning, policy results, and action results. |
| Operational visibility | Shows metrics, recovery rate, revenue at risk, audit entries, search, filters, details, and pagination. |
| Demoability | Provides four preset webhook scenarios and a live execution console without requiring a real failed checkout. |

The Razorpay executor supports two modes. With valid credentials it can make a test/live SDK call; with missing or placeholder credentials it returns a clearly marked simulation result so the rest of the workflow remains demonstrable.

---

## 📐 Architecture & Workflow Diagram

```mermaid
flowchart TD
    subgraph Ingestion ["1. Webhook Ingestion Layer"]
        RP[Razorpay Webhook] -->|HMAC-SHA256 Sig Check| API[FastAPI Webhook Router]
        API -->|Async Event Dispatch| DB[(PostgreSQL / SQLite DB)]
    end

    subgraph Agent ["2. LangGraph AI Agent & Policy Engine"]
        API -->|Background Task| Node1[Diagnose Node: AI/LLM]
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
- AI provider API key. Gemini 2.5 Flash is supported through `GEMINI_API_KEY` and [Google AI Studio](https://aistudio.google.com/).
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

#### Recommended Dashboard Demo

1. Open `http://localhost:3000` and start on **Overview**.
2. Open **Webhook Simulator** and run **Card Declined — Insufficient Funds** to show a recovery-link decision.
3. Run **Bank Gateway Technical Timeout** to show a scheduled retry.
4. Run **Security & Fraud Risk Flag** to show a deterministic policy block and human escalation.
5. Open **Live AI Audit Stream** to inspect diagnosis, confidence, policy status, and final action.
6. Open **Policy Guardrails** to explain why unsafe automation is blocked.

The **Customer Pays Recovery Link** preset represents the final `payment_link.paid` callback. It updates revenue only when its payment-link ID matches a stored recovery transaction; for a truthful live demo, complete the generated Razorpay test link or send a matching success webhook.

### API Surface

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Confirm that the backend is available. |
| `POST` | `/webhooks/razorpay` | Ingest and process Razorpay webhook events. |
| `GET` | `/api/metrics` | Return recovery, risk, escalation, and policy counters. |
| `GET` | `/api/audit-log?page=1&limit=20` | Return the paginated explainability trail. |
| `GET` | `/api/transactions?status=recovered` | List transactions, optionally filtered by status. |

---

## 🛡️ Deterministic Policy Gate Guardrail Rules

To ensure safety and compliance, the agent uses a **hardcoded Python policy gate layer** that overrides any potential LLM hallucination:

| Guardrail Rule | Condition | Policy Gate Output | Action Taken |
|---|---|---|---|
| **Rule 1: Fraud & Security Interception** | `error_source = 'fraud' \| 'risk'` | `BLOCKED_MANUAL_REVIEW` | Escalates to human support queue |
| **Rule 2: Customer Intervention Cap** | Customer total interventions ≥ 3 | `BLOCKED_INTERVENTION_CAP` | Suppresses messaging; logs escalation |
| **Rule 3: LLM Low Confidence** | AI confidence score < 0.70 | `BLOCKED_LOW_CONFIDENCE` | Escalates to human team |

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
│   │   ├── models/           # DB Schemas (Transaction, Customer, AuditLog)
│   │   │   └── db.py
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

- **AI & LLM Orchestration**: Python 3.11+, LangGraph, configurable AI provider with Gemini 2.5 Flash support
- **Backend Framework**: FastAPI, AsyncIO, Pydantic v2
- **Database & Persistence**: SQLite / PostgreSQL, SQLAlchemy 2.0 (Async), Alembic
- **Razorpay Integration**: Official `razorpay` Python SDK (v2.0.1) with dual Live / High-Fidelity Simulation support
- **Frontend Dashboard**: Next.js 16 (App Router), React 19, Recharts, Lucide Icons, Tailwind CSS v4
