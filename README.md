# Healthcare CRM — AI-First HCP Interaction Logging

Enterprise-grade Healthcare CRM module where **the AI Assistant is the only interface** for creating and editing HCP interactions. The left panel is a structured, read-only CRM form synchronized in real time from LangGraph agent responses.

## Project Overview

Medical representatives describe interactions in natural language. A LangGraph agent powered by **Groq (`llama-3.1-8b-instant`)** plans, reasons, routes tools, validates output, and updates an interaction draft. The React frontend reflects those updates instantly without manual form editing. Interactions remain in **draft** until explicitly saved to PostgreSQL.

### Key Capabilities

- Split-screen UI (65/35 desktop, 60/40 tablet, stacked mobile)
- AI-controlled read-only interaction form with field-level highlight animations
- SSE streaming chat with typing indicator and token display
- Five LangGraph tools: Log, Edit, Search HCP, Materials/Samples, Outcome/Follow-up
- Full REST API with consistent response envelope
- PostgreSQL persistence with repository pattern and Alembic migrations

## Architecture Diagram

```mermaid
flowchart TB
    subgraph Frontend["React Frontend"]
        UI[Split Screen UI]
        Redux[Redux Store]
        UI --> Redux
    end

    subgraph Backend["FastAPI Backend"]
        API[REST API Layer]
        SVC[Service Layer]
        REPO[Repository Layer]
        API --> SVC --> REPO
    end

    subgraph AI["LangGraph Agent"]
        PLAN[Planner]
        REASON[Intent Reasoner]
        ROUTE[Tool Router]
        EXEC[Tool Executor]
        VAL[Validator]
        UPD[State Updater]
        RESP[Response Generator]
        PLAN --> REASON --> ROUTE
        ROUTE --> EXEC --> VAL
        VAL --> UPD --> RESP
        ROUTE --> RESP
    end

  subgraph DB[(PostgreSQL)]
  end

    UI -->|POST /chat/stream| API
    API -->|invoke| AI
    AI -->|draft patch| API
    API -->|JSON| Redux
    Redux -->|render| UI
    SVC --> REPO --> DB
    EXEC --> REPO
```

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React 19, TypeScript, Vite, Redux Toolkit, TailwindCSS v4, shadcn/ui, Framer Motion, Sonner |
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2.x async, Alembic |
| Database | PostgreSQL 16 |
| AI | LangGraph, LangChain, Groq (`llama-3.1-8b-instant`, fallback `llama-3.3-70b-versatile`) |
| Infra | Docker Compose |

## Folder Structure

```
CRM-HCP/
├── frontend/src/
│   ├── components/       # UI, chat, interaction, layout
│   ├── hooks/            # useChatActions, useAppBootstrap
│   ├── pages/            # LogInteractionPage, HomePage
│   ├── services/         # Axios API clients
│   ├── store/            # Redux slices + thunks
│   └── types/            # TypeScript contracts
├── backend/app/
│   ├── api/              # FastAPI routes
│   ├── core/             # DI, middleware, exceptions
│   ├── langgraph/        # Graph, nodes, tools, state
│   ├── prompts/          # Prompt engineering layer
│   ├── models/           # SQLAlchemy ORM
│   ├── repositories/     # Data access
│   ├── schemas/          # Pydantic DTOs
│   └── services/         # Business logic
├── backend/scripts/      # seed_database.py
├── backend/alembic/      # Migrations
├── docs/                 # Architecture, demo, interview prep
└── docker-compose.yml
```

## Prerequisites

- Node.js 20+
- Python 3.12+
- Docker Desktop
- [Groq API key](https://console.groq.com/)

## Environment Variables

Copy templates and configure:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key (required for AI) |
| `GROQ_MODEL_NAME` | Primary model (`llama-3.1-8b-instant`) |
| `DATABASE_URL` | Async PostgreSQL URL |
| `VITE_API_BASE_URL` | Frontend API base (`/api` uses Vite proxy) |
| `VITE_DEMO_USER_ID` | Demo user UUID (`00000000-0000-0000-0000-000000000001`) |

## Setup Instructions

### 1. Start PostgreSQL

```bash
docker compose up -d
```

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
python scripts/seed_database.py
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

## API Documentation

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Application metadata |
| GET | `/health` | Health + database status |
| POST | `/chat` | Process message via LangGraph |
| POST | `/chat/stream` | SSE streaming chat |
| POST | `/interaction/save` | Persist interaction draft |
| GET | `/interaction/{id}` | Get full interaction |
| GET | `/hcp/search` | Search healthcare professionals |
| GET | `/hcp/{id}/history` | HCP interaction history |

Swagger UI: **http://localhost:8000/docs**

### Example Chat Request

```json
{
  "message": "I met Dr Sharma today to discuss CardioMax efficacy.",
  "conversation_id": null,
  "user_id": "00000000-0000-0000-0000-000000000001"
}
```

## LangGraph Overview

```
START → planner → intent_reasoner → tool_router
  → tool_executor → validator → state_updater → response_generator → END
  → response_generator → END (when no tool)
```

**Design principles:**
- FastAPI never selects tools or detects intent
- Tool routing is LLM-driven via structured outputs
- No keyword matching, regex extraction, or hardcoded intent logic
- All prompts live in `backend/app/prompts/`

### Five Tools

| Tool | Purpose |
|------|---------|
| `log_interaction` | Create interaction draft from conversation |
| `edit_interaction` | Patch specific draft fields |
| `search_hcp` | Find HCPs with interaction history |
| `materials_and_samples` | Update materials/samples lists |
| `outcome_and_followup` | Update outcomes, follow-up, sentiment |

## How AI Updates the Form

1. User sends a message in the AI chat panel
2. Frontend calls `POST /chat/stream` (SSE)
3. LangGraph executes planner → reasoner → router → tool → validator → updater
4. Backend returns `interaction_draft` patch in the response
5. Redux `interactionSlice` merges only changed fields
6. `uiSlice` highlights modified fields for 2.5 seconds
7. Read-only form re-renders affected fields only (memoized components)

**Save is explicit:** Draft state persists in conversation metadata until the user clicks **Save Interaction**.

## Testing

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm run test
```

## Scripts

| Command | Description |
|---------|-------------|
| `python scripts/seed_database.py` | Seed demo user, HCPs, catalogs |
| `alembic upgrade head` | Apply migrations |
| `npm run build` | Production frontend build |

## Security Notes

- JWT auth is prepared via `get_current_user()` placeholder (`X-User-Id` header)
- Change `SECRET_KEY` in production
- Configure `CORS_ORIGINS` for deployment domains
- Never commit `.env` with real API keys

## Future Improvements

- JWT authentication and role-based access
- LangGraph checkpointing for durable agent state
- Tool execution audit logging to `tool_execution_logs`
- HCP search UI with history sidebar
- LangSmith / OpenTelemetry observability
- Rate limiting and LLM cost controls

## Documentation

- [Architecture Details](docs/ARCHITECTURE.md)
- [Demo Walkthrough Script](docs/DEMO_SCRIPT.md)


