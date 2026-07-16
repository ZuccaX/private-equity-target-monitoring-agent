# Implementation Status

Last updated: 2026-07-16 (Europe/London)

## Authority and scope

Apply the following precedence:

1. the user's latest explicit instructions in the current thread;
2. `CODEX_MASTER_PROMPT_PE_AGENT.md`;
3. repository/path-specific `AGENTS.md` safety and execution rules;
4. `docs/FINAL_IMPLEMENTATION_PLAN.md` for Modules 0–15 scope, milestones and DoD;
5. `docs/ARCHITECTURE_DECISIONS.md` for confirmed decisions;
6. this file for actual progress and test evidence;
7. `README.md` and `README_ZH.md` for public overview, setup and demo.

Neither README is an implementation specification. Conflicts must be reported,
resolved against the higher-authority source, and then synchronized in the
README after the implementation decision is confirmed.

- Active scope: **Milestone 3 is the last checkpoint-complete public snapshot;
  Milestone 4 implementation is local work in progress, checkpoint-incomplete
  and excluded from this publication**.
- Working branch: `main`, following the repository owner's standing decision.
- Publication guard: do not commit or publish Milestone 4 implementation until
  its mandatory checkpoint passes.

## Mandatory milestone test policy

At the end of every milestone, do not immediately start the next milestone.
The milestone is not complete merely because its code has been written.

1. Run all unit tests for new or modified behavior.
2. Run integration tests for all affected module boundaries.
3. Run regression tests for previously working core behavior.
4. Run backend compilation and relevant frontend lint/type/build validation.
5. Validate every new Alembic migration against an isolated test database.
6. Run `git diff --check` and inspect the diff for accidental deletion,
   secrets, dead code and unrelated changes.
7. Record exact commands, pass/fail/skip counts and remaining limitations here.
8. Fix all newly introduced failures.
9. Commit the milestone only after the checkpoint passes and Git/worktree
   policy permits it.

If a checkpoint fails, stop later work, diagnose the cause, fix it, and rerun
the checkpoint before continuing. Use targeted tests while implementing,
milestone-level regression tests at each checkpoint, and the complete
full-stack suite in the final milestone.

## Milestone ledger

| Milestone | Status | Gate |
|---|---|---|
| 0 — Baseline freeze/audit | **Complete — gate passed** | Baseline documented; initial build failure fixed; final checkpoint clean |
| 1 — Infrastructure/migrations/core models | **Complete — gate passed** | 24 backend tests, migration matrix, build and Compose health passed |
| 2 — Semantic vector/RAG foundation | **Complete — gate passed** | 73 backend tests, migration/cohort matrix, host/Docker MiniLM, fallback, build and HTTP gates passed |
| 3 — News/trigger intelligence | **Complete — gate passed** | 154 backend tests, 89% coverage, migration matrix, frontend build and isolated full-stack sync/extraction gate passed |
| 4 — MCP enterprise boundaries | **Local implementation in progress — excluded from public M3 snapshot** | Checkpoint incomplete; no completion claim or implementation commit |
| 5 — LangGraph orchestration | Not started | Blocked by milestone order |
| 6 — Scoring/drafting/approval/feedback | Not started | Blocked by milestone order |
| 7 — Frontend completion | Not started | Blocked by milestone order |
| 8 — Final hardening/resume package | Not started | Blocked by milestone order |

## Milestone 0 repository audit

### Git and instructions

- Initial branch: `main`; initial `git status --short`: clean.
- The pre-public local baseline and the existing origin baseline were inspected.
  Unpublished local history is intentionally squashed during public preparation,
  so obsolete local commit identifiers are not presented as public evidence.
- A frontend-only `apps/web/AGENTS.md` existed; no root `AGENTS.md` existed.
- `README_ZH.md` is the detailed Chinese product overview; `README.md` is the
  concise English public landing page. Both are public documentation below the
  implementation plan, architecture decisions and status evidence.
- `apps/web/.env.local` exists but is untracked/ignored; its contents were not
  read or printed.

### Verified current capabilities

- FastAPI exposes health, dashboard, companies, news, triggers, CRM, documents,
  vector search, RAG retrieval, agent-run and draft endpoints.
- SQLAlchemy models/repositories exist for companies, news, triggers, contacts,
  CRM interactions, documents/chunks, runs, scores, drafts, approvals and audit.
- PostgreSQL 16 with pgvector is running under Compose; the vector extension and
  12 application tables exist.
- Current database row counts: 4 companies, 4 news articles, 4 triggers,
  4 contacts, 3 interactions, 4 documents, 4 chunks, 6 runs, 6 scores,
  6 drafts, 0 approvals and 6 audit rows.
- `OriginationWorkflow.run(...)` is synchronous and service-backed, with version
  `v3-crm-trigger-aware`; it is not LangGraph.
- Scoring is deterministic, CRM/trigger-aware and explainable, but mandate-unaware
  and has a zero-valued risk implementation.
- Email drafting is deterministic/template-only and creates pending approval
  drafts; no send endpoint or enforced send gate exists yet.
- CRM and document access are direct repository/service calls, not MCP.
- Documents are split, hashed into 384-dimensional deterministic embeddings,
  stored in pgvector and retrieved with company/model filtering.
- RAG is an independent service but has no threshold, document-type filtering,
  source-diversity control, context bound or prompt-injection policy.
- Next.js pages exist for dashboard, companies/detail, news, triggers, CRM,
  documents, RAG, runs and drafts. There are no mandate, pipeline, audit,
  feedback, integration-health or run-step detail pages.
- Seed files contain four companies, four contacts, three interactions, four
  documents, four news articles and two workflow fixtures.

### Verified absent or incomplete foundations

- No Alembic config, revisions or migration tests.
- No project unit, integration or frontend test files.
- `pytest` is not installed in the existing Python venv.
- No LangGraph dependency or graph/checkpoint code.
- No MCP server/client implementation.
- No crawler adapters or scheduled/news sync action.
- No investment mandate, pipeline, run-step, feedback or email-revision model.
- No Dockerfiles, Makefile/task runner, CI workflow, `/ready` endpoint,
  structured request/run logging or integration health API.
- Python dependency versions are not pinned.
- Public README roadmap content is explicitly labelled planned; the source tree
  and this ledger determine current implementation status.

## Baseline command record

Counts below are command/check counts unless a tool reports test-case counts.
Unavailable suites are marked **skipped/blocked**, never passed.

| Command | Result | Pass / fail / skip | Notes |
|---|---|---:|---|
| `git status --short` | Pass | 1 / 0 / 0 | Empty output at audit start |
| `git branch --show-current` | Pass | 1 / 0 / 0 | `main` |
| `cd apps/api && .venv/bin/python -m compileall app scripts` | Pass | 1 / 0 / 0 | All discovered Python files compiled |
| `cd apps/api && .venv/bin/python -m pytest -q` | Blocked | 0 / 0 / 1 | `No module named pytest`; no project tests exist |
| `cd apps/api && .venv/bin/python -m pip check` | Pass | 1 / 0 / 0 | No broken requirements found; cache warning is environmental |
| `cd apps/web && pnpm lint` | Pass with warnings | 1 / 0 / 0 | 0 errors, 2 unused-function warnings |
| `cd apps/web && pnpm exec tsc --noEmit` | Pass | 1 / 0 / 0 | Exit 0 |
| `cd apps/web && pnpm build` (initial) | Fail | 0 / 1 / 0 | Offline fetch of Geist/Geist Mono from Google Fonts failed |
| `cd apps/web && pnpm build` (post-fix, sandbox) | Environment-blocked | 0 / 0 / 1 | Font error gone; Turbopack could not bind its internal port in the sandbox |
| `cd apps/web && pnpm build` (post-fix, sandbox exception) | Pass | 1 / 0 / 0 | Compiled; TypeScript passed; 12/12 pages generated |
| `docker compose config` | Pass | 1 / 0 / 0 | Compose configuration renders successfully |
| `docker compose ps --format json` | Pass | 1 / 0 / 0 | PostgreSQL service running |
| `docker compose exec -T postgres pg_isready ...` | Pass | 1 / 0 / 0 | Database accepts connections |
| Read-only vector/table/schema queries | Pass | 3 / 0 / 0 | Vector extension, tables and schema/constraints verified |
| Alembic upgrade/downgrade on test DB | Skipped | 0 / 0 / 1 | No Alembic and no isolated test DB; no new migration in Milestone 0 |
| Backend integration/regression suite | Skipped | 0 / 0 / 1 | No suite and no safe test DB configuration |
| Frontend automated smoke suite | Skipped | 0 / 0 / 1 | No frontend test framework/specs |
| `git diff --check` and final diff review | Pass | 1 / 0 / 0 | No whitespace errors; no accidental tracked-file deletion |
| Changed-file secret/dead-code/unrelated-change scan | Pass | 3 / 0 / 0 | No secret-pattern hit; no new dead code; scope limited to docs and offline font fix |

Initial mistaken commands using `apps/api/.venv/bin/python` while already in
`apps/api` exited 127 and did not run any check. They were invocation errors,
not repository failures; the corrected commands and results are recorded above.

## Baseline environment

- Python: 3.12.5
- FastAPI: 0.139.0
- Pydantic: 2.13.4
- SQLAlchemy: 2.0.51
- psycopg: 3.3.4
- pgvector Python package: 0.5.0
- Node.js: 25.9.0
- pnpm: 10.13.1
- Next.js: 16.2.10
- React: 19.2.4
- PostgreSQL image: `pgvector/pgvector:pg16`

## Milestone 0 completion and carried limitations

- [x] Read the authoritative prompt and repository instructions.
- [x] Inspect Git state, tree, dependencies, Docker/Compose and environment docs.
- [x] Inspect backend models, schemas, repositories, services, routes and scripts.
- [x] Inspect frontend pages, components, API client and types.
- [x] Inspect live database schema read-only; do not mutate developer data.
- [x] Run baseline compile, lint, type, build and Compose checks.
- [x] Map current/planned files to Modules 0–15.
- [x] Record architecture and compatibility risks.
- [x] Replace build-time Google font fetching with an offline-safe system font path.
- [x] Rerun frontend lint, typecheck and production build after the fix.
- [x] Run final `git diff --check`, status, secret/deletion/dead-code review.
- [x] Change Milestone 0 to complete only after the checkpoint passes.

The absence of tests, Alembic and a test database is a pre-existing baseline
limitation and a Milestone 1 prerequisite. It is not silently waived for later
milestones: no feature milestone may pass without its applicable tests and
migration checks.

Additional carried warnings at the end of Milestone 0:

- ESLint reports two pre-existing unused-function warnings in
  `apps/web/src/app/agent-runs/page.tsx` and `apps/web/src/app/companies/page.tsx`;
  lint exits 0 and no warning was introduced by Milestone 0.
- Next.js previously warned that a user-level lockfile outside this repository
  affected workspace-root inference. The build succeeded; changing files
  outside the repository remained out of scope.

## Milestone 0 changed files

- `AGENTS.md`: repository commands, conventions, safety and mandatory gates.
- `docs/FINAL_IMPLEMENTATION_PLAN.md`: exact Modules 0–15 file/milestone map.
- `docs/IMPLEMENTATION_STATUS.md`: audit evidence, exact command results and
  milestone policy.
- `docs/ARCHITECTURE_DECISIONS.md`: compatibility decisions and risk register.
- `README.md`: concise English public landing page with verified/current versus
  planned capability labels.
- `README_ZH.md`: detailed Chinese product overview, setup, demo and roadmap.
- `apps/web/src/app/layout.tsx`: remove build-time Google font imports.
- `apps/web/src/app/globals.css`: use offline-safe system sans/mono stacks.

No dependency, database schema, seed data, route, model, service or API contract
was changed. No migration was created, no developer data was mutated, and no
Milestone 1 implementation was started.

## Documentation authority correction addendum

- **Cause:** A prior user annotation said, in Chinese, not to use the English
  README and to use the Chinese README as primary. That presentation preference
  was incorrectly expanded into a requirements/audit authority rule.
- **Correction:** Both READMEs are public documentation. The seven-level
  precedence above now governs implementation and audits.
- **README roles:** `README.md` is the concise English landing page;
  `README_ZH.md` is the detailed Chinese product overview; both cross-link.
- **Milestone 1 gate:** blocked until the documentation diff and cross-links are
  reviewed and `git diff --check` passes.
- **Validation commands:**
  - `git diff --check` — pass (1 / 0 / 0).
  - trailing-whitespace scan across `AGENTS.md`, `docs/` and both READMEs —
    pass (1 / 0 / 0).
  - stale-authority phrase scan — pass (1 / 0 / 0; no stale rule found).
  - README cross-link and required local-document existence checks —
    pass (2 / 0 / 0).
- **Checkpoint status:** passed. Milestone 1 is unblocked by this documentation
  correction and has now started by explicit user instruction.

## Milestone 1 work log

- **Started:** 2026-07-13 (Europe/Paris).
- **Completed:** 2026-07-13 (Europe/Paris); no commit created.
- **Scope:** Modules 0, 2 and 3 only.
- **Development dependencies installed:** Alembic 1.18.5, pytest 9.1.1,
  HTTPX2 2.5.0 and pytest-cov 7.1.0.
- **Safety rule:** test and migration checks must target a database whose name
  contains `test`; its host, port and database identity must not match
  `DATABASE_URL`, even when credentials differ.
- **Database outcome:** the isolated `pe_agent_test` database was used for all
  destructive migration tests. The unversioned developer database was detected
  as the known legacy `create_all()` partial state, repaired additively, stamped
  at `0002_milestone1_core`, and retained all 4 company records.
- **Application outcome:** import-time DDL was removed; `/health`, `/ready`,
  integration health, JSON request/run correlation logging, mandates, pipeline,
  feedback, audit listing, run-step and draft-revision APIs are available.
- **Infrastructure outcome:** pinned runtime/dev dependencies, Make targets,
  CI workflow, non-root production Dockerfiles, Compose health checks and
  frontend standalone output are present.

### Milestone 1 checkpoint command record

Counts are test-case counts where pytest reports them; otherwise they are
command/check counts.

| Command | Result | Pass / fail / skip | Notes |
|---|---|---:|---|
| `cd apps/api && .venv/bin/python -m pytest tests/unit/test_config.py -q` | Pass | 7 / 0 / 0 | Settings, container path and test-DB collision guard |
| `cd apps/api && .venv/bin/python -m pytest tests/integration/db/test_migrations.py -q` | Pass | 4 / 0 / 0 | Clean, baseline-copy, full-M1 unversioned, legacy partial, downgrade/re-upgrade and metadata-drift checks |
| `cd apps/api && .venv/bin/python -m pytest tests/integration/api/test_core_routes.py -q` | Pass | 4 / 0 / 0 | Preserved/new route contracts, workflow steps and revisions |
| `cd apps/api && .venv/bin/python -m pytest tests/integration/services/test_transaction_safety.py -q` | Pass | 2 / 0 / 0 | Safe workflow failure metadata and revision rollback |
| `cd apps/api && .venv/bin/python -m pytest --cov=app --cov-report=term-missing` | Pass | 24 / 0 / 0 | 81% line coverage; no warnings |
| `make test` | Pass | 24 / 0 / 0 | 12 unit and 12 integration tests through repeatable target |
| `make lint` | Pass | 2 / 0 / 0 | Backend compile plus frontend ESLint; 0 errors/warnings |
| `make build` | Pass | 2 / 0 / 0 | Backend compile plus Next.js production build; 12/12 routes generated |
| `docker compose config --quiet` | Pass | 1 / 0 / 0 | Compose configuration valid |
| `docker compose build api web` | Pass | 2 / 0 / 0 | API and Web production images built |
| `docker compose up -d --no-build --wait ... api web` | Pass | 3 / 0 / 0 | PostgreSQL, API and Web all healthy |
| Container `/health`, `/ready` and Web root probes | Pass | 3 / 0 / 0 | HTTP 200 for all probes |
| Developer DB version/data preservation query | Pass | 2 / 0 / 0 | Head is `0002_milestone1_core`; companies remain 4 |
| `git diff --check` and final diff review | Pass | 1 / 0 / 0 | No whitespace error or unintended tracked deletion |
| Added-line secret/dead-code/unrelated-change scan | Pass | 3 / 0 / 0 | No credential/private-key token; ESLint clean; scope limited to M0/M1 |

Checkpoint failures were not waived:

- direct database tests initially reported 2 connection errors because the
  sandbox blocked localhost; the identical authorized command passed;
- Alembic metadata check found 18 baseline drift operations; baseline indexes,
  unique-index form and source length were corrected before the matrix passed;
- the first Web Docker build failed under pnpm 11 supply-chain behavior; the
  repository, Docker build and CI were pinned to pnpm 10.13.1;
- three Compose startup attempts exposed and fixed script import-path, shallow
  container-root and legacy partial-schema compatibility bugs;
- the first sandboxed `make test` passed 11 unit tests but produced 12 database
  connection errors; the unchanged authorized Make command then passed, and the
  final suite increased to 24 after the DB identity regression test;
- the first sandboxed Next build could not bind Turbopack's internal port; the
  authorized build passed. All code/config failures were fixed and rerun.

### Milestone 1 remaining limitations

- CI configuration is present but has not run on GitHub in this local task.
- No frontend automated component/browser suite exists yet; Module 1 frontend
  feature pages and browser smoke coverage belong to Milestones 7–8.
- Integration health reports configured direct repository adapters only; MCP
  transport, timeout/retry and fallback evidence belong to Milestone 4.
- Coverage is 81%, but no repository-wide minimum threshold is enforced yet.
- Existing vector/RAG, news/trigger intelligence, orchestration and send-gate
  limitations remain assigned to later milestones; none were claimed complete.
- Milestone 1 received a dedicated local checkpoint commit after its gate was
  reconfirmed. That unpublished identifier is intentionally omitted because the
  public preparation process squashes local-only history into one reviewed M3
  snapshot.

## Milestone 2 work log

- **Started:** 2026-07-14 (Europe/Paris).
- **Completed:** 2026-07-14 (Europe/Paris); checkpoint passed with no required
  skips and was committed only after the staged diff review passed.
- **Scope:** Modules 4, 5 and 11 only.
- **Model policy:** hashing remains the offline default. The optional semantic
  cohort is pinned to `sentence-transformers/all-MiniLM-L6-v2` revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, 384 dimensions, CPU.
- **Storage policy:** model caches stay outside the repository and are supplied
  through `HF_MODEL_CACHE_DIR`; the real `.env` is not modified.
- **Database outcome:** revision `0003_milestone2_vector_cohorts` adds source
  identity, exact provider/model/version/dimension cohort isolation, compatible
  uniqueness and partial HNSW indexes. A populated multi-cohort downgrade fails
  closed; an explicit export-and-prune operator path permits a tested downgrade.
- **Retrieval outcome:** hashing remains the default, while the pinned MiniLM
  provider loads lazily and offline. Vector search can remain global for an
  explicit debug call; RAG requires `company_id`, enforces bounds/filters,
  builds source-diverse bounded context, treats retrieved text as untrusted,
  removes prompt-injection instructions and persists a safe digest-based audit.
- **Seed/evaluation outcome:** rerunnable owned fixtures now cover six companies,
  two mandates, 18 documents, 18 deduplicated news rows, positive/negative
  triggers, six contacts, 12 interactions, high/medium/low cases, empty RAG and
  prompt-injection content. The deterministic evaluation reports Recall@K and
  MRR `1.000`, zero cross-company/forbidden leakage and one empty case.

### Milestone 2 checkpoint command record

Counts are pytest cases where reported; other rows count commands or explicit
assertions. Required skip count is zero.

| Command | Result | Pass / fail / skip | Notes |
|---|---|---:|---|
| `cd apps/api && .venv/bin/python -m pytest tests/unit/test_config.py tests/unit/test_content_identity.py tests/unit/test_embedding_health.py tests/unit/test_retrieval_logging.py tests/unit/test_semantic_configuration_files.py tests/unit/services/embeddings tests/unit/services/test_document_indexing.py tests/unit/services/test_retrieval_evaluation.py tests/unit/rag -q` | Pass | 42 / 0 / 0 | Provider registry, identity, safety, context, config and evaluation units |
| `cd apps/api && .venv/bin/python -m pytest tests/integration/db/test_migrations.py tests/integration/vector tests/integration/rag tests/integration/seed tests/integration/api/test_core_routes.py tests/integration/services/test_transaction_safety.py tests/integration/test_health.py -q` | Pass | 26 / 0 / 0 | All affected database/API/service boundaries |
| `cd apps/api && .venv/bin/python -m compileall -q app scripts alembic tests` | Pass | 1 / 0 / 0 | Backend, migrations, scripts and tests compile |
| `cd apps/api && .venv/bin/python -m pytest -q` | Pass | 73 / 0 / 0 | Complete backend regression |
| `cd apps/api && .venv/bin/python -m pytest --cov=app --cov-report=term-missing` | Pass | 73 / 0 / 0 | 89% line coverage |
| `cd apps/api && .venv/bin/python -m pytest -q tests/integration/db/test_migrations.py tests/unit/test_retrieval_logging.py` | Pass | 8 / 0 / 0 | Migration logging no longer disables application loggers |
| Safe-test assertion, cohort export/prune, `alembic downgrade 0002_milestone1_core`, `upgrade head`, `check` | Pass | 6 / 0 / 0 | Exported exactly 19 semantic rows; retained hashing; no schema drift |
| `make lint`; `cd apps/web && pnpm exec tsc --noEmit`; `make build` | Pass | 3 / 0 / 0 | ESLint clean, TypeScript clean, 12/12 Next.js routes generated |
| `.venv/bin/python -m pip check` and exact package-version assertions | Pass | 4 / 0 / 0 | sentence-transformers 5.6.0, transformers 5.13.0, torch 2.13.0 |
| Host offline `scripts.semantic_probe --no-write-report` | Pass | 2 / 0 / 0 | Repeated before and after downgrade; pinned 384-dimension revision loaded locally |
| Semantic Compose `config --quiet`; API/Web image build and health | Pass | 6 / 0 / 0 | Disposable project/ports only; default project remained unchanged |
| Container offline flags, read-only cache, real MiniLM probe and missing-cache fallback | Pass | 4 / 0 / 0 | Offline/local-only semantic metrics passed; fallback reported `model_unavailable -> hashing` |
| Base and semantic HTTP contract chain | Pass | 8 / 0 / 0 | health, readiness, integration health, hashing vector, semantic company RAG, 422 scope guard and Web `/rag` |
| Disposable Compose teardown and temporary-file cleanup | Pass | 2 / 0 / 0 | Removed only `pe-agent-m2-check` containers/network/volume and generated `/private/tmp` JSON |
| `git diff --check`, deletion, secret, dead-code and unrelated-change review | Pass | 5 / 0 / 0 | No whitespace error, tracked deletion, secret, model/cache, `.env` or unrelated file |

Checkpoint failures were not waived:

- the first full regression ended 72 passed / 1 failed because Alembic logging
  disabled the retrieval logger; `disable_existing_loggers=False` and logging
  handler isolation fixed the root cause, then 73/73 passed twice including
  coverage;
- localhost integration checks blocked by the sandbox were rerun with the
  approved local-PostgreSQL permission and passed;
- early Docker probes exposed direct-script import paths and disabled autoflush
  assumptions; both were fixed and the container semantic/fallback gates reran;
- the first HTTP assertion assumed seed company ID `1`; inspection proved both
  cohorts healthy but the stable seed domain mapped to ID `7`. The gate now
  resolves the ID from `asteria.example` and passed from scratch;
- the next HTTP chain used zsh's read-only `status` variable after all retrieval
  assertions passed. It was renamed `http_status`, and the entire chain reran
  with exit 0.

### Milestone 2 remaining limitations

- The semantic image is substantially larger than the hashing-only runtime
  because PyTorch and sentence-transformers are installed; semantic use remains
  an explicit Compose override with an external read-only cache.
- The installed Transformers version emits a non-failing deprecation warning
  for `cache_dir` during the intentional missing-cache fallback probe.
- CI configuration exists but this local checkpoint did not execute GitHub
  Actions. There is still no frontend browser/component test framework; the
  required M2 frontend lint, type, production build and live HTTP route checks
  all passed.
- Authentication, MCP, LangGraph, news crawling, send-state enforcement and
  the remaining product UI are later milestones and were not claimed here.
- Milestone 3 subsequently completed under the evidence below.

## Milestone 3 work log

- **Started and completed:** 2026-07-14 (Europe/Paris).
- **Scope:** Modules 7 and 8 only; Milestone 4 implementation was not part of
  this checkpoint.
- **Default mode:** fully offline, checked-in `demo_mock` source, deterministic
  rules and manual API/CLI actions. No scheduler, worker or background loop.
- **Network mode:** RSS/Atom and configured static-page adapters exist only for
  server-owned HTTPS sources whose exact host is globally allowlisted. Requests
  cannot submit URLs, hosts, selectors, headers or fixture paths.
- **Safety:** every request/redirect is checked for scheme, credentials, port,
  exact host and globally routable DNS answers; MIME, streamed size, timeout,
  retry and per-host interval are bounded. XML is defused and HTML is sanitized.
- **Trigger outcome:** seven positive and seven negative canonical categories,
  exact evidence sentences, event dates, deterministic identity, same-article
  dedupe and conservative cross-article merge. Optional LLM output is local-
  schema validated and falls back to rules; the API, sync orchestrator and CLI
  share one settings-backed provider factory, and no real provider is required.
- **Database outcome:** `0004_milestone3_news_triggers` adds the article
  extraction lifecycle, backfills legacy trigger identities, constrains status/
  method/confidence and adds canonical URL and article/type uniqueness.
- **API/CLI outcome:** `POST /api/news-articles/sync` and
  `POST /api/triggers/extract` share the same services as the guarded CLI tools.
  Source and article transactions include safe ID/count-only audit records.

### Milestone 3 checkpoint command record

Required skip count is zero. Pytest rows use test-case counts; other rows count
commands or explicit assertions.

| Command | Result | Pass / fail / skip | Notes |
|---|---|---:|---|
| `cd apps/api && .venv/bin/python -m pytest tests/unit/news tests/unit/triggers tests/unit/test_config.py tests/unit/test_core_schemas.py -q` | Pass | 90 / 0 / 0 | Source config, SSRF/HTTP, parsers, matching, settings-backed hybrid LLM fallback and reports |
| `cd apps/api && .venv/bin/python -m pytest tests/integration/db/test_migrations.py tests/integration/news tests/integration/triggers tests/integration/seed tests/integration/api/test_core_routes.py tests/integration/test_health.py -q` | Pass | 26 / 0 / 0 | Migration, sync, extraction, API/CLI, audit and seed boundaries |
| `cd apps/api && .venv/bin/python -m compileall -q app scripts alembic tests` | Pass | 1 / 0 / 0 | Backend, scripts, migrations and tests compile |
| `cd apps/api && .venv/bin/python -m pytest -q` | Pass | 154 / 0 / 0 | Complete backend regression; final run was the coverage-instrumented equivalent below |
| `cd apps/api && .venv/bin/python -m pytest --cov=app --cov-report=term-missing -q` | Pass | 154 / 0 / 0 | 89% total line coverage |
| `cd apps/api && .venv/bin/python -m pip check` | Pass | 1 / 0 / 0 | No broken requirements; HTTPX 0.28.1, Beautiful Soup 4.15.0 and defusedxml 0.7.1 pinned |
| Guarded test DB `alembic downgrade 0003_milestone2_vector_cohorts`; `upgrade head`; `check` | Pass | 3 / 0 / 0 | Data-safe downgrade/re-upgrade; no new operations detected |
| `make lint`; `cd apps/web && pnpm exec tsc --noEmit`; `pnpm build` | Pass | 3 / 0 / 0 | ESLint and TypeScript clean; 12/12 routes generated |
| `docker compose config --quiet`; isolated API/Web build and health | Pass | 5 / 0 / 0 | Project `pe-agent-m3-check`, isolated DB names, ports and volume |
| Isolated health/readiness/integration-health and Web news/trigger probes | Pass | 5 / 0 / 0 | All returned HTTP 200 |
| First/repeated mock sync | Pass | 2 / 0 / 0 | First: 3 created/2 triggers; repeat: 3 duplicates/0 new triggers |
| First/repeated standalone extraction | Pass | 2 / 0 / 0 | First: 18 selected/18 succeeded; repeat: 0 selected |
| Unknown source and request-supplied URL rejection | Pass | 2 / 0 / 0 | Both returned HTTP 422 |
| Isolated database/audit query | Pass | 4 / 0 / 0 | 21 news, 9 triggers, 4 negative triggers, 20 M3 audit rows |
| Disposable teardown and default Compose comparison | Pass | 2 / 0 / 0 | Removed only M3 project/volume; original PostgreSQL remained healthy |
| `git diff --check`, status/name/stat/deletion and secret/dead-code/scope review | Pass | 6 / 0 / 0 | No whitespace error or tracked deletion; final cached review recorded at commit gate |

Checkpoint failures were diagnosed and rerun rather than waived:

- one migration regression expected the old M2 head; it was updated to the new
  additive head and the 26-test affected integration suite passed;
- the first complete collection found two identically named transaction test
  modules; the M3 file was renamed and the complete suite passed;
- repeated sync exposed singular `duplicate` versus report `duplicates`; the
  counter mapping and post-savepoint accounting were fixed, then idempotency
  passed;
- coverage and Turbopack initially failed only because the sandbox denied local
  PostgreSQL/internal-port access; the identical authorized commands passed;
- the first container seed attempts proved the database-identity guard and
  container seed path were effective but incomplete. A distinct guard identity
  and explicit `/data/seed` path passed; Compose now sets `SEED_DATA_DIR`.
- the first cached `git diff --check` found trailing blank lines in 26 new
  Python files; the endings were normalized, files were restaged and the full
  cached whitespace/deletion/secret/dead-code/scope review passed.

### Milestone 3 remaining limitations

- RSS/public-page production sources and the optional LLM require explicit
  server configuration; automated tests use local mock transports only.
- There is no scheduler or background worker. Sync and extraction are manual
  API/CLI actions, and dedicated sync UI belongs to Milestone 7.
- Negative triggers are now reliable downstream inputs, but risk weights and
  recommendation effects remain Milestone 6 scope.
- CI exists but GitHub Actions was not executed in this local checkpoint.
- MCP and LangGraph are not part of the verified public M3 runtime. Local M4
  work remains checkpoint-incomplete and excluded from this snapshot.

## Public repository preparation work log

- **Started:** 2026-07-16 (Europe/London).
- **Publication target:** the last checkpoint-verified M3 tree only.
- **Local work preservation:** unfinished M4 tracked/untracked content is
  archived and hashed outside the repository before history preparation; it is
  not part of the public commit.
- **Ignore audit:** tracked macOS/editor metadata and an unignored `output/`
  directory were identified. `output/` contains role-specific CV artifacts and
  is excluded from publication.
- **Source audit:** a broad Python-template `lib/` ignore rule hid the required
  frontend `apps/web/src/lib/api.ts`, `utils.ts` and `mock-data.ts`. The public
  snapshot explicitly tracks those M3 source files.
- **Credential audit:** unpublished local history contained a real local
  PostgreSQL password in Alembic configuration. The public tree uses a
  non-secret placeholder, and all unpublished descendants are replaced by one
  sanitized snapshot commit before push.
- **History policy:** the existing `origin/main` remains unchanged and becomes
  the parent of the sanitized snapshot; no force-push is required.
- **History outcome:** `origin/main..HEAD` contains exactly one sanitized M3
  snapshot commit whose parent is the unchanged public `origin/main`; a normal
  push is sufficient and no force-push is required.
- **Clean-snapshot gate:** the first complete gate ran from a detached worktree
  at the exact snapshot commit, without reading the developer `.env`. Required
  skip count is zero.

| Command or check | Result | Pass / fail / skip | Notes |
|---|---|---:|---|
| Tracked-path assertions and `git rev-list --count origin/main..HEAD` | Pass | 5 / 0 / 0 | Three required frontend `src/lib` files tracked; no M4, metadata, `output/` or real environment files; exactly one public commit |
| Full commit/tree credential, owner-path, private-key and large-blob scan | Pass | 5 / 0 / 0 | 347 reachable objects and 293 tracked files inspected; no publish-blocking hit and no blob at or above 5 MiB |
| README local-link validation | Pass | 1 / 0 / 0 | All repository-local links in the public landing pages resolve |
| `cd apps/api && .venv/bin/python -m compileall -q app main.py alembic tests` | Pass | 1 / 0 / 0 | Exact clean snapshot compiled |
| `cd apps/api && .venv/bin/python -m pytest --cov=app --cov-report=term-missing -q` | Pass | 154 / 0 / 0 | Complete backend regression; 89% total line coverage (3945 statements, 420 missed) |
| Isolated `alembic upgrade head`; `downgrade 0003_milestone2_vector_cohorts`; `upgrade head`; `alembic check` | Pass | 4 / 0 / 0 | Dedicated publication databases only; final head `0004_milestone3_news_triggers`; no new operations detected |
| `make lint`; `cd apps/web && pnpm exec tsc --noEmit`; `pnpm build` | Pass | 3 / 0 / 0 | ESLint and TypeScript clean; production build generated 12/12 routes |
| `docker compose --env-file /dev/null config --quiet` | Pass | 1 / 0 / 0 | Compose rendered using documented defaults without loading a real `.env` |
| `git diff --check` | Pass | 1 / 0 / 0 | No whitespace errors |

Two validation-environment failures were diagnosed rather than waived. The
first build rejected a dependency symlink outside the detached worktree; a
local physical dependency copy removed that condition. The next sandboxed
build was denied permission to bind Turbopack's internal temporary port; the
identical authorized build outside that sandbox passed. Neither failure was a
source-code or test failure. The complete gate is rerun after the evidence-only
amend so the final commit, rather than its predecessor, is the validated object.
