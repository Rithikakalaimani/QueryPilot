# QueryPilot

Text-to-SQL RAG chatbot: ask questions in natural language and get SQL + results from your database. Schema is synced into a vector store (FAISS); the LLM (Groq) generates validated SQL using retrieved schema context.

**Live demo:** [https://querypilot.netlify.app/](https://querypilot.netlify.app/)

- **Backend:** Railway (FastAPI, Dockerfile, `requirements-railway.txt`)
- **Frontend:** Netlify (React + Vite)
- **Database:** Railway MySQL (referenced in backend); you can also use the connection form for your own MySQL/Postgres

---

## Features

- **Natural language → SQL** — Ask e.g. “How many customers?” or “Unique product categories without duplicates”; get generated SQL and results.
- **Schema sync** — Connect to MySQL/Postgres, click **Sync schema**; embeddings (HuggingFace) and FAISS power retrieval. On the demo, the backend uses Railway MySQL by default.
- **SQL preview & validation** — Generated SQL is shown; syntax, read-only, and row limits are enforced.
- **Result table + summary** — Results in a table with a short LLM summary (one sentence).
- **Database connection** — Use the form to point at your own DB (host, port, user, password, database). When the backend is on Railway, use a host reachable from the internet (e.g. Railway MySQL, cloud DB).
- **RAGAS evaluation** — Available when running the full backend locally (`requirements.txt`); on Railway the minimal build returns 503 for `/evaluate`.

### Screenshots

| Feature | Screenshot |
|--------|------------|
| QueryPilot interface — Header, chat, database connection. | ![QueryPilot interface](screenshots/Screenshot%202026-02-02%20at%209.48.38%20AM.png) |
| Database connection — Host, port, user, password, database (MySQL/Postgres). | ![Database connection](screenshots/Screenshot%202026-02-02%20at%209.48.50%20AM.png) |
| Chat and SQL preview — Natural language question and generated SQL. | ![Chat and SQL preview](screenshots/Screenshot%202026-02-02%20at%2010.01.17%20AM.png) |
| Result table — Query results with row count. | ![Result table](screenshots/Screenshot%202026-02-02%20at%2010.02.27%20AM.png) |
| RAGAS metrics — Evaluation dashboard (when running full backend locally). | ![RAGAS metrics](screenshots/Screenshot%202026-02-02%20at%2010.03.00%20AM.png) |

---

## Tech stack (current)

- **Backend:** Python, FastAPI, MySQL/Postgres (SQLAlchemy, PyMySQL, `cryptography`), HuggingFace embeddings (sentence-transformers), Groq LLM, FAISS (in-memory). Deployed on Railway via Dockerfile; uses `requirements-railway.txt` (HuggingFace + Groq; no RAGAS in image).
- **Frontend:** React (Vite), TypeScript — chat, SQL preview, result table, connection form, metrics dashboard. Deployed on Netlify; `VITE_API_URL` points to Railway backend.
- **DB:** Railway MySQL; backend references `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`.

---

## Quick start (local)

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy `env.example` to `.env`. Set `MYSQL_*` and either HuggingFace + Groq (`EMBEDDING_PROVIDER=huggingface`, `LLM_PROVIDER=groq`, `GROQ_API_KEY=...`) or OpenAI.

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Click **Sync schema**, then ask questions.

---

## Deployment (what’s live)

- **Railway (backend):** Root directory `backend`, builder Dockerfile. Uses `requirements-railway.txt`; CPU-only PyTorch in Dockerfile for sentence-transformers. Env: `MYSQL_*` (reference Railway MySQL), `EMBEDDING_PROVIDER=huggingface`, `EMBEDDING_MODEL=all-MiniLM-L6-v2`, `LLM_PROVIDER=groq`, `GROQ_API_KEY`, optional `REDIS_*`. Port/target port 8080 (or leave blank). Start command in `railway.toml` runs via shell so `$PORT` is set.
- **Netlify (frontend):** Base directory `frontend`, build `npm run build`, publish `frontend/dist`. Env: `VITE_API_URL=https://querypilot.up.railway.app` (or your Railway backend URL).
- **Railway MySQL:** Same project; backend references its `MYSQLHOST`, `MYSQLPORT`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`. Sync schema uses that by default when the connection form is not filled.

See [DEPLOYMENT.md](DEPLOYMENT.md) and [DEPLOY_STEP_BY_STEP.md](DEPLOY_STEP_BY_STEP.md) for step-by-step.

---

## Safety

- Read-only by default (`READ_ONLY=true`); row limit enforced (`MAX_ROWS_LIMIT`); SQL validated (syntax, read-only, table existence) before execution.
