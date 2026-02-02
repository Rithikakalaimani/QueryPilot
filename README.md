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
- **RAGAS evaluation** — Available when running the full backend locally (`requirements.txt`); on Railway the minimal build.

### Screenshots

 ![QueryPilot interface](https://github.com/Rithikakalaimani/QueryPilot/blob/main/screenshots/Screenshot%202026-02-02%20at%2010.01.17%E2%80%AFAM.png) 
![Database connection](https://github.com/Rithikakalaimani/QueryPilot/blob/main/screenshots/Screenshot%202026-02-02%20at%2010.02.27%E2%80%AFAM.png) 
![Chat and SQL preview](https://github.com/Rithikakalaimani/QueryPilot/blob/main/screenshots/Screenshot%202026-02-02%20at%2010.03.00%E2%80%AFAM.png) 
![Result table](https://github.com/Rithikakalaimani/QueryPilot/blob/main/screenshots/Screenshot%202026-02-02%20at%209.48.38%E2%80%AFAM.png) 
![RAGAS metrics](https://github.com/Rithikakalaimani/QueryPilot/blob/main/screenshots/Screenshot%202026-02-02%20at%209.48.50%E2%80%AFAM.png) 

---

## Tech stack (current)

- **Backend:** Python, FastAPI, MySQL(SQLAlchemy, PyMySQL), HuggingFace embeddings, Groq LLM, FAISS (in-memory). Deployed on Railway via Dockerfile.
- **Frontend:** React
- **DB:** Railway MySQL

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

