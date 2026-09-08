# Aria Kitchen — AI Restaurant Receptionist Prototype

An end-to-end voice-enabled AI restaurant receptionist prototype for **Aria Kitchen**, built following the core architectural principle:

> **The LLM handles conversation and reasoning.**  
> **Deterministic backend services handle restaurant truth and operations.**

The LLM never invents table availability, opening hours, prices, menu items, policies, or wait times. Every factual claim is verified via live PostgreSQL database queries or pgvector semantic RAG retrieval.

---

## Architecture Overview

```text
[ Browser / Kiosk UI ]
       │ (WebSocket audio/events + REST fallback)
       ▼
[ FastAPI Backend ]
       │
       ├── Receptionist Agent (GPT-4o + Tool Calling)
       │       │
       │       ├── Tool: find_available_table  ──► Table Service (PostgreSQL)
       │       ├── Tool: get_restaurant_info   ──► RAG Service (pgvector)
       │       └── Tool: get_live_table_state  ──► Table Service (PostgreSQL)
       │
       └── Voice Service (OpenAI Realtime API Bridge + Session Management)
```

### Key Guarantees (Non-Negotiable)

1. **Anti-Hallucination Gate**: RAG retrieval requires cosine similarity $\ge 0.75$. If unverified, the AI explicitly states it cannot confirm.
2. **Deterministic Table Truth**: Table queries read live database status. The AI never promises or guesses availability.
3. **No Reservations**: Aria Kitchen is strictly walk-in only. Reservation requests are categorically rejected.
4. **Resilient Dual Mode**: Supports full-duplex OpenAI Realtime voice streaming with graceful fallback to text messaging.

---

## Prerequisites

- **Docker & Docker Compose** (for PostgreSQL with `pgvector` & Redis)
- **Python 3.11+**
- **Node.js 18+** & `npm`
- **OpenAI API Key** (with GPT-4o and Realtime API access)

---

## Setup & Running

### 1. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your own local values (never commit real keys/passwords):
```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://<db_user>:<db_password>@localhost:5433/restaurant_ai
REDIS_URL=redis://localhost:6379
RESTAURANT_ID=1
RAG_SIMILARITY_THRESHOLD=0.75
```

> Security note: keep `.env` private and rotate credentials immediately if they are ever exposed.

### 2. Start PostgreSQL & Redis

```bash
docker compose up -d
```

Verify services are healthy:
```bash
docker compose ps
```

### 3. Setup & Seed Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate   # Windows
# or: source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Seed restaurant data (Aria Kitchen tables, menu, hours, policies, knowledge docs)
python -m app.db.seed

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

The backend is now live at `http://localhost:8000`.  
- Interactive API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 4. Setup & Start Frontend

In a separate terminal:

```bash
cd frontend

npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Running Automated Tests

Run the full suite of unit, integration, and hallucination regression tests:

```bash
cd backend
.\.venv\Scripts\pytest tests -v
```

### Test Coverage

- `tests/unit/test_table_service.py`: Capacity matching, zone filtering, smallest suitable table logic, DB error handling.
- `tests/unit/test_rag_service.py`: Cosine similarity threshold gating, unverified knowledge rejection.
- `tests/integration/test_api.py`: FastAPI endpoints (`/health`, `/api/tables`, `/api/conversation/session`, `/api/conversation/message`, `/api/tools/find-available-table`).
- `tests/hallucination/test_hallucination_regression.py`: Grounding tests verifying the AI refuses to invent amenities (rooftop pool), refuses reservations, checks live availability for party sizes, and handles database outages gracefully.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System and database liveness check |
| `GET` | `/api/restaurant` | Restaurant metadata (name, address, phone) |
| `GET` | `/api/menu` | Menu items with categories, prices, allergens |
| `GET` | `/api/hours` | Structured opening hours |
| `GET` | `/api/tables` | Current live table states |
| `POST` | `/api/conversation/session` | Create new conversation session |
| `POST` | `/api/conversation/message` | Text fallback messaging endpoint |
| `POST` | `/api/tools/find-available-table` | Direct table availability tool call |
| `POST` | `/api/tools/restaurant-information` | Direct RAG semantic knowledge tool call |
| `WS` | `/ws/receptionist/{session_id}` | Realtime voice & event WebSocket stream |
