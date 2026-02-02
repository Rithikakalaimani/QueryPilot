# QueryPilot

**Text-to-SQL RAG Chatbot** — Ask questions in natural language and get SQL + results from your MySQL or Postgres database. Schema is ingested into a vector store, and the LLM generates validated SQL using retrieved context.

**Live demo:** [https://querypilot.netlify.app/](https://querypilot.netlify.app/)

---

## Features

- **Natural language to SQL** — Type questions like “How many customers are there?” or “List unique product categories” and get executable SQL plus results.
- **Schema sync** — Connect to your MySQL/Postgres, sync schema once; embeddings (HuggingFace or OpenAI) and FAISS power retrieval for each query.
- **SQL preview & validation** — Generated SQL is shown before/after run; syntax, read-only, and row limits are enforced.
- **Result table + summary** — Results appear in a table with an optional short LLM summary.
- **Per-user database** — Use the Database connection form to point at your own DB (or rely on the server default); schema is isolated per connection.
- **RAGAS evaluation** — Run a benchmark to measure faithfulness, answer relevancy, context precision/recall, and execution accuracy (when using full `requirements.txt`).

### Screenshots

| Feature | Screenshot |
|--------|------------|
| **QueryPilot interface** — Header, chat, and database connection panel. | ![QueryPilot interface](screenshots/Screenshot%202026-02-02%20at%209.48.38%20AM.png) |
| **Database connection** — Configure host, port, user, password, and database (MySQL/Postgres). | ![Database connection](screenshots/Screenshot%202026-02-02%20at%209.48.50%20AM.png) |
| **Chat and SQL preview** — Ask in natural language; see generated SQL and validation. | ![Chat and SQL preview](screenshots/Screenshot%202026-02-02%20at%2010.01.17%20AM.png) |
| **Result table** — Query results in a tabular view with row count. | ![Result table](screenshots/Screenshot%202026-02-02%20at%2010.02.27%20AM.png) |
| **RAGAS metrics** — Evaluation dashboard (faithfulness, relevancy, context precision/recall, execution accuracy). | ![RAGAS metrics](screenshots/Screenshot%202026-02-02%20at%2010.03.00%20AM.png) |

---

## Architecture

| Phase | Goal | Components |
|-------|------|------------|
| **1. Schema ingestion** | Make the LLM schema-aware | Connect to MySQL/Postgres → extract tables, columns, FKs → chunk → embed (OpenAI/HuggingFace) → store in FAISS (in-memory) |
| **2. Query understanding** | NL → intent | Parse intent (SELECT/aggregation/filter/join), entities → retrieve relevant schema chunks via similarity search |
| **3. SQL generation** | Correct, executable SQL | LLM + schema context + SQL rules → generate SQL → validate (syntax, read-only, row limit, table existence) |
| **4. Execution & presentation** | Close the loop | Execute validated SQL → format results (table + optional LLM summary) |
| **RAGAS evaluation** | Prove correctness | Faithfulness, answer relevancy, context precision/recall, execution accuracy over a benchmark set |

---

## Tech stack

- **Backend:** Python, FastAPI, MySQL/Postgres (SQLAlchemy), **HuggingFace + Groq** (default) or OpenAI/Ollama, FAISS (in-memory)
- **Frontend:** React (Vite), TypeScript — chat UI, SQL preview, result table, connection form, metrics dashboard
- **Evaluation:** RAGAS-style metrics (when using full `requirements.txt`)

---

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy `env.example` to `.env` and set `MYSQL_*` for your DB.

**Default (HuggingFace + Groq):**

- **Embeddings:** `EMBEDDING_PROVIDER=huggingface`, `EMBEDDING_MODEL=all-MiniLM-L6-v2` (local).
- **LLM:** `LLM_PROVIDER=groq`, `LLM_MODEL=llama-3.1-8b-instant`, `GROQ_API_KEY=your_key` from [console.groq.com](https://console.groq.com).

**Start the API:**

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Click **Sync schema** once (ingests DB schema into FAISS), then ask questions in natural language.

### 3. API endpoints

- `GET /health` — health check
- `POST /api/sync-schema` — ingest schema from DB into FAISS
- `POST /api/chat` — Body: `{ "message": "How many users?", "include_summary": true }` → returns SQL, columns, rows, summary
- `POST /api/evaluate` — run RAGAS benchmark (requires full `requirements.txt`)

---

## Project layout

```
TtSQL/
├── backend/
│   ├── config.py              # Settings (DB, LLM, embeddings)
│   ├── main.py                # FastAPI app (sync, chat, evaluate)
│   ├── schema_ingestion/      # Phase 1: extract, chunk, embed, FAISS
│   ├── query_understanding/   # Phase 2: intent, retriever
│   ├── sql_generation/        # Phase 3: generator, validator, pipeline
│   ├── execution/             # Phase 4: runner, formatter
│   └── evaluation/            # RAGAS benchmark & metrics
├── frontend/                  # React chat UI, SQL preview, result table
├── screenshots/               # App screenshots for README
└── README.md
```

---

## Production & deployment

- **Per-user database:** Use the **Database connection** form to point at your own MySQL/Postgres; sync and chat use that connection. When the backend is deployed (e.g. Railway), use a DB host reachable from the internet (e.g. Railway MySQL, PlanetScale); see [DEPLOYMENT.md](DEPLOYMENT.md).
- **Redis (optional):** Set `REDIS_*` in `.env` for sync job status, schema cache, and chat cache across workers.
- **Deploy:** Backend on Railway (Dockerfile + `requirements-railway.txt`), frontend on Netlify/Vercel with `VITE_API_URL` set to the backend URL. See [DEPLOYMENT.md](DEPLOYMENT.md) and [DEPLOY_STEP_BY_STEP.md](DEPLOY_STEP_BY_STEP.md).

---

## Safety

- **Read-only:** By default only SELECT is allowed (`READ_ONLY=true`).
- **Row limit:** `MAX_ROWS_LIMIT` (default 1000) is enforced; LIMIT is added if missing.
- **Validation:** Syntax, table existence, and read-only checks before execution.

---

## License

Use and modify as needed for your project.
