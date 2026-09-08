# BUILD INSTRUCTION — AI RESTAURANT RECEPTIONIST PROTOTYPE

## 1. PROJECT GOAL

Build a clean, production-structured prototype of an **AI Restaurant Receptionist**.

The purpose of this prototype is to validate the following end-to-end flow:

```text
Customer speaks
      ↓
Speech recognition
      ↓
AI receptionist understands request
      ↓
Backend / Database / RAG retrieves verified restaurant information
      ↓
LLM generates a grounded response
      ↓
Response converted to speech
      ↓
Customer hears receptionist response
```

The main objective is to test:

1. Real-time speech recognition
2. Natural conversational responses
3. LLM tool/function calling
4. Backend integration
5. Database retrieval
6. RAG/knowledge retrieval
7. Strict grounding / hallucination prevention
8. Clean receptionist UI

This is a PROTOTYPE.

Do NOT implement unnecessary production features yet.

---

# 2. IMPORTANT SCOPE LIMITS

## IMPLEMENT NOW

### Frontend
- Clean receptionist screen
- Voice interaction UI
- Microphone input
- Listening state
- Thinking/checking state
- Speaking state
- Conversation transcript
- Receptionist placeholder/avatar area
- Connection/system status
- Minimal restaurant branding
- Responsive layout

### Backend
- FastAPI
- REST/WebSocket communication where appropriate
- Conversation session management
- LLM integration
- Tool calling
- Restaurant information retrieval
- Table availability retrieval
- RAG pipeline
- Hallucination protection
- Structured logging
- Error handling

### Database
Use a local PostgreSQL database through Docker Compose.

Create realistic seeded restaurant data for the prototype.

### AI
Use OpenAI as the LLM provider.

Use OpenAI Realtime API for the voice conversation layer.

### RAG
Implement a real RAG pipeline.

The receptionist must be capable of answering restaurant questions using the restaurant's stored information.

---

# 3. DO NOT IMPLEMENT YET

These features are OUT OF SCOPE for this prototype:

- Face recognition
- Face embeddings
- Customer face memory
- Customer biometric storage
- Consent workflow for biometrics
- Manager dashboard
- SMS notifications
- WhatsApp notifications
- Push notifications
- Restaurant reservations
- Reservation scheduling
- Cloud deployment
- Unreal Engine
- MetaHuman
- 3D avatar
- Advanced analytics
- Payment integration
- POS integration
- Ordering system

Create clean interfaces/placeholders so these can be added later without restructuring the project.

---

# 4. CORE ARCHITECTURAL PRINCIPLE

THIS RULE IS NON-NEGOTIABLE:

> The LLM handles conversation and reasoning.
> Deterministic backend services handle restaurant truth and operations.

The LLM MUST NOT invent:

- table availability
- table numbers
- restaurant opening hours
- menu items
- prices
- ingredients
- allergens
- restaurant policies
- facilities
- wait times
- restaurant capabilities

Every factual restaurant-specific answer must come from the database or approved knowledge base.

---

# 5. TECHNOLOGY STACK

Use:

```text
Frontend:
React
TypeScript
Vite
Tailwind CSS

Backend:
Python
FastAPI
Pydantic

Database:
PostgreSQL
pgvector

Cache/session support:
Redis

AI:
OpenAI

Voice:
OpenAI Realtime API

RAG:
Embeddings
pgvector
retrieval service

Infrastructure:
Docker Compose

Testing:
pytest
```

Do not introduce additional frameworks unless they provide a clear technical necessity.

Keep the architecture simple.

---

# 6. SYSTEM ARCHITECTURE

Implement this architecture:

```text
                         CUSTOMER
                            │
                            │ voice
                            ▼
                  ┌────────────────────┐
                  │ Receptionist UI    │
                  │ React + TypeScript │
                  └─────────┬──────────┘
                            │
                            │ realtime audio
                            ▼
                  ┌────────────────────┐
                  │ Voice / AI Layer   │
                  │ OpenAI Realtime    │
                  └─────────┬──────────┘
                            │
                            │ intent / tool call
                            ▼
                  ┌────────────────────┐
                  │ FastAPI Backend    │
                  │ Tool Gateway       │
                  └─────────┬──────────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
       Restaurant       Table Service   RAG Service
       Information          │              │
             │              │              │
             └──────────────┼──────────────┘
                            │
                            ▼
                    PostgreSQL
                     + pgvector
```

The frontend must never directly access PostgreSQL.

The LLM must never directly access PostgreSQL.

All database access goes through backend services.

---

# 7. DATABASE

Use PostgreSQL locally through Docker Compose.

Seed one fictional restaurant.

Example:

```text
Restaurant:
Aria Kitchen
```

Create realistic data.

## Required data

### restaurants

```text
id
name
address
phone
timezone
description
```

### restaurant_hours

```text
id
restaurant_id
day_of_week
open_at
close_at
is_closed
```

### restaurant_policies

```text
id
restaurant_id
key
value
```

Examples:

```text
reservation_policy
children_policy
pet_policy
parking
payment_methods
cancellation_policy
outside_food_policy
accessibility
```

### menu_items

```text
id
restaurant_id
name
category
description
price
ingredients
allergens
is_vegetarian
is_vegan
is_available
```

### restaurant_tables

```text
id
restaurant_id
table_number
capacity
zone
status
```

For the prototype use:

```text
AVAILABLE
OCCUPIED
CLEANING
READY
OUT_OF_SERVICE
```

DO NOT add reservation functionality.

There is NO RESERVED state.

### knowledge_documents

```text
id
restaurant_id
title
content
embedding
metadata
```

Populate this with restaurant information that benefits from natural-language retrieval.

---

# 8. TABLE LOGIC FOR PROTOTYPE

The receptionist must be able to answer:

> "Do you have a table for four?"

The backend should determine this.

Example tool:

```text
find_available_table(party_size, zone?)
```

The tool must query PostgreSQL.

Example response:

```json
{
  "success": true,
  "available": true,
  "table_number": 12,
  "capacity": 4,
  "zone": "indoor"
}
```

If no suitable table exists:

```json
{
  "success": true,
  "available": false
}
```

The LLM must base its response ONLY on this result.

Example:

Customer:

> "Do you have a table for four?"

Tool:

```json
{
  "available": false
}
```

AI:

> "We don't have a suitable table available right now."

The AI must NOT invent a table or availability.

---

# 9. RAG SYSTEM

Implement real retrieval-augmented generation.

Do NOT simply put all restaurant information into the system prompt.

The system should work like:

```text
Customer question
       ↓
Question understanding
       ↓
Retrieve relevant restaurant information
       ↓
PostgreSQL / pgvector
       ↓
Relevant documents
       ↓
LLM
       ↓
Grounded response
```

Use pgvector for semantic retrieval.

Examples of questions:

```text
"What time do you close?"

"Do you have vegetarian food?"

"Do you have vegan options?"

"Do you have parking?"

"Do you have high chairs?"

"Can I bring my dog?"

"What payment methods do you accept?"

"Do you have gluten-free dishes?"
```

For structured information such as restaurant hours and exact table status, prefer direct database queries over semantic retrieval.

For natural-language policies and general restaurant knowledge, use RAG.

---

# 10. RAG GROUNDING RULE

The RAG service must return:

```json
{
  "found": true,
  "sources": [
    {
      "id": "...",
      "title": "...",
      "content": "...",
      "score": 0.91
    }
  ]
}
```

If retrieval confidence is below the configured threshold:

```json
{
  "found": false,
  "sources": []
}
```

When `found=false`, the LLM MUST NOT invent an answer.

It should respond naturally:

> "I don't have verified information about that right now."

OR:

> "I'm not able to confirm that from the restaurant information I have."

Do NOT generate a plausible answer.

---

# 11. LLM TOOL CALLING

Create a controlled tool gateway.

Initial tools:

```text
get_restaurant_information
find_available_table
get_live_table_state
```

Future tools can be added later.

Each tool must have:

- Strict input schema
- Strict output schema
- Server-side validation
- Error handling
- Logging
- No direct database access from the LLM

Example:

```text
LLM
 ↓
find_available_table
 ↓
FastAPI tool gateway
 ↓
table_service.py
 ↓
PostgreSQL
 ↓
structured result
 ↓
LLM
 ↓
spoken response
```

---

# 12. ANTI-HALLUCINATION RULES

These are NON-NEGOTIABLE.

## RULE 1

Never invent restaurant facts.

## RULE 2

Never invent table availability.

## RULE 3

Never claim an action succeeded unless the backend returns success.

## RULE 4

Never fabricate prices.

## RULE 5

Never fabricate menu items.

## RULE 6

Never fabricate opening hours.

## RULE 7

Never fabricate allergens or ingredients.

## RULE 8

Never claim the restaurant provides a service unless verified.

## RULE 9

When information is unavailable, explicitly say it cannot be confirmed.

## RULE 10

The LLM must never directly query PostgreSQL.

## RULE 11

The frontend must never directly query PostgreSQL.

## RULE 12

Tool failures must never become fake successful responses.

Example:

Backend:

```json
{
  "success": false,
  "error_code": "DATABASE_UNAVAILABLE"
}
```

The AI MUST NOT say:

> "Yes, we have a table."

Instead:

> "I'm having trouble checking the restaurant system right now."

---

# 13. CONVERSATION STATE MACHINE

Implement a simple state machine:

```text
IDLE
  ↓
LISTENING
  ↓
UNDERSTANDING
  ↓
TOOL_CALLING
  ↓
RESPONDING
  ↓
SPEAKING
  ↓
IDLE
```

Possible error state:

```text
ERROR
```

Possible escalation placeholder:

```text
STAFF_ASSISTANCE
```

Do not implement full staff dashboard yet.

---

# 14. VOICE BEHAVIOR

Use OpenAI Realtime API.

The receptionist should support:

- microphone input
- realtime speech recognition
- natural voice response
- interruption/barge-in
- turn detection
- session management

The customer should be able to speak naturally.

The UI should show:

```text
Listening...
Thinking...
Checking restaurant information...
Speaking...
```

Avoid forcing the customer to type.

Typing can exist as a development fallback.

---

# 15. CLEAN RECEPTIONIST UI

The frontend is important.

The prototype should look like a real restaurant AI receptionist kiosk, not a developer dashboard.

## Main screen

Use a clean fullscreen layout.

Structure:

```text
┌─────────────────────────────────────────────┐
│                                             │
│              ARIA KITCHEN                   │
│                                             │
│                                             │
│            ┌──────────────┐                 │
│            │              │                 │
│            │   AVATAR     │                 │
│            │ PLACEHOLDER  │                 │
│            │              │                 │
│            └──────────────┘                 │
│                                             │
│          "How can I help you?"              │
│                                             │
│           ● Listening / Ready               │
│                                             │
│      ┌─────────────────────────────┐        │
│      │ Customer: Do you have...    │        │
│      │ Receptionist: Yes, we...    │        │
│      └─────────────────────────────┘        │
│                                             │
│             🎙 Microphone                   │
│                                             │
└─────────────────────────────────────────────┘
```

Do not make it cluttered.

The receptionist should be the visual focus.

---

# 16. AVATAR PLACEHOLDER

For this prototype, DO NOT implement a 3D avatar.

Create:

```text
ReceptionistAvatar.tsx
```

The component should support these visual states:

```text
idle
listening
thinking
speaking
error
```

Use a clean placeholder visual such as:

- professional receptionist silhouette
- abstract human avatar
- elegant circular animated placeholder

Do not create a complicated character system.

IMPORTANT:

Design this component behind an abstraction so that later it can be replaced with:

```text
React animated avatar
        ↓
Unreal Engine / MetaHuman
```

without changing the AI/backend architecture.

---

# 17. UI STATES

Implement visually distinct states.

### IDLE

```text
"Welcome. How can I help you?"
```

### LISTENING

```text
"Listening..."
```

Animate microphone indicator.

### THINKING

```text
"Let me check that for you..."
```

### SPEAKING

Show active voice/speaking indicator.

### ERROR

Example:

```text
"I'm having trouble connecting to the restaurant system."
```

Never show raw stack traces to the customer.

---

# 18. DEVELOPMENT FALLBACK

Because realtime voice can fail during development, provide a developer fallback:

```text
Text input
      ↓
same conversation pipeline
      ↓
same backend
      ↓
same tools
      ↓
same LLM
```

This allows backend/RAG/LLM testing without microphone hardware.

The text mode must use the EXACT same agent and tools as the voice mode.

---

# 19. API DESIGN

Create clean backend APIs.

Example:

```text
GET /health

GET /api/restaurant

GET /api/tables

POST /api/conversation/session

POST /api/tools/find-available-table

POST /api/tools/restaurant-information

POST /api/rag/search

WebSocket /ws/receptionist/{session_id}
```

Do not expose internal database implementation details through the frontend.

---

# 20. PROJECT STRUCTURE

Create this structure:

```text
ai-restaurant-receptionist/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── health.py
│   │   │   │   ├── restaurant.py
│   │   │   │   ├── tables.py
│   │   │   │   └── conversation.py
│   │   │   └── websocket.py
│   │   │
│   │   ├── agents/
│   │   │   ├── receptionist_agent.py
│   │   │   ├── prompts.py
│   │   │   └── schemas.py
│   │   │
│   │   ├── tools/
│   │   │   ├── restaurant_information.py
│   │   │   ├── table_availability.py
│   │   │   └── table_state.py
│   │   │
│   │   ├── services/
│   │   │   ├── llm_service.py
│   │   │   ├── voice_service.py
│   │   │   ├── restaurant_service.py
│   │   │   ├── table_service.py
│   │   │   └── rag_service.py
│   │   │
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   ├── models.py
│   │   │   └── seed.py
│   │   │
│   │   └── config/
│   │       ├── settings.py
│   │       └── logging.py
│   │
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── hallucination/
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ReceptionistAvatar.tsx
│       │   ├── ConversationPanel.tsx
│       │   ├── VoiceIndicator.tsx
│       │   └── SystemStatus.tsx
│       │
│       ├── pages/
│       │   └── Receptionist.tsx
│       │
│       ├── services/
│       │   ├── api.ts
│       │   └── websocket.ts
│       │
│       └── types/
│           └── receptionist.ts
│
├── database/
│   └── seed/
│
├── docker-compose.yml
├── .env.example
├── README.md
└── .gitignore
```

Keep responsibilities separated.

---

# 21. ENVIRONMENT VARIABLES

Create `.env.example`.

Example:

```env
OPENAI_API_KEY=

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/restaurant_ai

REDIS_URL=redis://localhost:6379

RESTAURANT_ID=
```

Never hard-code API keys.

Never commit `.env`.

---

# 22. TEST RESTAURANT DATA

Seed enough data to realistically test conversations.

Include:

### Restaurant

```text
Aria Kitchen
```

### Hours

Use realistic opening hours.

### Tables

At least 10 tables.

Use different capacities:

```text
2
2
2
4
4
4
6
6
8
8
```

Use statuses such as:

```text
AVAILABLE
OCCUPIED
CLEANING
READY
```

### Menu

At least:

```text
10-20 menu items
```

Include categories, prices, ingredients, allergens, vegetarian/vegan status.

### Policies

Include:

```text
opening hours
parking
children
high chairs
pets
payment methods
accessibility
outside food
waiting policy
```

### Knowledge documents

Create natural-language restaurant documents so RAG can be demonstrated.

---

# 23. CONVERSATION EXAMPLES TO SUPPORT

The prototype must support conversations like:

### Example 1

Customer:

> "Hi, do you have a table for four?"

System:

```text
LLM → find_available_table(4)
Backend → available
LLM → natural response
```

---

### Example 2

Customer:

> "What time do you close?"

System:

```text
LLM → get_restaurant_information
RAG/DB → verified hours
LLM → grounded answer
```

---

### Example 3

Customer:

> "Do you have vegetarian food?"

System retrieves menu data and responds only using verified menu information.

---

### Example 4

Customer:

> "Can I bring my dog?"

System retrieves pet policy.

---

### Example 5

Customer:

> "Do you have parking?"

System retrieves parking information.

---

### Example 6

Customer asks something nonexistent:

> "Do you have a rooftop swimming pool?"

There is no such information.

The system MUST NOT say:

> "Yes."

or:

> "No, we don't."

unless the knowledge base actually contains verified information supporting that answer.

Correct behavior:

> "I don't have verified information about a rooftop swimming pool."

---

### Example 7

Customer:

> "Can you reserve me a table for 8 PM?"

The restaurant does not support reservations.

The AI MUST NOT pretend to create one.

Correct response:

> "We don't currently take reservations. I can check whether a suitable table is available when you arrive."

---

# 24. HALLUCINATION REGRESSION TESTS

Create automated tests.

Examples:

```text
Question:
"What is your rooftop pool policy?"

Expected:
No fabricated answer.

Question:
"Can I reserve Table 5 for 8 PM?"

Expected:
No reservation claim.

Question:
"Do you have a table for 10?"

Expected:
Backend availability result only.

Question:
"What is the price of an item that doesn't exist?"

Expected:
Cannot confirm.

Question:
"Do you offer helicopter parking?"

Expected:
Cannot confirm.
```

Tests should verify that the AI does not generate unsupported restaurant facts.

---

# 25. ERROR HANDLING

Handle:

```text
OpenAI unavailable
Database unavailable
Redis unavailable
RAG failure
Tool failure
Microphone unavailable
WebSocket disconnect
Invalid tool input
Timeout
```

The customer should always receive a safe response.

Never expose:

```text
Python traceback
database credentials
API errors
internal prompts
raw SQL
stack traces
```

---

# 26. LOGGING

Use structured logs.

Log:

```text
session_id
timestamp
conversation state
tool name
tool success/failure
latency
RAG retrieval score
error code
```

Do NOT log API secrets.

Do NOT log biometric information.

Face recognition is not part of this prototype anyway.

---

# 27. SECURITY

Implement basic security now:

- `.env` for secrets
- input validation
- Pydantic schemas
- CORS configured correctly
- no direct database access from frontend
- no API key in frontend source
- no secrets in Git
- parameterized queries / ORM
- safe error responses

Do not over-engineer authentication for this prototype.

---

# 28. DEVELOPMENT ORDER

Follow this exact order.

## STEP 1

Create project structure.

## STEP 2

Create Docker Compose.

Start:

```text
PostgreSQL
Redis
```

## STEP 3

Create database models.

## STEP 4

Create migrations.

## STEP 5

Seed fictional restaurant data.

## STEP 6

Implement table service.

## STEP 7

Implement restaurant information service.

## STEP 8

Implement pgvector RAG.

## STEP 9

Implement OpenAI LLM integration.

## STEP 10

Implement tool calling.

## STEP 11

Implement hallucination protections.

## STEP 12

Implement text-based conversation testing.

## STEP 13

Implement OpenAI Realtime voice.

## STEP 14

Connect voice to the same agent/tool pipeline.

## STEP 15

Create clean receptionist UI.

## STEP 16

Connect UI to backend.

## STEP 17

Add listening/thinking/speaking states.

## STEP 18

Add automated tests.

## STEP 19

Run complete end-to-end testing.

---

# 29. CRITICAL IMPLEMENTATION RULE

Do NOT start by building the visual avatar.

The order of importance is:

```text
1. Backend correctness
2. Database correctness
3. RAG correctness
4. Tool calling correctness
5. LLM grounding
6. Speech recognition
7. Speech response
8. UI polish
9. Avatar replacement later
```

The prototype is successful even with a placeholder avatar.

It is NOT successful if it looks beautiful but invents restaurant information.

---

# 30. DEFINITION OF DONE

The prototype is complete when:

- [ ] React receptionist page works
- [ ] Placeholder avatar works
- [ ] Microphone input works
- [ ] Speech recognition works
- [ ] AI responds with voice
- [ ] Text fallback works
- [ ] FastAPI backend works
- [ ] PostgreSQL works
- [ ] Restaurant data is seeded
- [ ] Table availability can be checked
- [ ] RAG retrieval works
- [ ] LLM can call backend tools
- [ ] Restaurant information is grounded
- [ ] Unsupported questions do not cause fabricated answers
- [ ] Reservation requests are correctly rejected because reservations do not exist
- [ ] Tool/database failures never produce fake success messages
- [ ] Conversation states are visible in UI
- [ ] Automated hallucination tests pass
- [ ] Docker Compose starts the local system
- [ ] README explains setup and architecture

---

# 31. FINAL DESIGN PRINCIPLE

The prototype should feel like:

> **A real restaurant receptionist powered by AI**

not:

> **A chatbot placed inside a restaurant website.**

The user experience should be conversational and simple.

The technical architecture should remain strict:

```text
              CUSTOMER
                  ↓
               VOICE
                  ↓
          OPENAI REALTIME
                  ↓
           RECEPTIONIST AGENT
                  ↓
            TOOL GATEWAY
                  ↓
        ┌─────────┴──────────┐
        ↓                    ↓
 RESTAURANT DB              RAG
        ↓                    ↓
        └─────────┬──────────┘
                  ↓
          VERIFIED TOOL RESULT
                  ↓
             LLM RESPONSE
                  ↓
              VOICE OUTPUT
                  ↓
              CUSTOMER
```

DO NOT deviate from this architecture without a clear technical reason.

When making implementation decisions not explicitly covered above, prefer:
1. Simplicity
2. Deterministic behavior
3. Testability
4. Separation of concerns
5. Extensibility for future 3D avatar, face memory, manager dashboard, and production deployment

Build the prototype accordingly.