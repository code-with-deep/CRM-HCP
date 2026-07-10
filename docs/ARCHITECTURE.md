# Architecture Documentation

## Overall System Architecture

```mermaid
flowchart LR
    User[Medical Representative] --> Chat[AI Chat Panel]
    Chat -->|SSE /chat/stream| FastAPI
    FastAPI --> ChatService
    ChatService --> AgentService
    AgentService --> LangGraph
    LangGraph --> Groq[Groq gemma2-9b-it]
    LangGraph --> Tools[5 CRM Tools]
    Tools --> PostgreSQL[(PostgreSQL)]
    LangGraph -->|interaction_draft| ChatService
    ChatService -->|ApiResponse| Redux
    Redux --> Form[Read-Only Form]
    User -->|Save Interaction| FastAPI
    FastAPI --> InteractionService --> PostgreSQL
```

## Frontend Architecture

```mermaid
flowchart TB
    subgraph Pages
        LIP[LogInteractionPage]
    end

    subgraph Hooks
        UCA[useChatActions]
    end

    subgraph Redux
        CS[chatSlice]
        IS[interactionSlice]
        US[uiSlice]
        HS[hcpSlice]
    end

    subgraph Services
        ChatSvc[chatService]
        IntSvc[interactionService]
        HcpSvc[hcpService]
    end

    LIP --> UCA
    UCA -->|thunks| CS
    UCA -->|thunks| IS
    UCA -->|thunks| HS
  UCA -->|thunks| US
    CS --> ChatSvc
    IS --> IntSvc
    HS --> HcpSvc
```

### Redux Flow

```mermaid
sequenceDiagram
    participant User
    participant ChatPanel
    participant Thunk as sendChatMessage
    participant API as POST /chat/stream
    participant Redux as interactionSlice
    participant Form as InteractionCard

    User->>ChatPanel: Send message
    ChatPanel->>Thunk: dispatch
    Thunk->>API: SSE stream
    API-->>Thunk: tokens + complete event
    Thunk->>Redux: mergeInteractionDraft (partial)
    Thunk->>Redux: setHighlightedFields
    Redux->>Form: Re-render changed fields
```

## Backend Architecture

```mermaid
flowchart TB
    subgraph API Layer
        ChatAPI[chat.py]
        IntAPI[interaction.py]
        HcpAPI[hcp.py]
    end

    subgraph Services
        ChatSvc[ChatService]
        AgentSvc[AgentService]
        IntSvc[InteractionService]
        HcpSvc[HcpService]
    end

    subgraph Repositories
        ConvRepo[ConversationRepository]
        IntRepo[InteractionRepository]
        HcpRepo[HcpRepository]
    end

    ChatAPI --> ChatSvc --> AgentSvc
    ChatAPI --> ChatSvc --> ConvRepo
    IntAPI --> IntSvc --> IntRepo
    HcpAPI --> HcpSvc --> HcpRepo
```

### Dependency Injection

- `core/dependencies.py` — settings, DB session, services, auth placeholder
- `RequestContextMiddleware` — correlation ID, request timing
- Global exception handlers — consistent `ApiResponse` envelope

## LangGraph Flow

```mermaid
flowchart TD
    START([START]) --> P[planner]
    P --> IR[intent_reasoner]
    IR --> TR[tool_router]
    TR -->|tool selected| TE[tool_executor]
    TR -->|no tool| RG[response_generator]
    TE --> V[validator]
    V -->|invalid + retry| IR
    V -->|valid| SU[state_updater]
    SU --> RG
    RG --> END([END])
```

### State Schema

| Field | Purpose |
|-------|---------|
| `messages` | LangChain message history |
| `current_interaction` | Interaction draft dict |
| `current_hcp` | Selected HCP context |
| `selected_tool` | Last executed tool |
| `interaction_status` | draft / completed |
| `validation_errors` | Business validation notes |
| `memory` | Turn count, last tool, summaries |

### Routing Rules

- **No keyword matching** — `routing.py` uses LLM structured outputs only
- `route_after_router` — checks `should_execute_tool` and `ToolName`
- `route_after_validation` — retry loop with `LLM_MAX_VALIDATION_RETRIES`

## Database ER Diagram

```mermaid
erDiagram
    USERS ||--o{ CONVERSATION_SESSIONS : has
    USERS ||--o{ INTERACTIONS : logs
    HCPS ||--o{ INTERACTIONS : receives
    INTERACTION_TYPES ||--o{ INTERACTIONS : classifies
    CONVERSATION_SESSIONS ||--o| INTERACTIONS : links
    INTERACTIONS ||--o{ INTERACTION_ATTENDEES : has
    INTERACTIONS ||--o{ INTERACTION_TOPICS : discusses
    INTERACTIONS ||--o{ INTERACTION_MATERIALS : shares
    INTERACTIONS ||--o{ INTERACTION_SAMPLES : distributes
    INTERACTIONS ||--o{ INTERACTION_PRODUCTS : promotes
    TOPICS ||--o{ INTERACTION_TOPICS : referenced
    MATERIALS ||--o{ INTERACTION_MATERIALS : referenced
    SAMPLES ||--o{ INTERACTION_SAMPLES : referenced
    PRODUCTS ||--o{ INTERACTION_PRODUCTS : referenced
```

## AI Workflow

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as FastAPI
    participant G as LangGraph
    participant T as Tool
    participant DB as PostgreSQL

    U->>F: "I met Dr Sharma today"
    F->>B: POST /chat/stream
    B->>G: ainvoke(initial_state)
    G->>G: planner → reasoner → router
    G->>T: LogInteractionTool
    T-->>G: interaction patch
    G->>G: validator → state_updater → response
    G-->>B: final_state
    B->>DB: persist messages
    B-->>F: SSE tokens + complete
    F->>F: Redux merge draft
    Note over F: Form updates live
    U->>F: Save Interaction
    F->>B: POST /interaction/save
    B->>DB: persist interaction + associations
```

## Prompt Engineering Layer

Located in `backend/app/prompts/` (separate from LangGraph nodes):

| Module | Used By |
|--------|---------|
| `system_prompt.py` | All LLM calls |
| `planner_prompt.py` | Planner node |
| `intent_prompt.py` | Intent reasoner |
| `router_prompt.py` | Tool router |
| `log_interaction_prompt.py` | LogInteractionTool |
| `edit_interaction_prompt.py` | EditInteractionTool |
| `search_hcp_prompt.py` | SearchHCPTool |
| `materials_prompt.py` | MaterialsAndSamplesTool |
| `followup_prompt.py` | OutcomeAndFollowupTool |
| `validation_prompt.py` | Validator node |
| `response_prompt.py` | Response generator |

All tools use **Pydantic structured outputs** via Groq.

## Performance Considerations

| Area | Strategy |
|------|----------|
| Frontend | `React.memo` on MessageBubble, InteractionCard; lazy routes |
| Redux | Partial draft merge; field-level highlights |
| API | Axios retry for transient failures |
| Database | Indexes on HCP, interaction date, conversation |
| LangGraph | Lazy graph compilation; 8-message memory window |

## Security Architecture

| Control | Implementation |
|---------|----------------|
| Auth placeholder | `get_current_user()` + `X-User-Id` |
| Input validation | Pydantic v2 on all endpoints |
| SQL injection | SQLAlchemy parameterized queries |
| CORS | Configurable origins |
| Error exposure | Sanitized ApiErrorResponse |
| Secrets | Environment variables only |
