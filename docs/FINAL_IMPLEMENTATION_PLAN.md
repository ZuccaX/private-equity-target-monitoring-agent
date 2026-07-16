# PE Origination Agent Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `executing-plans` to implement
> this plan task by task. Keep `docs/IMPLEMENTATION_STATUS.md` current and stop
> at every mandatory milestone checkpoint.

**Goal:** Complete the current repository as a locally runnable, resume-ready
Private Equity Origination Agent Platform without rewriting working behavior or
requiring paid services, live credentials or network access for tests.

**Architecture:** Evolve the existing Next.js/FastAPI/PostgreSQL application in
place. Preserve route and data compatibility, add an Alembic-managed relational
foundation, keep business logic in services, place MCP behind typed adapters,
and use LangGraph only to orchestrate those services with persisted steps and
human approval.

**Tech stack:** Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic,
PostgreSQL 16, pgvector, LangGraph, MCP, Next.js 16 App Router, React 19,
TypeScript, pnpm, Docker Compose and pytest.

---

## Authority, execution boundary and invariants

Apply documentation and instruction sources in this order:

1. the user's latest explicit instructions in the current thread;
2. `CODEX_MASTER_PROMPT_PE_AGENT.md`;
3. repository and path-specific `AGENTS.md` safety/execution rules;
4. this plan for Modules 0–15 scope, milestone requirements and Definition of Done;
5. `docs/ARCHITECTURE_DECISIONS.md` for confirmed implementation decisions;
6. `docs/IMPLEMENTATION_STATUS.md` for actual progress and test evidence;
7. `README.md` and `README_ZH.md` for public product overview, setup and demo.

The source tree and test evidence determine what is actually implemented.
Neither README may substitute for this detailed plan. If a README conflicts
with a higher-authority source, report the conflict, confirm the implementation
decision, and then synchronize the README rather than silently following it.

This plan maps all Modules 0–15. Milestone 0 is complete, subject to the
documentation-authority correction recorded as its final addendum. Milestone 1
must not start until that correction passes `git diff --check`.

Invariants across all milestones:

- no speculative wholesale rewrite;
- no destructive database reset or migration-history deletion;
- no real credentials, confidential data or real email sending;
- no network/API/model dependency in automated tests;
- no business logic hidden in graph nodes or MCP transport;
- no response-envelope rewrite that breaks the existing frontend;
- no milestone completion claim based only on written code.

## Mandatory checkpoint after every milestone

Do not enter the next milestone immediately after implementation. First:

1. run all unit tests for new or modified behavior;
2. run integration tests across every affected module boundary;
3. run regression tests for previously working core behavior;
4. run backend compilation and relevant frontend lint/type/build checks;
5. validate new Alembic migrations against an isolated test database;
6. run `git diff --check` and inspect the full diff for accidental deletion,
   secrets, dead code and unrelated changes;
7. update `docs/IMPLEMENTATION_STATUS.md` with exact commands, pass/fail/skip
   counts and remaining limitations;
8. fix every newly introduced failure and rerun the checkpoint;
9. commit only after the checkpoint passes and Git/worktree policy permits it.

If a checkpoint fails, stop later milestone work, diagnose and fix the cause,
then rerun the checkpoint. Use targeted tests during implementation,
milestone-level regressions at checkpoints, and the complete full-stack suite
in Milestone 8.

## Current file ownership map

| Area | Existing source of truth | Preserve during evolution |
|---|---|---|
| Backend startup/config | `apps/api/main.py`, `apps/api/app/core/config.py`, `apps/api/app/core/database.py`, `apps/api/app/core/vector.py` | `/health`, local CORS behavior until replacement is tested |
| Domain persistence | `apps/api/app/models/*.py`, `apps/api/app/repositories/*.py` | Current table/column data and response identities |
| API contracts | `apps/api/app/schemas/*.py`, `apps/api/app/api/routes_*.py` | Existing endpoint paths and unwrapped response shapes |
| Business services | `apps/api/app/services/*.py` | Deterministic hashing, scoring and template fallback behavior |
| Workflow | `apps/api/app/agents/origination_workflow.py`, `apps/api/app/services/agent_run_service.py` | Working synchronous path until graph parity tests pass |
| Data lifecycle | `apps/api/scripts/*.py`, `data/seed/*.json` | Rerunnable external IDs and mock-only data |
| Frontend contracts | `apps/web/src/lib/api.ts` | Existing methods/types until backend contracts stabilize |
| Frontend UI | `apps/web/src/app/**`, `apps/web/src/components/**` | Current pages, button API and App Router conventions |
| Local infrastructure | `docker-compose.yml`, `.env.example`, `apps/api/requirements.txt`, `apps/web/package.json`, `apps/web/pnpm-lock.yaml` | PostgreSQL/pgvector service and locked frontend versions |

## Modules 0–15: exact file plan

### Module 0 — Project infrastructure

**Preserve:** `docker-compose.yml`, `.env.example`, `apps/api/main.py`,
`apps/api/app/core/config.py`, `apps/api/app/core/database.py`,
`apps/web/package.json`, `apps/web/pnpm-lock.yaml`.

**Modify:** `docker-compose.yml`, `.env.example`, `apps/api/main.py`,
`apps/api/requirements.txt`, `apps/api/app/core/config.py`,
`apps/api/app/core/database.py`, `apps/web/next.config.ts`, `README_ZH.md`.

**Create:** `Makefile`, `apps/api/Dockerfile`, `apps/web/Dockerfile`,
`apps/api/requirements-dev.txt`, `apps/api/app/core/logging.py`,
`apps/api/app/api/routes_health.py`, `apps/api/tests/conftest.py`,
`apps/api/tests/unit/test_config.py`, `apps/api/tests/integration/test_health.py`,
`.github/workflows/ci.yml`.

**Outcome:** explicit dev/test settings, request/run IDs, `/health`, `/ready`,
integration health, isolated test DB guard, health checks, repeatable commands,
CI compile/tests/lint/build and production-safe containers.

### Module 1 — Frontend dashboard

**Preserve:** `apps/web/src/lib/api.ts`, UI primitives under
`apps/web/src/components/ui/`, current pages and `apps/web/src/components/site-nav.tsx`.

**Modify:** `apps/web/src/lib/api.ts`, `apps/web/src/components/site-nav.tsx`,
all existing files under `apps/web/src/app/`, and company detail sections under
`apps/web/src/components/company-*-section.tsx`.

**Create:** `apps/web/src/app/mandates/page.tsx`,
`apps/web/src/app/pipeline/page.tsx`,
`apps/web/src/app/agent-runs/[runId]/page.tsx`,
`apps/web/src/app/audit/page.tsx`, `apps/web/src/app/feedback/page.tsx`,
`apps/web/src/app/integrations/page.tsx`,
`apps/web/src/components/loading-state.tsx`,
`apps/web/src/components/empty-state.tsx`,
`apps/web/src/components/error-state.tsx`, and focused feature components only
when a page would otherwise become larger or duplicate logic.

**Tests:** create frontend component/smoke tests using the framework chosen in
Module 0, plus a deterministic browser smoke path in Milestone 8.

### Module 2 — Backend API

**Preserve:** all existing `apps/api/app/api/routes_*.py` paths and existing
Pydantic response fields.

**Modify:** current routes/schemas/services to add validated pagination,
filtering, sorting, domain errors and OpenAPI descriptions without an envelope
rewrite.

**Create:** `apps/api/app/api/routes_mandates.py`,
`routes_pipeline.py`, `routes_integrations.py`, `routes_audit.py`,
`routes_feedback.py`; `apps/api/app/schemas/common.py`, `mandate.py`,
`pipeline.py`, `integration.py`, `audit.py`, `feedback.py`;
`apps/api/app/core/exceptions.py`.

**Tests:** route contract tests for all preserved and new endpoints under
`apps/api/tests/integration/api/`.

### Module 3 — Database layer

**Preserve:** all existing model/table data and foreign-key identities.

**Modify:** `apps/api/app/models/__init__.py` and existing model/repository/schema
files for additive fields, constraints and indexes.

**Create:** `apps/api/alembic.ini`, `apps/api/alembic/env.py`,
`apps/api/alembic/script.py.mako`, `apps/api/alembic/versions/0001_baseline.py`,
`apps/api/alembic/versions/0002_milestone1_core.py`,
`apps/api/app/models/investment_mandate.py`, `agent_run_step.py`, `feedback.py`,
`email_revision.py`; corresponding repository and schema files;
`apps/api/tests/integration/db/test_migrations.py`.

**Migration rule:** create current schema cleanly at baseline; schema-verify and
stamp a compatible existing database; then apply additive changes. Test clean,
existing-copy, downgrade and re-upgrade paths.

### Module 4 — Vector/RAG foundation

**Preserve:** `embedding_service.py`, `chunking_service.py`,
`document_indexing_service.py`, `vector_search_service.py`,
`document_chunk_repository.py`, `document_chunk.py`, `scripts/index_documents.py`.

**Modify:** those files to depend on typed provider interfaces, enforce model
and dimension compatibility, batch embeddings, filters, thresholds and bounds.

**Create:** `apps/api/app/services/embeddings/base.py`, `hashing.py`,
`sentence_transformer.py`, `registry.py`, plus unit tests under
`apps/api/tests/unit/services/` and vector integration tests under
`apps/api/tests/integration/vector/`.

**Migration:** add model/version metadata and a safe pgvector HNSW index only
after current data is verified and reindex behavior is tested.

### Module 5 — Seed data

**Preserve:** current JSON file names and stable external IDs where possible.

**Modify:** all `data/seed/*.json`, `apps/api/scripts/seed_data.py`,
`apps/api/scripts/index_documents.py`.

**Create:** `data/seed/mandates.json`, `data/seed/feedback.json`, and deterministic
evaluation fixtures under `apps/api/tests/fixtures/`.

**Outcome:** 6–8 companies, two mandates, 3–5 news and documents per company,
positive/negative/duplicate/irrelevant/fallback/approval scenarios, and a
rerunnable quality report.

### Module 6 — LangGraph workflow

**Preserve:** `apps/api/app/agents/origination_workflow.py` as a compatibility
adapter until graph parity is established; preserve service boundaries.

**Modify:** `apps/api/app/services/agent_run_service.py`,
`apps/api/app/api/routes_agent_runs.py`, `apps/api/app/schemas/agent_run.py`.

**Create:** `apps/api/app/agents/state.py`, `nodes.py`, `routing.py`, `graph.py`,
`checkpoint.py`; graph scenario tests under `apps/api/tests/integration/agents/`.

**Outcome:** typed state, required nodes/routes, persisted run steps,
MCP/RAG/LLM fallbacks, and approval pause/resume compatible with the installed
LangGraph version.

### Module 7 — News crawler

**Preserve:** `news_article.py`, `news_article_repository.py`,
`news_article_service.py`, `routes_news_articles.py`.

**Modify:** those files plus `.env.example`, settings and seed scripts for
canonical URL/hash/status/reliability/match fields and sync actions.

**Create:** `apps/api/app/integrations/news/base.py`, `mock.py`, `rss.py`,
`public_page.py`, `url_safety.py`; `apps/api/app/services/news_ingestion_service.py`;
`apps/api/scripts/sync_news.py`; deterministic no-network tests under
`apps/api/tests/unit/news/` and `apps/api/tests/integration/news/`.

### Module 8 — Trigger extraction

**Preserve:** `trigger_extraction_service.py`, `trigger_service.py`,
`trigger_repository.py`, `trigger.py`, `routes_triggers.py`.

**Modify:** those files for positive/negative rules, evidence sentence, event
date, method, dedupe key, validation and review status.

**Create:** `apps/api/app/services/trigger_providers/base.py`, `rules.py`,
`llm.py`; trigger unit/idempotency tests under `apps/api/tests/unit/triggers/`
and `apps/api/tests/integration/triggers/`.

### Module 9 — CRM MCP integration

**Preserve:** `crm_service.py`, contact/interaction models and repositories as
the local business/data implementation.

**Modify:** `crm_service.py`, settings, agent nodes and integration health/audit.

**Create:** `apps/api/app/integrations/crm/base.py`, `direct.py`, `mcp_client.py`,
`schemas.py`; `mcp_servers/crm/server.py`, `tools.py`; local MCP and fallback
tests under `apps/api/tests/integration/mcp/test_crm_mcp.py`.

### Module 10 — Egnyte/document MCP integration

**Preserve:** document models/repositories/services/indexing and current mock
document data.

**Modify:** those files for content hash, version, sync/index state, safe
extraction, idempotency and soft deletion.

**Create:** `apps/api/app/integrations/documents/base.py`, `direct.py`,
`mcp_client.py`, `extractors.py`, `path_safety.py`; `mcp_servers/documents/server.py`,
`tools.py`; safe extraction/sync/index/fallback tests.

### Module 11 — RAG service

**Preserve:** `rag_retrieval_service.py`, `routes_rag.py`, vector schemas and
current company-scoped search behavior.

**Modify:** those files for company/mandate/trigger query building, document
filters, threshold, source diversity, context limits, citations, empty status,
audit and untrusted-content warnings.

**Create:** `apps/api/app/services/rag_query_service.py`,
`rag_context_service.py`, `rag_safety_service.py`; focused RAG tests under
`apps/api/tests/unit/rag/` and `apps/api/tests/integration/rag/`.

### Module 12 — Priority scoring

**Preserve:** `scoring_service.py`, `priority_score.py`, repository/schema and
existing `v3-crm-trigger-aware` records.

**Modify:** those files for mandate-aware versioned weights, business quality,
internal evidence, negative-trigger penalty and explainable recommendations.

**Create:** `apps/api/app/services/recommendation_service.py`,
`apps/api/app/schemas/scoring_config.py`, scoring/recommendation regression
tests under `apps/api/tests/unit/scoring/`.

### Module 13 — Email drafting

**Preserve:** `email_generation_service.py`, the template provider behavior,
and the current draft response shape.

**Modify:** email generation/draft services, models and schemas for provider
selection, validated output, warnings, evidence/version metadata and length/
claim safety.

**Create:** `apps/api/app/services/email_providers/base.py`, `template.py`,
`remote_llm.py`, `apps/api/app/services/email_validation_service.py`, and
provider/fallback/safety tests under `apps/api/tests/unit/email/`.

### Module 14 — Human approval

**Preserve:** approval/audit tables and `PATCH /api/drafts/{draft_id}` until a
compatible transition API is available.

**Modify:** draft/approval models, repositories, schemas, services and routes;
agent resume behavior; drafts UI.

**Create:** `apps/api/app/models/email_revision.py`, its repository/schema,
`apps/api/app/services/approval_service.py`, `mock_email_sender.py`, explicit
review/send routes, and transition/send-gate integration tests.

### Module 15 — Audit and feedback

**Preserve:** `audit_log.py` and `audit_log_repository.py` data.

**Modify:** audit model/repository for safe summaries, durations, run/tool/
fallback metadata and redaction.

**Create:** feedback model/repository/schema/service/routes; audit service and
redaction utility; frontend audit/feedback pages; metrics and redaction tests.

## Milestone execution plan

### Milestone 0 — Freeze and understand baseline (complete with final documentation addendum)

- [x] Inspect Git state, repository instructions and the full source tree.
- [x] Treat both READMEs as public documentation, not implementation authority.
- [x] Inspect dependencies, Compose, environment example, models, schemas,
  repositories, services, routes, pages, components, API client, seeds and scripts.
- [x] Verify the live database read-only: readiness, vector extension, tables,
  columns, constraints, indexes and aggregate counts.
- [x] Run backend compile, frontend lint/type/build and Compose validation.
- [x] Record pre-existing missing tests/Alembic/test DB separately from new failures.
- [x] Create `AGENTS.md`, this plan, status ledger and architecture decisions.
- [x] Make the minimal offline-safe frontend font change.
- [x] Rerun frontend lint, typecheck and production build.
- [x] Run final compile, `git diff --check`, secret/deletion/dead-code review.
- [x] Mark complete only after the gate passes; do not start Milestone 1.
- [x] Apply the seven-level documentation authority model, synchronize both
  READMEs, and rerun `git diff --check` before Milestone 1.

Expected commit if authorized after the gate:
`docs: freeze milestone 0 implementation baseline`.

### Milestone 1 — Infrastructure, migrations and core models

Implement Modules 0, 2 and 3 test-first: install/pin dev tooling, isolate the
test database, write baseline/upgrade tests, introduce Alembic, add health/
logging/settings, then mandates, pipeline, run steps, feedback/revisions and
compatible routes. Gate on clean/existing DB upgrade, downgrade/re-upgrade,
backend compile/tests and affected frontend contracts.

**Status:** Complete — checkpoint passed on 2026-07-13. Evidence and exact
commands are recorded in `docs/IMPLEMENTATION_STATUS.md`.

### Milestone 2 — Semantic vector/RAG foundation and seeds

Implement Modules 4, 5 and 11 test-first. Keep hashing fallback, add the
semantic provider behind an optional dependency, enforce model/dimension
compatibility, add filters/threshold/bounds/safety, expand deterministic seeds
and record retrieval evaluation honestly.

**Status:** Complete — checkpoint passed on 2026-07-14 with zero required
skips. Hashing and the pinned offline MiniLM cohort, migration/prune safety,
company-scoped RAG, deterministic seeds/evaluation, frontend/build validation
and live host/Docker/HTTP probes are recorded in
`docs/IMPLEMENTATION_STATUS.md`. Milestone 3 subsequently completed under the
checkpoint below.

### Milestone 3 — News and trigger intelligence

Implement Modules 7 and 8 with no-network adapters and idempotency fixtures.
Gate on duplicate-free reruns, controlled event dedupe, negative risk input and
strict URL/size/timeout tests.

**Status:** Complete — checkpoint passed on 2026-07-14 with zero required
skips. Default-offline mock sync, opt-in allowlisted RSS/Atom and static-page
adapters, 14 canonical trigger categories, lifecycle/idempotency, migration,
API/CLI, transaction/audit and disposable full-stack evidence are recorded in
`docs/IMPLEMENTATION_STATUS.md`. Milestone 4 has not started.

### Milestone 4 — MCP enterprise boundaries

Implement Modules 9 and 10 with local MCP servers, typed clients, allowlists,
timeouts, audit and direct fallbacks. Gate on local retrieval, stopped-server
fallback and side-effect approval enforcement.

### Milestone 5 — LangGraph orchestration

Implement Module 6 only after service boundaries are stable. Establish parity
with the synchronous workflow, then enable conditional routes, persisted steps
and approval pause/resume. Gate high/medium/low/fallback/empty/resume scenarios.

### Milestone 6 — Scoring, drafting, approval and feedback

Implement Modules 12–15, including the backend send invariant. Gate on score/
recommendation versions, evidence, unsupported-claim handling, revision/audit,
feedback and proof that unapproved drafts cannot send.

### Milestone 7 — Frontend completion

Complete Module 1 using the stable API client and installed Next.js 16 docs.
Gate `pnpm lint`, `pnpm exec tsc --noEmit`, `pnpm build` and the affected UI
smoke paths; the demo must not require Swagger or direct SQL.

### Milestone 8 — Final hardening and resume package

Run the complete backend unit/integration suite, migration matrix, frontend
checks and browser smoke path. Finalize CI, the primary Chinese README, Mermaid diagrams, demo
script, screenshot checklist, limitations and only evidence-backed resume
bullets. Run the full no-network full-stack suite and final secret/diff audit.

## Repository Definition of Done

Completion requires evidence for every applicable item; planned or written code
does not count as complete without its checkpoint result.

### Engineering

- [x] Docker Compose validates and health checks work.
- [x] Backend compilation and the complete backend test suite pass.
- [x] Frontend lint, typecheck and production build pass.
- [x] Alembic upgrades a clean test database.
- [x] Alembic upgrades a compatible existing database without destructive loss.
- [x] Migration downgrade/re-upgrade paths pass on test data.
- [ ] CI runs backend and frontend gates.
- [x] No secrets are committed and `git diff --check` passes.

### Data, ETL and retrieval

- [x] Seeds cover high, medium and low priority scenarios.
- [x] News and document synchronization are idempotent for the deterministic M2 fixtures.
- [x] Duplicate news and trigger events are controlled.
- [x] Hashing fallback and semantic embeddings are supported without mixing models.
- [x] Reindexing, thresholds, filters and evaluation evidence are present.
- [x] Empty RAG retrieval does not fail the workflow.
- [x] Retrieved and crawled content is handled as untrusted data; crawler URL, DNS, redirect, size, timeout and parsing controls are tested.

### MCP and orchestration

- [ ] CRM and document MCP integrations work locally with typed contracts.
- [ ] Timeouts, allowlists, audit and direct fallbacks are tested.
- [ ] Side-effecting tools require explicit approval.
- [ ] LangGraph nodes/routes run, persist step status and exercise fallbacks.
- [ ] Approval pause and resume work with the installed LangGraph version.

### PE workflow and human review

- [ ] Mandates and pipeline state are configurable and manageable.
- [ ] Scores, risk penalties and recommended actions are explainable/versioned.
- [ ] Negative triggers affect risk and action recommendations.
- [ ] Drafts are grounded, editable and revision history is retained.
- [ ] Approve, reject and request-changes transitions are audited.
- [ ] An unapproved draft cannot be sent, including through direct API calls.
- [ ] Feedback and audit views explain evidence, tools, fallbacks and reviewers.

### Presentation

- [ ] `README.md` is a concise English public landing page.
- [ ] `README_ZH.md` is the detailed Chinese public product overview.
- [ ] Both READMEs link to each other and to the detailed implementation docs.
- [ ] Architecture, LangGraph and MCP diagrams reflect verified behavior.
- [ ] Demo data, startup/test instructions and a three-minute demo are documented.
- [ ] Limitations are explicit and resume bullets mention only verified features.
