# Database Agent

A natural-language database analyst: connect a Postgres/MySQL database, CSV, Excel file, or Google Sheet, describe your tables in plain English, and ask questions that get compiled into safe, executed SQL with charted results.

## Features

- **Multi-source connectors** — Postgres, MySQL, CSV, Excel, and Google Sheets behind a single `BaseConnector` interface (`src/database_agent/connectors/`).
- **Schema introspection & semantic layer** — extracts tables/columns/relationships, lets an LLM propose business-friendly names, and assembles a per-session YAML semantic layer (`services/semantic_layer_assembly.py`, `backend/configs/*.yaml`).
- **Relationship editor** — view, add, edit, and delete inferred table relationships before querying (`api/routes/relationships.py`).
- **LangGraph query agent** — a stateful graph (`query_writer → compiler → executor → interpreter → chart_decider`) turns a question into business-name SQL, compiles it to physical SQL, executes it, interprets the results, and decides on a chart, with automatic retry/give-up routing on failure (`src/database_agent/graph/`).
- **Semantic search over columns** — column/table names are embedded (Ollama) and indexed in Qdrant so the agent can retrieve relevant schema context per question (`services/embedding_service.py`, `sessions/qdrant_client.py`).
- **Durable agent state** — LangGraph checkpoints persist to Postgres (`AsyncPostgresSaver`), so multi-turn conversations survive restarts.
- **Chat & session management** — multiple named chats per session, full chat history, and session listing/cleanup backed by Redis (`api/routes/chats.py`, `api/routes/session.py`, `services/session_cleanup.py`).
- **ERD generation** — renders an entity-relationship diagram of the connected schema (`api/routes/erd.py`, `frontend/src/components/ErdDiagram.jsx`).
- **Google OAuth for private Sheets** — OAuth login flow to read Google Sheets the user doesn't own publicly (`api/routes/google_auth.py`).
- **Input guardrails & name sanitization** — validates/guards user input before it reaches the agent and sanitizes identifiers used in generated SQL (`services/input_guardrail.py`, `services/name_sanitizer.py`).
- **React wizard UI** — step-driven frontend (Connect → Select Tables → Review → Ask) with chart rendering, KPI cards, and a result table (`frontend/src/pages/`, `frontend/src/components/`).

## Tech Stack

**Backend**
- Python 3.11, [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/)
- [LangGraph](https://github.com/langchain-ai/langgraph) + [LangGraph Postgres checkpointer](https://pypi.org/project/langgraph-checkpoint-postgres/) for the agent state machine
- [LangChain Ollama](https://python.langchain.com/) for local LLM calls and embeddings
- [Qdrant](https://qdrant.tech/) (via `langchain-qdrant` / `qdrant-client`) for semantic column search
- [Redis](https://redis.io/) for session metadata
- [DuckDB](https://duckdb.org/) for querying CSV/Excel/Google Sheets sources
- `asyncpg`, `psycopg[binary]` + `psycopg-pool` for Postgres access; `aiomysql` for MySQL
- [SQLGlot](https://github.com/tobymao/sqlglot) to compile business-name SQL to physical SQL
- [Guardrails AI](https://www.guardrailsai.com/) for input validation
- `google-api-python-client` + `google-auth-oauthlib` for Google Sheets/OAuth
- [LangSmith](https://www.langchain.com/langsmith) for tracing/observability
- [uv](https://docs.astral.sh/uv/) for dependency management and packaging

**Frontend**
- [React 19](https://react.dev/) + [Vite](https://vitejs.dev/)
- [Zustand](https://github.com/pmndrs/zustand) for state management
- [Recharts](https://recharts.org/) for charts, [react-erd](https://www.npmjs.com/package/react-erd) for ERD rendering, [react-markdown](https://github.com/remarkjs/react-markdown) for answer rendering
- ESLint for linting

**Infrastructure**
- Docker / Docker Compose (backend, frontend, Redis, Qdrant, checkpoint Postgres)
- Nginx (serves the built frontend in production)

## Prerequisites

- [Python 3.11](https://www.python.org/) (pinned in `.python-version`)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package/dependency manager)
- [Node.js 20+](https://nodejs.org/) and npm (for the frontend)
- [Docker](https://www.docker.com/) and Docker Compose (for Redis, Qdrant, and the Postgres checkpoint store)
- An [Ollama](https://ollama.ai/) instance reachable at `OLLAMA_BASE_URL`, with the configured chat and embedding models pulled

## Installation

### Clone

```bash
git clone <repository-url>
cd database-agent
```

### Backend (local, without Docker)

```bash
# install dependencies into a local .venv
uv sync

# start the supporting services (Redis, Qdrant, checkpoint Postgres)
docker compose up -d redis qdrant checkpoint-postgres

# pull the Ollama models referenced in your .env
ollama pull gpt-oss:latest
ollama pull nomic-embed-text:latest

# run the API
uv run uvicorn database_agent.main:app --reload --port 8000
```

### Frontend (local)

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on `http://localhost:5173` and expects the backend on `http://localhost:8000` (CORS is pre-configured for this origin in `src/database_agent/main.py`).

### Full stack with Docker Compose

```bash
docker compose up --build
```

This builds and starts the backend, frontend (Nginx), Redis, Qdrant, and the checkpoint Postgres database together.

| Service | Port |
|---|---|
| Backend (FastAPI) | `8000` |
| Frontend (Nginx) | `5173` |
| Redis | `6379` |
| Qdrant | `6333` |
| Checkpoint Postgres | `5434` |

## Configuration

The backend reads configuration from environment variables (loaded from a `.env` file at the project root via `pydantic-settings`). See `src/database_agent/core/config.py` for defaults.

Create a `.env` file in the project root:

```dotenv
# --- App ---
ENVIRONMENT=development
DEBUG=true

# --- Redis (session metadata store) ---
REDIS_URL=redis://localhost:6379/0
REDIS_SESSION_TTL_SECONDS=1800

# --- DuckDB (file-based sources: CSV, Excel, Google Sheets) ---
DUCKDB_MEMORY_LIMIT=1GB

# --- Connection limits ---
MAX_ACTIVE_SESSIONS=50
CONNECTION_TIMEOUT_SECONDS=10

# --- Ollama (LLM + embeddings) ---
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gpt-oss:latest
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest

# --- Qdrant (semantic column index) ---
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=semantic_layer_columns

# --- Google OAuth (private Google Sheets access) ---
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/auth/google/callback

# --- LangSmith (tracing/observability) ---
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=database-agent

# --- LangGraph checkpoint store ---
CHECKPOINT_DB_URI=postgresql://agent:agent@localhost:5434/checkpoints
```

When running via `docker compose`, `REDIS_URL`, `QDRANT_URL`, and `CHECKPOINT_DB_URI` are overridden to point at the Compose service names — the values above are for running the backend directly on the host.

## Usage

1. Start the backend, frontend, and supporting services (see [Installation](#installation)).
2. Open `http://localhost:5173` in a browser.
3. **Connect** a data source: Postgres, MySQL, CSV, Excel, or Google Sheets.
4. **Select tables** to include in the session's semantic layer.
5. **Review** the generated semantic layer (business names, descriptions, relationships) and edit relationships if needed.
6. **Ask** questions in natural language; the agent compiles and runs SQL, then returns an answer, a result table, and (when applicable) a chart.

You can also call the API directly, for example:

```bash
# connect to a Postgres database
curl -X POST http://localhost:8000/connect/postgres \
  -H "Content-Type: application/json" \
  -d '{"host": "localhost", "port": 5432, "database": "mydb", "user": "user", "password": "pass"}'

# ask a question against an existing session
curl -X POST http://localhost:8000/session/<session_id>/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What were total sales last month?"}'

# health check
curl http://localhost:8000/health
```

## Testing

This repository does not currently ship an automated test suite (no `pytest` configuration or test modules are present).

`docker-compose.test.yml` and `test-data/` provide seeded Postgres and MySQL instances for manual/integration verification of the connectors:

```bash
# start isolated test databases, pre-seeded from test-data/*.sql
docker compose -f docker-compose.test.yml up -d

# point the app at test-postgres (localhost:5433) or test-mysql (localhost:3307)
# to exercise the connect/schema/ask flow against known data
```

`test-data/test.csv` and `test-data/test.xlsx` can be used the same way to exercise the CSV/Excel connectors, and `test-data/semantics.skeleton.yaml` shows the expected shape of an assembled semantic layer.

## Project Structure

```
database-agent/
├── src/database_agent/
│   ├── main.py                  # FastAPI app, lifespan (DB pool, checkpointer, chat store)
│   ├── api/
│   │   ├── router.py             # aggregates all route modules
│   │   └── routes/                # connect/*, session, agent (ask), erd, relationships,
│   │                              # semantic_layer, chats, google_auth
│   ├── connectors/                # BaseConnector + postgres/mysql/duckdb_file implementations
│   ├── core/config.py             # pydantic-settings app configuration
│   ├── graph/
│   │   ├── builder.py             # LangGraph StateGraph definition (see diagram below)
│   │   ├── state.py                # AgentState schema
│   │   ├── prompts.py              # LLM prompts for each node
│   │   └── nodes/                  # query_writer, compiler, executor, interpreter,
│   │                                # chart_decider, give_up
│   ├── models/                    # Pydantic request/response/domain models
│   ├── services/                  # semantic layer assembly/indexing, embeddings,
│   │                              # SQL compiler, guardrails, name sanitizer, session cleanup
│   └── sessions/                  # Redis-backed chat store, connection registry,
│                                   # metadata store, Qdrant client, semantic layer cache
├── backend/configs/               # per-session assembled semantic layer YAML files
├── frontend/
│   ├── src/
│   │   ├── pages/                 # ConnectPage, TableSelectionPage, ReviewPage, AskPage,
│   │   │                          # ConnectionsPage
│   │   ├── components/            # ErdDiagram, ChartRenderer, ChartCandidateList,
│   │   │                          # ResultTable, KpiCard, RelationshipsPanel, StepIndicator
│   │   ├── api/                    # fetch wrappers per backend resource
│   │   └── store/sessionStore.js  # Zustand session/UI state
│   ├── Dockerfile                 # multi-stage build, served via Nginx
│   └── nginx.conf
├── scripts/
│   └── generate_agent_graph.py    # renders the LangGraph agent workflow to docs/assets/
├── docs/assets/                   # generated diagrams (agent_graph.mmd / .png)
├── test-data/                     # seed SQL, sample CSV/Excel, semantic layer skeleton
├── docker-compose.yml             # full stack: backend, frontend, redis, qdrant, checkpoint db
├── docker-compose.test.yml        # isolated seeded Postgres/MySQL for testing connectors
├── Dockerfile                     # backend image (uv-built, non-root runtime)
├── pyproject.toml / uv.lock       # backend dependencies
└── .python-version                 # pinned Python 3.11
```

## Agent Workflow Graph

The core reasoning loop is a [LangGraph](https://github.com/langchain-ai/langgraph) state machine defined in [`src/database_agent/graph/builder.py`](src/database_agent/graph/builder.py). A question is written as business-name SQL, compiled to physical SQL, executed, interpreted into a natural-language answer, and finally routed to a chart decision — with conditional retry loops back to `query_writer` on compile/execute failure, and a bounded `give_up` path once retries are exhausted.

Regenerate the diagram after changing the graph:

```bash
uv run python scripts/generate_agent_graph.py
```

This writes `docs/assets/agent_graph.mmd` (Mermaid source, embedded below) and `docs/assets/agent_graph.png` (best-effort, requires network access to render).

```mermaid
graph TD;
	__start__([<p>__start__</p>]):::first
	query_writer(query_writer)
	compiler(compiler)
	executor(executor)
	interpreter(interpreter)
	chart_decider(chart_decider)
	give_up(give_up)
	__end__([<p>__end__</p>]):::last
	__start__ --> query_writer;
	compiler -.-> executor;
	compiler -.-> give_up;
	compiler -.-> query_writer;
	executor -.-> give_up;
	executor -.-> interpreter;
	executor -.-> query_writer;
	interpreter --> chart_decider;
	query_writer --> compiler;
	chart_decider --> __end__;
	give_up --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```
