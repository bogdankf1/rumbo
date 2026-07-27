# Rumbo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Source of truth for behavior: `SPEC.md` at repo root.

**Goal:** Build the Rumbo career intelligence assistant end to end: ingestion, deterministic matching, cited chat with refusals, evals, Docker Compose, editorial dark UI.

**Architecture:** FastAPI backend (async SQLAlchemy + pgvector) does PDF parsing, Claude structured extraction, deterministic skill matching, and an SSE chat pipeline with evidence-pack grounding. Next.js App Router frontend proxies `/api/*` to the backend and renders a sidebar document library plus a streaming chat. Embeddings via an adapter over OpenAI.

**Tech Stack:** Python 3.12, uv, FastAPI, SQLAlchemy 2 async, asyncpg, pgvector, anthropic>=0.116.0 (`claude-opus-5`), openai (text-embedding-3-small), pdfplumber, structlog, pytest; Next.js 15, React 19, TypeScript, Tailwind v4; Docker Compose.

**Conventions for every task:** no em dashes or en dashes anywhere (code, copy, docs, commits); match SPEC section numbers when in doubt; commit at the end of every task with a conventional message ending in the Claude co-author line; keep files small and single-purpose.

---

## Slice 0: Scaffold

### Task 1: Backend skeleton with health endpoint

**Files:**
- Create: `backend/pyproject.toml`, `backend/app/__init__.py`, `backend/app/config.py`, `backend/app/db.py`, `backend/app/models.py`, `backend/app/main.py`, `backend/app/routers/__init__.py`, `backend/app/routers/health.py`, `backend/app/logging.py`
- Test: `backend/tests/test_health.py`

- [ ] **Step 1: pyproject**

```toml
[project]
name = "rumbo-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.30",
  "sqlalchemy[asyncio]>=2.0",
  "asyncpg>=0.29",
  "pgvector>=0.3",
  "pydantic>=2.8",
  "pydantic-settings>=2.4",
  "anthropic>=0.116.0",
  "openai>=1.50",
  "pdfplumber>=0.11",
  "structlog>=24.4",
  "python-multipart>=0.0.9",
  "pyyaml>=6.0",
  "httpx>=0.27",
]

[dependency-groups]
dev = ["pytest>=8.3", "pytest-asyncio>=0.24", "reportlab>=4.2"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 2: config.py** using pydantic-settings: `anthropic_api_key`, `openai_api_key`, `database_url` (default `postgresql+asyncpg://rumbo:rumbo@localhost:5432/rumbo`), `claude_model = "claude-opus-5"`, `embedding_model = "text-embedding-3-small"`, `embedding_dims = 1536`. Reads repo-root `.env` via `model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")`.

- [ ] **Step 3: models.py** exactly per SPEC section 4 (`Resume`, `JobDescription`, `Chunk` with `Vector(1536)` from `pgvector.sqlalchemy`, `ChatMessage`), uuid PKs via `uuid.uuid4` defaults, `JobDescription.seq` as `Integer` populated from a `SELECT coalesce(max(seq),0)+1` at insert.

- [ ] **Step 4: db.py**: async engine + sessionmaker, `get_session` dependency, `init_db()` that runs `CREATE EXTENSION IF NOT EXISTS vector` then `Base.metadata.create_all` via `conn.run_sync`. Called from FastAPI lifespan.

- [ ] **Step 5: logging.py**: structlog JSON config (timestamper, level, event renderer to stdout). `main.py` calls it, mounts routers, adds a middleware that logs method, path, status, duration_ms.

- [ ] **Step 6: health router**: `GET /health` returns `{"status": "ok", "db": true|false}`; db checked with `SELECT 1` in a try/except, status stays "ok" only if db is true else 503.

- [ ] **Step 7: test_health.py**: httpx `ASGITransport` test asserting 200 and body shape (requires the compose db running; see Task 3).

- [ ] **Step 8: `uv sync` inside `backend/`, verify import: `uv run python -c "import app.main"`.** Commit: `feat: backend skeleton with health endpoint`.

### Task 2: Frontend skeleton

**Files:**
- Create: `frontend/package.json`, `frontend/tsconfig.json`, `frontend/next.config.ts`, `frontend/postcss.config.mjs`, `frontend/app/layout.tsx`, `frontend/app/page.tsx`, `frontend/app/globals.css`, `frontend/lib/types.ts`, `frontend/lib/api.ts`

- [ ] **Step 1:** Hand-author `package.json` (next@^15, react@^19, react-dom@^19, typescript, @types/react, @types/node, tailwindcss@^4, @tailwindcss/postcss). `npm install`.
- [ ] **Step 2:** `next.config.ts` rewrites `/api/:path*` to `${process.env.BACKEND_URL ?? "http://localhost:8000"}/api/:path*`.
- [ ] **Step 3:** `globals.css` with Tailwind v4 `@import "tailwindcss";` plus an `@theme` block defining the SPEC section 12 palette as CSS variables (`--color-bg: #141110; --color-surface: #1C1917; --color-ink: #EDE8E3; --color-muted: #A8A29E; --color-accent: #C2704E; --color-amber: #D99A4E;`).
- [ ] **Step 4:** `layout.tsx` loads Fraunces, Instrument Sans, JetBrains Mono via `next/font/google`, sets `<html class="dark">`, body bg/ink. `page.tsx` renders a placeholder shell (top bar with Rumbo wordmark in Fraunces italic, sidebar column, main column).
- [ ] **Step 5:** `npm run build` passes. Commit: `feat: frontend skeleton with editorial dark theme tokens`.

### Task 3: Compose, Makefile, dockerfiles

**Files:**
- Create: `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `Makefile`

- [ ] **Step 1: docker-compose.yml**: `db` (image `pgvector/pgvector:pg16`, POSTGRES_USER/PASSWORD/DB all `rumbo`, port 5432, healthcheck `pg_isready -U rumbo`), `backend` (build `./backend`, env_file `.env`, `DATABASE_URL=postgresql+asyncpg://rumbo:rumbo@db:5432/rumbo`, port 8000, depends_on db healthy, healthcheck curl `/health`), `frontend` (build `./frontend`, `BACKEND_URL=http://backend:8000`, port 3000, depends_on backend).
- [ ] **Step 2: backend Dockerfile**: `python:3.12-slim`, install uv, `uv sync --frozen --no-dev`, `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`. frontend Dockerfile: `node:22-alpine`, `npm ci`, `npm run build`, `npm start`.
- [ ] **Step 3: Makefile** targets: `dev-db` (compose up -d db), `dev-backend` (uv run uvicorn --reload), `dev-frontend` (npm run dev), `test` (cd backend && uv run pytest), `eval` (compose up -d db backend handled by the eval target in Task 14), `up` (docker compose up --build).
- [ ] **Step 4: Verify** `docker compose up -d db`, then `make dev-backend` in background, `curl localhost:8000/health` returns `{"status":"ok","db":true}`. Run `pytest tests/test_health.py`. Commit: `feat: docker compose, dockerfiles, makefile`.

---

## Slice 1: Ingestion

### Task 4: Alias map and canonical skill normalization (TDD)

**Files:**
- Create: `backend/app/services/__init__.py`, `backend/app/services/aliases.py`
- Test: `backend/tests/test_aliases.py`

- [ ] **Step 1: failing tests** covering: `canonicalize("postgres") == "PostgreSQL"`, `canonicalize("React.js") == "React"`, `canonicalize("REACT") == "React"`, unknown skill passes through with original casing trimmed (`canonicalize(" Elixir ") == "Elixir"`), `same_skill("k8s", "Kubernetes") is True`, `same_skill("React", "Vue") is False`.
- [ ] **Step 2: implement** `ALIASES: dict[str, str]` (~40 entries, lowercase alias to canonical: postgres/postgresql, react.js/reactjs, js/javascript, ts/typescript, k8s/kubernetes, gcp/google cloud, aws/amazon web services -> "AWS", node/node.js -> "Node.js", golang -> "Go", py -> "Python", tf -> "Terraform", ci-cd variants -> "CI/CD", scikit-learn variants, next/nextjs -> "Next.js", vue.js -> "Vue", express.js -> "Express", mongo -> "MongoDB", etc.) plus `CANONICAL: dict[str, str]` lowercase-canonical to display form. `canonicalize(name)`: strip, lookup alias, else lookup canonical by lowercase, else return stripped input. `same_skill(a, b)`: `canonicalize(a).lower() == canonicalize(b).lower()`.
- [ ] **Step 3:** tests pass. Commit: `feat: canonical skill alias map`.

### Task 5: PDF text extraction

**Files:**
- Create: `backend/app/services/pdf.py`
- Test: `backend/tests/test_pdf.py`

- [ ] **Step 1: failing test**: build a 1-page PDF in-memory with reportlab containing two known lines, assert `extract_text(bytes)` returns both lines and normalizes internal whitespace runs to single spaces per line. Also: `extract_text(b"not a pdf")` raises `PdfParseError`.
- [ ] **Step 2: implement** with `pdfplumber.open(io.BytesIO(data))`, join page texts with newlines, collapse `[ \t]+` runs, strip trailing spaces; raise `PdfParseError` on any pdfplumber exception or empty text.
- [ ] **Step 3:** tests pass. Commit: `feat: pdf text extraction`.

### Task 6: Extraction schemas, prompts, evidence validation

**Files:**
- Create: `backend/app/services/extraction.py`
- Test: `backend/tests/test_extraction.py`

- [ ] **Step 1: Pydantic models** exactly per SPEC section 5: `SkillItem {name, category, evidence, years: float|None, verified: bool = True}`, `ResumeExtract`, `ReqSkill {name, evidence, verified: bool = True}`, `JDExtract`. Categories as `Literal`.
- [ ] **Step 2: prompts.** `RESUME_PROMPT` and `JD_PROMPT` as module constants. Both must instruct: canonical skill naming with examples ("PostgreSQL" not "Postgres", "React" not "React.js"), evidence must be a verbatim contiguous quote copied from the document, do not invent skills, seniority inference rules, JD prompt distinguishes required vs nice-to-have by phrasing ("must", "required" vs "nice to have", "bonus", "a plus").
- [ ] **Step 3: extraction calls.** `async def extract_resume(text) -> ResumeExtract` and `extract_jd(text) -> JDExtract` using `await client.messages.parse(model=settings.claude_model, max_tokens=16000, messages=[{"role": "user", "content": prompt + text}], output_format=Model)`; read `.parsed_output`. Client from `anthropic.AsyncAnthropic()` created once in the module. After parse: apply `canonicalize` to every skill name, then `validate_evidence(extract, raw_text)`: whitespace-normalize both sides (`" ".join(s.split()).lower()`), substring check; on failure set `verified=False` and log a structlog warning.
- [ ] **Step 4: tests** (no network): `validate_evidence` marks a fabricated quote unverified and keeps a real quote verified; canonicalization applied to parsed skills (feed a `ResumeExtract` built directly); prompt constants mention "verbatim" (guard against accidental edits).
- [ ] **Step 5:** tests pass. Commit: `feat: claude structured extraction with evidence validation`.

### Task 7: Chunking and embeddings adapter

**Files:**
- Create: `backend/app/services/chunking.py`, `backend/app/services/embeddings.py`
- Test: `backend/tests/test_chunking.py`

- [ ] **Step 1: chunking tests**: paragraph-grouped chunks; a doc with 6 short paragraphs and target 400 tokens yields fewer chunks than paragraphs (grouping happens); no chunk exceeds ~600 token estimate (len//4 heuristic); section labels: for resumes pass `sections` hints (role titles) that become `section` when a chunk starts with that text, default label `body`; chunk indexes are sequential.
- [ ] **Step 2: implement** `chunk_text(text, target_tokens=400) -> list[ChunkDraft {idx, section, content}]`: split on blank lines, greedily pack paragraphs until the estimate (`len(p)//4`) would exceed target, never split a paragraph.
- [ ] **Step 3: embeddings adapter**: `class EmbeddingProvider(Protocol): async def embed(self, texts: list[str]) -> list[list[float]]`. `OpenAIEmbeddings` implements it with `AsyncOpenAI().embeddings.create(model=settings.embedding_model, input=texts)`. Module-level `get_provider()` returns the OpenAI impl (the one-file swap point).
- [ ] **Step 4:** chunking tests pass. Commit: `feat: section chunking and embedding adapter`.

### Task 8: Resume and job CRUD with ingestion orchestration

**Files:**
- Create: `backend/app/schemas.py`, `backend/app/services/ingestion.py`, `backend/app/routers/resumes.py`, `backend/app/routers/jobs.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: schemas.py**: `ResumeOut {id, name, source_filename, extracted, is_active, created_at}`, `JobOut {id, seq, title, company, source, extracted, created_at, fit: MatchResult|None}` (fit filled from Task 10 onward, `None` until then), `JobCreateText {title: str|None, text: str}`, `ChatMessageOut`.
- [ ] **Step 2: ingestion.py**: `ingest_resume(session, filename, pdf_bytes)`: pdf -> text -> extract_resume -> chunk (sections from role titles) -> embed -> insert resume + chunks; first resume ever becomes active. `ingest_job(session, source, text_or_pdf, title_hint)`: same shape for JDs; title/company from extract. Both return ORM rows. Delete helpers also delete owned chunks.
- [ ] **Step 3: routers** per SPEC section 8 table: resumes (POST multipart, GET list, POST activate which deactivates others, DELETE), jobs (POST accepting either multipart PDF or JSON body, GET list, GET one, DELETE). 422 with `{detail}` on `PdfParseError`.
- [ ] **Step 4: verify manually** against the running dev stack with one of the sample PDFs once Task 12 lands (interim: any short PDF). `GET /api/resumes` shows extracted JSON. Commit: `feat: resume and job ingestion endpoints`.

### Task 9: Demo dataset and seed endpoint

**Files:**
- Create: `backend/data/demo/resumes/r1..r7.json`, `backend/data/demo/jobs/j1..j7.json`, `backend/app/routers/demo.py`, `backend/scripts/make_demo_pdfs.py`, `backend/data/demo/pdfs/*.pdf` (3 files)
- Modify: `backend/app/main.py`

- [ ] **Step 1: author 14 JSON docs**, each `{meta: {name|title, company?}, raw_text, extracted}`. Personas and deliberate overlaps (verdict spread is the point):
  - R1 Maya Chen, senior frontend: React, TypeScript, Next.js, GraphQL, Jest, Tailwind CSS; 7y. R2 Diego Alvarez, backend Python: FastAPI, PostgreSQL, Redis, Docker, AWS; 5y, no Kubernetes/Kafka. R3 Sofia Novak, data engineer: Python, Spark, Airflow, dbt, Snowflake, SQL; 6y. R4 Ethan Brooks, full-stack JS: Node.js, Express, React, MongoDB; 3y. R5 Priya Raman, platform: Kubernetes, Terraform, AWS, Go, CI/CD, Prometheus; 8y. R6 Lena Fischer, ML: PyTorch, Python, MLflow, AWS; 4y. R7 Tom Okafor, mobile: React Native, TypeScript, Swift; 5y.
  - J1 Senior Frontend (Vue) at Nimbus Retail: required Vue, TypeScript, Pinia; nice Vitest; 5y. J2 Backend Engineer at Finch Health: required Python, FastAPI, PostgreSQL, Kubernetes; nice Kafka; 4y. J3 Data Platform Engineer at Meridian Analytics: required Spark, Airflow, Kafka, AWS; nice Terraform; 5y. J4 Full-stack Engineer at Loop Studio: required React, Node.js, PostgreSQL; nice AWS; 4y. J5 Platform Engineer at Volta Cloud: required Kubernetes, Go, Terraform, AWS; nice Prometheus; 6y. J6 ML Platform Engineer at Arbor AI: required PyTorch, Kubernetes, MLflow; nice AWS; 5y. J7 Senior Product Engineer at Harbor Labs: required React, TypeScript, Next.js; nice GraphQL; 5y.
  - **Hard rule:** every `evidence` string is copied verbatim from that document's `raw_text` (write raw_text first, then copy lines). All data invented, no real people.
- [ ] **Step 2: demo.py**: `POST /api/demo` deletes chat_messages, chunks, job_descriptions, resumes (in that order), loads all JSON files, inserts docs with pre-baked `extracted`, chunks + embeds raw_text live, marks R1 active, returns counts.
- [ ] **Step 3: make_demo_pdfs.py**: renders r1, j1, j2 raw_text to simple PDFs with reportlab; run once, commit the PDFs.
- [ ] **Step 4: verify**: `curl -X POST localhost:8000/api/demo` returns `{"resumes": 7, "jobs": 7}`; spot-check a `chunks` count > 0. Add a pytest that loads every demo JSON and asserts all evidence strings pass `validate_evidence` (pure, no network). Commit: `feat: demo dataset and seed endpoint`.

### Task 10 (frontend): Sidebar, uploads, demo button

**Files:**
- Create: `frontend/components/TopBar.tsx`, `frontend/components/Sidebar.tsx`, `frontend/components/ResumeCard.tsx`, `frontend/components/JobCard.tsx`, `frontend/components/UploadZone.tsx`, `frontend/components/PasteJobModal.tsx`, `frontend/components/EmptyState.tsx`
- Modify: `frontend/app/page.tsx`, `frontend/lib/api.ts`, `frontend/lib/types.ts`

- [ ] **Step 1: types.ts** mirrors backend schemas (Resume, Job, MatchResult, ChatMessage). **api.ts**: `listResumes`, `uploadResume(file)`, `activateResume(id)`, `deleteResume(id)`, `listJobs`, `uploadJobPdf(file)`, `createJobText(title, text)`, `deleteJob(id)`, `loadDemo()`.
- [ ] **Step 2: page.tsx** becomes a client component owning `resumes`, `jobs`, `refresh()`; renders TopBar (wordmark + Load demo data button with pending state), Sidebar, main area (EmptyState until documents exist).
- [ ] **Step 3: Sidebar**: "Resumes" group (ResumeCard: name, headline, active marker, click to activate, delete on hover) and "Positions" group (JobCard: `#seq`, title, company; score UI arrives Task 11). UploadZone (drag-drop + click, accepts PDF, posts, refreshes) for resumes; jobs get UploadZone + "Paste text" opening PasteJobModal (title optional + textarea).
- [ ] **Step 4: verify** in browser against dev backend: demo button fills sidebar; uploading `backend/data/demo/pdfs/r1.pdf` works end to end. Commit: `feat: document sidebar with uploads and demo load`.

---

## Slice 2: Matching

### Task 11: Match engine (TDD) and fit wiring

**Files:**
- Create: `backend/app/services/matching.py`
- Modify: `backend/app/routers/jobs.py`, `backend/app/schemas.py`, `frontend/components/JobCard.tsx`, create `frontend/components/ScoreRing.tsx`
- Test: `backend/tests/test_matching.py`

- [ ] **Step 1: failing tests** (build small ResumeExtract/JDExtract fixtures inline):
  - full required match, no nice, no min years -> score 100
  - half of 4 required matched, nothing else present -> 50
  - weight redistribution: JD with required only (no nice, no years) uses weight 1.0 on req_cov; JD with required + years but no nice splits 0.70/0.10 renormalized to 0.875/0.125
  - experience: candidate 3y vs min 6y -> exp_fit 0.5; no min years -> component absent
  - alias-level matching: resume "Postgres" matches JD "PostgreSQL"
  - adjacent skills never match: resume React vs JD Vue -> Vue in missing_required
  - verdict bands at 80/60/40 boundaries (80 -> strong fit, 79 -> good fit)
  - MatchResult carries jd_evidence for every matched and missing entry and resume_evidence for matched
- [ ] **Step 2: implement** `match(resume: ResumeExtract, jd: JDExtract) -> MatchResult` exactly per SPEC section 6: canonical case-insensitive set matching via `same_skill`, weighted mean with proportional redistribution of absent components, `round()` to int score, verdict banding. Pure, no I/O. `MatchResult` is a Pydantic model in `matching.py` (schemas.py imports it).
- [ ] **Step 3:** tests pass.
- [ ] **Step 4: wire**: `GET /api/jobs` and `GET /api/jobs/{id}` load the active resume once and attach `fit` (None when no active resume). `POST /api/jobs` response includes fit too.
- [ ] **Step 5: frontend**: ScoreRing (SVG ring, mono number, band color via CSS variables, animates stroke on mount), JobCard shows ring + verdict word; clicking a job could expand matched/missing lists (simple disclosure, gaps show the JD evidence line as a quote).
- [ ] **Step 6: verify**: demo data shows a spread (J7 high for R1, J1 low-mid, etc.); switching active resume changes scores. Commit: `feat: deterministic match engine with fit scores in sidebar`.

---

## Slice 3: Chat

### Task 12: Retrieval and chat pipeline (backend)

**Files:**
- Create: `backend/app/services/retrieval.py`, `backend/app/services/chat_pipeline.py`, `backend/app/routers/chat.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_chat_pipeline.py`

- [ ] **Step 1: retrieval.py**: `retrieve(session, query, resume_id, job_ids, k=6)`: embed query via adapter, `SELECT ... ORDER BY embedding <=> :q LIMIT k` using `Chunk.embedding.cosine_distance`, scoped with `owner_id IN (resume + jobs)`; returns chunks with owner labels.
- [ ] **Step 2: router call.** `RouteResult {intent: Literal[fit_assessment, skill_gap, comparison, interview_prep, narrative, out_of_scope], job_seqs: list[int], all_jobs: bool}`. `route(message, history, inventory)` uses `messages.parse` with `output_config={"effort": "low"}`, max_tokens 4096. Prompt includes: job inventory as `#seq title at company` lines, the last 10 chat messages, rules (questions answerable only from the uploaded documents are in scope; salary negotiation, market trends, life advice are out_of_scope; "which fits best" is comparison with all_jobs=true; follow-ups inherit the previous intent when the new message only changes the job reference).
- [ ] **Step 3: evidence packs.** Builders returning `list[Evidence {id: "E1"..., doc_type, doc_id, doc_label, quote}]` plus a context string:
  - fit/skill_gap/interview_prep: from `match()` for referenced jobs; every matched entry contributes resume+jd quotes, every missing entry the jd quote; interview_prep also adds JD responsibilities as evidence items. Include the numeric score and verdict in the context string.
  - comparison: run match for all jobs, evidence from top entries of each, context lists every job with score.
  - narrative: `retrieve()` chunks as evidence.
- [ ] **Step 4: generation.** System prompt: answer only from the evidence pack and conversation, cite every factual claim as `[En]`, never invent skills or requirements, adjacent-skill commentary allowed but labeled as commentary and never counted toward scores, concise editorial tone, no em dashes. Stream via `client.messages.stream(model, max_tokens=16000, system=..., messages=history_last_10 + [user turn with evidence pack + question])`.
- [ ] **Step 5: SSE endpoint.** `POST /api/chat` returns `StreamingResponse` (media_type `text/event-stream`) emitting events per SPEC section 7 plus a `router` event: `router {intent, job_seqs}`, `delta {text}`, `citations [{id, doc_type, doc_id, doc_label, quote}]` (only ids actually cited in the answer text, extracted with `re.findall(r"\[E\d+\]", full_text)`), `done {message_id, meta}`, `refusal {}`, `error {detail}`. `meta` carries `{missing_required: [...]}` for skill_gap and `{scores: [{job_seq, score}]}` for comparison (evals depend on this). out_of_scope: stream the fixed refusal text as one `delta`, then `refusal`, then `done`; no generation call. Persist user + assistant messages (assistant with intent + citations). Handle `stop_reason == "refusal"` from the API by emitting `error`.
- [ ] **Step 6: history endpoint** `GET /api/chat/messages` returns all messages oldest-first.
- [ ] **Step 7: tests** (pure parts): citation extraction maps only cited ids; refusal path emits no citations; evidence pack for a known fixture pair contains the JD evidence line for a missing skill (use match() directly, no network).
- [ ] **Step 8:** manual smoke test with curl against dev stack: one skill_gap question streams deltas and citations. Commit: `feat: chat pipeline with routing, grounding, citations, refusal`.

### Task 13 (frontend): Chat UI

**Files:**
- Create: `frontend/lib/sse.ts`, `frontend/components/chat/Chat.tsx`, `frontend/components/chat/MessageList.tsx`, `frontend/components/chat/MessageBubble.tsx`, `frontend/components/chat/CitationChip.tsx`, `frontend/components/chat/Composer.tsx`
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1: sse.ts**: `streamChat(message, handlers)` does `fetch("/api/chat", {method: "POST", body: JSON...})`, reads `response.body` with a TextDecoder, splits SSE frames (`event:` + `data:` lines separated by blank line), dispatches to `onRouter/onDelta/onCitations/onRefusal/onDone/onError`.
- [ ] **Step 2: Chat.tsx** owns messages state, loads history on mount (`GET /api/chat/messages`), appends streaming assistant text live, swaps in citations on the `citations` event. Composer: textarea, Enter to send, disabled while streaming, suggestion chips when empty ("What skills am I missing for Job #2?", "Which of these roles fits me best and why?", "Help me prep for the Job #5 interview").
- [ ] **Step 3: MessageBubble** renders `[En]` markers as inline CitationChip components (superscript accent chips); clicking expands a panel under the message showing quote + source label. Refusal messages get a muted "outside my scope" badge. User messages echoed in Fraunces italic; assistant in Instrument Sans; streaming caret while active.
- [ ] **Step 4: verify** in browser: full demo conversation across intents, citations expand, refusal badge shows for "should I ask for a raise?". Commit: `feat: streaming chat ui with citation chips`.

---

## Slice 4: Evals and polish

### Task 14: Eval suite

**Files:**
- Create: `backend/evals/__init__.py`, `backend/evals/cases.yaml`, `backend/evals/run.py`
- Modify: `Makefile`

- [ ] **Step 1: cases.yaml**, 13 cases per SPEC section 10. Shape: `{name, active_resume: "Maya Chen", question, expect: {kind: skill_gap|grounded|refusal|ranking|router, ...}}`. Expected values derived from the demo JSON (e.g. R2 Diego vs J2: missing_required exactly ["Kubernetes"]; R1 Maya vs J1: missing_required ["Vue", "Pinia"]; ranking for R1 -> top job_seq 7; router case expects intent skill_gap and job_seqs [2]).
- [ ] **Step 2: run.py**: httpx against `BASE_URL` (default `http://localhost:8000`): POST /api/demo, then per case: activate the named resume (lookup by name via GET /api/resumes), POST /api/chat consuming the SSE stream, collect events, assert per kind: `skill_gap` -> set(meta.missing_required) equals expected; `grounded` -> every citation quote is a whitespace-normalized substring of the source doc's raw_text (fetch via GET /api/jobs/{id} or /api/resumes); `refusal` -> refusal event present and citations empty; `ranking` -> meta.scores argmax equals expected seq; `router` -> router event fields match. Print a table (case, kind, PASS/FAIL, note), exit 1 on any failure.
- [ ] **Step 3: Makefile** `eval`: `docker compose up -d db && (start backend if not running) && cd backend && uv run python -m evals.run`. Simplest robust form: require dev backend running, document it; the target checks `/health` first and fails fast with a clear message.
- [ ] **Step 4: run `make eval`**, fix pipeline issues until 13/13 pass. Commit: `feat: deterministic eval suite (13 cases)`.

### Task 15: README, polish, final verification

**Files:**
- Create: `README.md`
- Modify: UI components as needed, `SPEC.md` (add `router` SSE event to section 7 protocol line)

- [ ] **Step 1: README.md** sections: what it is (2 lines), quickstart (copy .env.example, `docker compose up --build`, open :3000, Load demo data), architecture (mermaid, prose summary), API table, evals (`make eval`) and tests (`make test`), decisions log (condensed from SPEC section 14), productionization path (auth + per-user isolation, Alembic, ANN index, queueing extraction, AWS deployment), what I'd do with more time. Insert clearly marked blocks the user writes themselves:

```markdown
<!-- TODO(bohdan): write in your own words -->
> _TODO: my reasoning here._
<!-- /TODO -->
```

  placed under: why Option 4, stack choice, vendor split, what I'd do with more time. Do not fill them with generated prose.
- [ ] **Step 2: UI polish pass**: empty states, loading skeletons for extraction (upload shows "Reading..." card state), error toasts (plain inline messages, no library), score ring animation, focus states, responsive-enough at 1280px+.
- [ ] **Step 3: full verification**: `make test` green; `make eval` 13/13; `docker compose down -v && docker compose up --build` from scratch, demo + chat flow works in browser via the compose frontend.
- [ ] **Step 4:** Commit: `docs: readme with decisions log and owner TODO blocks` plus any `fix:`/`polish:` commits.

### Task 16: Publish

- [ ] **Step 1:** `git log` sanity pass (no secrets: `git grep -I "sk-ant\|sk-proj" $(git rev-list --all)` must be empty).
- [ ] **Step 2:** `gh repo create rumbo --public --source . --push`.
- [ ] **Step 3:** Report the repo URL and a summary of verification results.

---

## Self-review notes

- Spec coverage: sections 2-12 map to Tasks 1-15; section 16 pin lands in Task 1 pyproject; demo wipe incl. chat_messages in Task 9 Step 2; history-aware router and generation in Task 12 Steps 2 and 4; `router` SSE event is an addition to the SPEC protocol and gets folded back into SPEC in Task 15.
- Type consistency: `MatchResult` defined once in `matching.py`, imported by `schemas.py` and the pipeline; `Evidence` ids `En` used identically in generation prompt, citation regex, and frontend chips; `RouteResult.job_seqs` used by evals Task 14.
- Known risk: extraction latency on upload (one opus call, seconds). Accepted for demo scale; upload UI shows a pending state (Task 15 Step 2).
