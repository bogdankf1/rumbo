# CLAUDE.md

Standing instructions for AI coding assistants working in this repository.
These rules were in force for the entire build and stay in force for any
future session.

## Workflow

- Spec first. No implementation before `SPEC.md` covers the change and the
  owner has approved it. The spec is the source of truth for behavior.
- Work in vertical slices, each with an explicit verification step. A slice is
  done only when unit tests pass, the eval suite passes, and the change is
  confirmed by hand in the running app.
- Reproduce bugs before fixing them. A fix without a reproduced root cause is
  a guess.
- Commit per slice with messages that explain why, not just what.

## Non-negotiables

- Determinism at AI boundaries. Anything numeric or factual (fit scores,
  skill matching, rankings) is computed in plain Python and handed to the
  model as facts. The model never computes or adjusts numbers.
- Every model claim must trace to a source. Evidence quotes are validated as
  verbatim substrings of the raw document text; unverified evidence is never
  cited. Citations returned to the UI are only ids the answer actually used.
- Out-of-scope questions get the fixed server-side refusal, never a generated
  answer.
- Never weaken the eval suite to make it pass. Evals assert structure (set
  equality, events, substrings), never model prose.
- Secrets only via environment variables. Nothing key-shaped in the repo or
  its git history, ever.
- Simplicity: no new abstraction, dependency, or configuration knob without a
  concrete present need. One or two levels of abstraction where ten would fit.
- No em dashes anywhere: code, UI copy, docs, commit messages.

## Commands

- `docker compose up --build` runs everything (frontend :3000, API :8000, db :5433).
- `make dev-db` / `make dev-backend` / `make dev-frontend` for local dev.
- `make test` runs pytest (no API keys needed).
- `make eval` runs the 13-case deterministic eval suite (needs both API keys
  and a running backend).

## Map

- `SPEC.md`: approved specification (architecture, data model, API contract,
  decisions log).
- `docs/plans/`: the implementation plan the build followed.
- `backend/app/services/`: the pipeline (extraction, matching, chunking,
  embeddings adapter, retrieval, chat).
- `backend/evals/`: eval cases and runner.
- `frontend/components/`: UI; all colors go through semantic tokens in
  `frontend/app/globals.css` (dark and light themes).
