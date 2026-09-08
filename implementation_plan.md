# AI Restaurant Receptionist — Implementation Plan

> Based on: [AI_RESTAURANT_RECEPTIONIST_ARCHITECTURE.md](file:///d:/Ai%20Receptionist%202026/AI_RESTAURANT_RECEPTIONIST_ARCHITECTURE.md)  
> Status: **Ready for Review**  
> Target: Full-stack voice AI receptionist for walk-in restaurant

---

## Overview

Build a real-time, voice-first AI receptionist that greets walk-in customers, manages live table seating, maintains a waiting queue, answers restaurant FAQs, collects feedback, and optionally remembers returning customers via opt-in face recognition.

The core architectural principle that must remain intact throughout:

> **The AI handles conversation; deterministic backend services handle truth and operations.**

---

## User Review Required

> [!IMPORTANT]
> Before implementation starts, confirm the following:
> - Which LLM provider to use? (OpenAI / Gemini / Anthropic / self-hosted)
> - Which real-time voice provider? (OpenAI Realtime API / Deepgram / AssemblyAI / ElevenLabs)
> - Which face recognition library? (DeepFace / InsightFace / AWS Rekognition / Azure Face)
> - Hosting target? (Local dev only / cloud — AWS / GCP / Azure)
> - Is the Manager Dashboard in scope for the first build, or a later phase?

> [!WARNING]
> Face recognition (MVP-4) must NOT be implemented before the core restaurant state machine (MVP-2) is fully tested and stable.

---

## Open Questions

> [!IMPORTANT]
> 1. What restaurant data should be pre-seeded? (table count, zones, menu items, hours, policies)
> 2. Should the avatar be a static UI widget or an animated 3D avatar?
> 3. Is a mobile-responsive receptionist UI required or only kiosk/desktop?
> 4. What language(s) should the voice receptionist support?
> 5. Should the waiting queue send SMS/push notifications when a table is ready, or is AI voice notification sufficient?

---

## Proposed Changes

---

### Phase 0 — Project Skeleton

#### [NEW] `backend/` — FastAPI Python backend
#### [NEW] `frontend/` — React + TypeScript frontend
#### [NEW] `docker-compose.yml` — Local dev orchestration
#### [NEW] `.env.example` — Environment variable template
#### [NEW] `README.md` — Setup and run instructions

**What gets set up:**
- Python virtual environment + `pyproject.toml` / `requirements.txt`
- FastAPI app entry point (`backend/app/main.py`)
- Vite + React + TypeScript scaffolding (`frontend/`)
- PostgreSQL + Redis containers via Docker Compose
- pgvector extension enabled in PostgreSQL
- Environment config loading (`backend/app/config/settings.py`)
- Structured logging (`backend/app/config/logging.py`)

---

### Phase 1 — Database Models & Migrations

#### [NEW] `backend/migrations/` — Alembic migration files

**Tables to create (PostgreSQL):**

| Table | Key Fields |
|---|---|
| `restaurants` | id, name, address, timezone |
| `restaurant_hours` | restaurant_id, day_of_week, open_at, close_at |
| `restaurant_policies` | restaurant_id, key, value |
| `menu_items` | id, name, category, price, description, allergens, is_vegetarian |
| `knowledge_documents` | id, restaurant_id, title, content, embedding (vector) |
| `restaurant_tables` | id, restaurant_id, table_number, capacity, zone, status, current_visit_id |
| `visits` | id, restaurant_id, customer_id, party_size, table_id, arrival_at, seated_at, departed_at, status |
| `waiting_queue` | id, restaurant_id, visit_id, party_size, requested_zone, status, queue_position, joined_at, estimated_wait_minutes |
| `customers` | id, name, phone, email, memory_enabled, created_at, last_visit_at |
| `customer_face_memory` | id, customer_id, face_embedding (vector), consent_status, consent_timestamp, revoked_at |
| `customer_preferences` | customer_id, preferred_zone, usual_party_size |
| `feedback` | id, visit_id, food_rating, service_rating, wait_rating, overall_rating, sentiment, comment |
| `conversation_sessions` | id, session_id, restaurant_id, customer_id, state, created_at |
| `conversation_messages` | id, session_id, role, content, timestamp |
| `consent_events` | id, customer_id, session_id, consent_type, action, timestamp, policy_version |
| `audit_events` | id, entity_type, entity_id, action, performed_by, timestamp |
| `staff_requests` | id, session_id, reason, summary, status, ticket_id, created_at |

> [!IMPORTANT]
> There is **no `RESERVED` table state**. The only states are:
> `AVAILABLE → OCCUPIED → ORDERING → DINING → BILL_REQUESTED → PAYMENT_PENDING → CLEANING → READY → AVAILABLE`

---

### Phase 2 — Backend Services

#### [NEW] `backend/app/services/table_service.py`
- Get all table states
- Find available table by party size + zone
- Atomic table state transition with optimistic locking
- OUT_OF_SERVICE management (staff only)

#### [NEW] `backend/app/services/seating_service.py`
- `find_available_table(party_size, zone)` — returns best match or `NO_SUITABLE_TABLE`
- `seat_customer(table_id, party_size, session_id)` — atomic commit with re-check (prevents race conditions)
- Returns `TABLE_NO_LONGER_AVAILABLE` if table was taken between check and commit

#### [NEW] `backend/app/services/queue_service.py`
- `add_to_queue(party_size, zone, session_id)`
- FIFO ordering with compatible table matching
- `notify_next_compatible_party()` — called when a table becomes READY
- Queue status transitions: `WAITING → CALLED → SEATED / LEFT / CANCELLED`

#### [NEW] `backend/app/services/knowledge_service.py`
- Structured lookup (hours, policies, menu) from PostgreSQL
- Vector similarity search (pgvector) for natural language queries
- Returns `found=false` if no sufficiently relevant result; never fabricates

#### [NEW] `backend/app/services/feedback_service.py`
- Store structured feedback from LLM extraction
- Null fields allowed — never fabricate a numeric rating not given

#### [NEW] `backend/app/services/consent_service.py`
- `request_consent(session_id)` — initiates consent dialog
- `record_consent(customer_id, action)` — GRANTED / REVOKED / DELETED
- Audit event written for every consent change

#### [NEW] `backend/app/services/face_memory_service.py`
- Enrollment: detect face → generate embedding → store (no raw image by default)
- Recognition: camera frame → embedding → similarity search (opted-in profiles only)
- Revocation: mark disabled, remove from active search, delete embedding, write audit

#### [NEW] `backend/app/services/escalation_service.py`
- Create staff assistance ticket
- Notify manager dashboard via WebSocket event

#### [NEW] `backend/app/services/wait_estimation_service.py`
- Deterministic wait-time calculation using live table state + configured rules
- Returns estimate range + confidence level (`low / medium / high`)
- LLM must label output as an estimate, never a guarantee

---

### Phase 3 — Tool Gateway & Tool Schemas

#### [NEW] `backend/app/tools/` — Tool definitions (11 canonical tools)

| Tool | Purpose |
|---|---|
| `get_live_table_state` | Read-only: all table statuses |
| `find_available_table` | Check availability for party size + zone |
| `seat_customer` | Atomic seating with re-check |
| `estimate_wait_time` | Backend-computed wait estimate |
| `add_to_waiting_queue` | Add current waiting party to queue |
| `get_restaurant_information` | RAG knowledge retrieval |
| `request_memory_consent` | Begin opt-in consent flow |
| `save_customer_memory` | Enroll face (post-consent only) |
| `find_opted_in_customer` | Face similarity search (consented only) |
| `record_feedback` | Store post-visit feedback |
| `request_staff_assistance` | Escalate to human |

#### [NEW] `backend/app/api/routes/` — FastAPI route files
- `tables.py`, `queue.py`, `customers.py`, `feedback.py`, `knowledge.py`, `staff.py`

#### [NEW] `backend/app/api/websocket.py`
- Real-time session management
- Push table/queue updates to Manager Dashboard

---

### Phase 4 — Conversation Agent (LLM)

#### [NEW] `backend/app/agents/receptionist_agent.py`
- LLM agent with tool-calling enabled
- Conversation state machine:

```
GREETING → UNDERSTAND_REQUEST → [CLARIFYING] → CHECKING_SYSTEM
→ RESPONDING → SEATING / WAITING / INFORMATION / FEEDBACK / MEMORY
→ COMPLETED / ESCALATED
```

- Tool result → LLM response pipeline
- Grounded responses: every operational claim backed by a tool result
- Never claims success unless `success: true` returned by backend

#### [NEW] `backend/app/agents/prompts.py`
- System prompt enforcing all non-negotiable rules (Section 34 of architecture)
- Version-controlled; covered by hallucination regression tests

#### [NEW] `backend/app/agents/schemas.py`
- Pydantic models for all tool inputs/outputs
- Server-side validation before any tool executes

---

### Phase 5 — Voice Integration (Real-Time)

#### [NEW] `backend/app/services/voice_service.py`
- Real-time audio streaming pipeline
- STT: transcribe incoming speech
- TTS: convert agent response to speech
- Turn detection + barge-in/interruption handling
- Session lifecycle management (session_id per customer interaction)
- Graceful degradation: if voice service fails → show UI text message

---

### Phase 6 — Camera & Face Pipeline

#### [NEW] `backend/app/services/camera_service.py`
- Camera frame capture (enrollment-time and recognition-time)
- Face detection → embedding generation
- Passes server-side reference (never raw biometric) to memory service

**Privacy controls enforced:**
- `RAW_FACE_IMAGE_STORAGE = false` (default)
- Only embeddings stored
- Only opted-in profiles searched
- Low confidence → treat as unknown guest, no name guessing
- Embeddings never exposed to LLM or conversation logs

---

### Phase 7 — Frontend: Receptionist UI

#### [NEW] `frontend/src/pages/Receptionist.tsx`
- Full-screen kiosk-style layout
- Animated avatar (listening / thinking / speaking / idle states)
- Conversation transcript panel
- Visual status indicators

#### [NEW] `frontend/src/components/ReceptionistAvatar.tsx`
- Visual state: listening 🎙️ / thinking 🤔 / speaking 🗣️ / checking ⏳ / waiting for staff 👤

#### [NEW] `frontend/src/components/ConsentDialog.tsx`
- Explicit opt-in consent UI for face memory enrollment
- Clear "Yes / No" choice; no pre-checked defaults

#### [NEW] `frontend/src/components/TableStatus.tsx`
#### [NEW] `frontend/src/components/QueueStatus.tsx`

---

### Phase 8 — Manager Dashboard

#### [NEW] `frontend/src/pages/ManagerDashboard.tsx`

**Panels:**

| Panel | Contents |
|---|---|
| Live Table Map | Color-coded table states, real-time via WebSocket |
| Waiting Queue | Current waiting parties, positions, estimated wait |
| Active Visits | Seated parties and duration |
| Feedback Summary | Ratings + sentiment trends |
| Common Questions | Most-asked knowledge base queries |
| Staff Requests | Open escalation tickets |
| Memory/Consent Events | Summary (no raw biometrics) |
| System Health | Voice, DB, face service statuses |

---

### Phase 9 — Security Hardening

- Secrets in `.env` / secret manager only — never in source code
- Role-based access: `PUBLIC_SESSION / STAFF / MANAGER / ADMIN`
- Rate limiting on all public endpoints
- Input validation + output encoding on all routes
- Audit logs for all privileged actions (consent, table overrides, memory deletion)
- Encryption in transit (HTTPS/WSS) and at rest where supported
- No biometric data in application logs
- Idempotency keys on all state-changing operations

---

### Phase 10 — Testing

#### [NEW] `backend/tests/unit/`
- Table state transition rules
- Party-size matching logic
- Queue ordering (FIFO)
- Wait-time calculation
- Consent enforcement (no memory before consent)
- Memory deletion flow
- Confidence threshold behavior (low → treat as unknown)
- Feedback extraction (null allowed, no fabrication)

#### [NEW] `backend/tests/integration/`
- `available table → seat_customer → OCCUPIED`
- `table taken mid-conversation → retry with new availability check`
- `no table → add to queue → table ready → seat`
- `consent false → enrollment rejected`
- `consent revoked → face excluded from search`
- `feedback stored with null fields`

#### [NEW] `backend/tests/e2e/`
- Simulated full conversation flows (Scenarios A–G from architecture)

#### [NEW] `backend/tests/hallucination/`
- Fixed question set where KB has no answer → assert AI does NOT fabricate
- Assert AI does NOT claim reservation capability
- Assert AI does NOT identify below-threshold face match

---

### Phase 11 — Docker & CI/CD

#### [NEW] `Dockerfile` (backend)
#### [NEW] `Dockerfile` (frontend)
#### [NEW] `docker-compose.yml` (full stack: backend + frontend + postgres + redis)
#### [NEW] `.github/workflows/ci.yml`
- Lint → Unit tests → Integration tests → Build → (optional) Deploy

---

## Verification Plan

### Automated Tests
```bash
# Backend unit + integration tests
pytest backend/tests/

# Hallucination regression suite
pytest backend/tests/hallucination/

# Frontend build check
cd frontend && npm run build
```

### Manual Verification (per phase)

| Phase | Verification |
|---|---|
| DB Models | Run migrations cleanly; verify schema in psql |
| Table Service | Confirm no RESERVED state exists; test all state transitions |
| Seating | Simulate two simultaneous customers competing for last table → only one succeeds |
| Queue | Add 3 parties → table becomes ready → confirm FIFO next-party selection |
| Knowledge | Ask a question not in KB → confirm AI says "I can't confirm" |
| Feedback | Give verbal feedback → confirm null rating fields not fabricated |
| Face Memory | Attempt enrollment without consent → confirm rejected |
| Face Recognition | Low-confidence match → confirm AI greets as unknown |
| Voice | Speak mid-response (barge-in) → confirm interruption handled |
| Race Condition | Parallel seat requests for same table → confirm atomic rejection |

---

## Build Order Summary

```text
1.  Project skeleton + Docker Compose
2.  Database models + Alembic migrations
3.  Table state machine + seating service
4.  Waiting queue service + wait estimation
5.  Restaurant knowledge service (RAG)
6.  Feedback service
7.  Consent service
8.  Customer memory + face embedding service
9.  Tool schemas + backend tool gateway
10. Conversation agent (LLM + tool-calling)
11. Voice integration (STT / TTS / streaming)
12. Camera + face pipeline
13. Receptionist UI (frontend)
14. Manager dashboard (frontend)
15. Unit + integration + hallucination tests
16. Security hardening + RBAC
17. Docker production images
18. CI/CD pipeline
```

---

## Definition of Done

The system is complete only when all of these pass:

- [ ] Customer can speak; receptionist responds naturally in voice
- [ ] Restaurant FAQ answered from verified knowledge only
- [ ] Live table availability comes from backend (never LLM guess)
- [ ] Customer seated immediately when a suitable table is free
- [ ] Customer added to queue when no table is free
- [ ] Queue is NOT treated as a reservation
- [ ] Table state transitions are deterministic and auditable
- [ ] Wait times are backend estimates (never LLM guesses)
- [ ] Feedback collected and stored (null fields allowed)
- [ ] Customer memory requires explicit opt-in
- [ ] Face matching searches only active opted-in profiles
- [ ] Low-confidence face match → customer treated as unknown
- [ ] Customer can revoke/delete memory
- [ ] LLM cannot directly access the database
- [ ] All state-changing operations validated server-side
- [ ] Failures produce no false success messages
- [ ] Automated tests cover all critical business rules
- [ ] Logs contain no raw biometric data
