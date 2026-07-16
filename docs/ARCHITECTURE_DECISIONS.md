# Architecture Decisions

This log freezes decisions made during Milestone 0. Later milestones may amend
them only with a new dated decision and corresponding compatibility tests.

## ADR-0001 — Preserve and evolve the current layered application

- **Status:** Accepted
- **Date:** 2026-07-13
- **Decision:** Keep the existing FastAPI route → service → repository →
  SQLAlchemy model layering and the existing Next.js API client. Add new
  capabilities incrementally instead of replacing the application wholesale.
- **Reason:** Existing companies, dashboard, CRM, documents, RAG, agent-run and
  draft flows are already connected end to end. A rewrite would create route,
  response-shape and data-loss risk without improving the Milestone 0 baseline.
- **Consequence:** Existing endpoints and response fields are compatibility
  contracts until tests and an explicit migration plan permit a change.

## ADR-0002 — Treat the current database as a compatibility baseline

- **Status:** Implemented and verified in Milestone 1
- **Date:** 2026-07-13
- **Decision:** Introduce Alembic with two stages: a baseline revision that can
  create the current schema on a clean database, followed by additive feature
  revisions. An existing compatible database must be schema-verified before it
  is stamped at the baseline revision; it must never be dropped or recreated.
- **Reason:** The developer database contains 12 application tables and live
  demo records but has no migration history. A naive initial migration would
  attempt to recreate existing tables.
- **Verification required:** (1) upgrade a clean test database from zero,
  (2) restore a schema/data copy of the current database, verify it, stamp the
  baseline, then upgrade, and (3) exercise downgrade/upgrade paths on test data.

## ADR-0003 — Separate test data from developer data before integration tests

- **Status:** Implemented and verified in Milestone 1
- **Date:** 2026-07-13
- **Decision:** Add a dedicated test database configuration and fail closed if
  integration tests resolve to the developer database name or URL.
- **Reason:** The current settings have one default `DATABASE_URL`, and the
  running Compose database already contains demo data. Tests and migration
  validation must not mutate it.

## ADR-0004 — Keep deterministic local providers as the default path

- **Status:** Accepted
- **Date:** 2026-07-13
- **Decision:** Preserve the hashing embedding service and template email
  generator as deterministic fallbacks. Semantic embeddings, remote LLMs and
  MCP transport are opt-in adapters with explicit health/fallback reporting.
- **Reason:** Local startup and automated tests must require no network, paid
  API or enterprise credential.

## ADR-0005 — LangGraph orchestrates services; it does not absorb business logic

- **Status:** Accepted for planning; implementation belongs to Milestone 5
- **Date:** 2026-07-13
- **Decision:** Wrap/replace the synchronous `OriginationWorkflow` with typed
  LangGraph state and small nodes that call the existing/new services.
- **Reason:** Scoring, retrieval, drafting and approval logic must stay directly
  testable and reusable outside a graph runtime.

## ADR-0006 — Backend approval state is the sending authority

- **Status:** Accepted for planning; implementation belongs to Milestone 6
- **Date:** 2026-07-13
- **Decision:** Only a backend service may transition a current draft from
  `approved` to mock sending/sent states. Frontend controls and graph routing
  are not security boundaries.
- **Compatibility note:** Current values include `revision_requested` and
  `sent_simulated`; the authoritative target vocabulary uses
  `changes_requested`, `sending`, `sent` and `send_failed`. A migration and API
  compatibility layer must be designed before values are renamed.

## ADR-0007 — Production builds must not depend on build-time internet access

- **Status:** Accepted
- **Date:** 2026-07-13
- **Decision:** Use a local or system font stack unless font assets are checked
  into the repository. Do not use `next/font/google` in the offline default
  build path.
- **Reason:** The initial production build failed only because it attempted to
  fetch Geist CSS from Google Fonts. The product requires no-network checks.

## ADR-0008 — Separate implementation authority from public README content

- **Status:** Accepted
- **Date:** 2026-07-13
- **Decision:** Use the seven-level precedence defined in `AGENTS.md` and
  `docs/FINAL_IMPLEMENTATION_PLAN.md`. `README_ZH.md` remains the detailed
  Chinese product overview and `README.md` becomes the concise English public
  landing page. Both are lower-authority public documentation and neither is a
  substitute for the detailed implementation plan or status evidence.
- **Conflict rule:** If either README conflicts with a higher-authority source,
  report the conflict, confirm the implementation decision, then synchronize
  the README. Never silently implement from the README.
- **Reason:** A prior thread annotation said to use the Chinese README rather
  than the English README. That instruction was incorrectly generalized into
  misclassifying a presentation preference as implementation authority. The
  intended meaning was presentation priority, not requirements precedence.

## ADR-0009 — Fail closed, then repair the known legacy `create_all()` state

- **Status:** Accepted and implemented
- **Date:** 2026-07-13
- **Decision:** The migration bootstrap accepts only four verified states:
  empty, compatible baseline, compatible Milestone 1, or the exact legacy
  partial state where `create_all()` created all four new M1 tables but could
  not alter baseline tables. It rejects every other partial schema. The known
  partial state is stamped at baseline and upgraded additively; revision 0002
  skips already compatible new tables and adds the missing baseline columns,
  constraints and indexes.
- **Reason:** The live developer database contained demo data plus the exact
  non-destructive artifact produced by the former import-time `create_all()`.
  Dropping/recreating tables or blindly stamping head would either lose data or
  leave missing columns.
- **Verification:** Migration tests cover clean upgrade, existing baseline data,
  unversioned full M1, legacy partial repair, downgrade/re-upgrade and Alembic
  metadata drift. The live database reached `0002_milestone1_core` with all four
  existing companies preserved.

## ADR-0010 — Keep schema lifecycle outside application import

- **Status:** Accepted and implemented
- **Date:** 2026-07-13
- **Decision:** FastAPI app creation performs no extension or table DDL. Local,
  container and CI schema lifecycle is owned by the guarded migration bootstrap.
- **Reason:** Import-time DDL made tests unsafe, created partial schemas and
  coupled process startup to database ownership. Explicit migrations make the
  lifecycle observable and reversible.

## ADR-0011 — Isolate embedding cohorts by complete model identity

- **Status:** Accepted and implemented
- **Date:** 2026-07-14
- **Decision:** A document chunk is unique within its provider, model, immutable
  model revision and dimension cohort. Search always filters by the complete
  identity. Hashing and MiniLM rows may coexist; neither provider reuses or
  silently interprets the other's vectors. Revision 0003 adds compatible
  identity constraints and cohort-specific HNSW indexes.
- **Lifecycle rule:** Downgrade refuses a populated multi-cohort table. The
  operator must first use the safe-test-only export/prune command, name the
  single cohort to retain and inspect the exported metadata.
- **Reason:** Filtering only by a display model name can mix incompatible vector
  spaces and make ranking silently wrong. Explicit cohort lifecycle also avoids
  destructive migration assumptions.

## ADR-0012 — Keep semantic embeddings optional, offline and external

- **Status:** Accepted and implemented
- **Date:** 2026-07-14
- **Decision:** Deterministic hashing remains the default runtime provider. The
  optional semantic provider is pinned to
  `sentence-transformers/all-MiniLM-L6-v2` revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, dimension 384, and loads only
  from a configured external cache. Docker mounts that cache read-only and uses
  Hugging Face/Transformers offline flags.
- **Fallback rule:** An implicit semantic request may report and use hashing if
  the local model is unavailable. An explicit semantic identity request fails
  instead of silently changing models. Responses and health output expose the
  requested/effective identity and fallback reason.
- **Reason:** The default project must remain no-network and lightweight while
  still supporting reproducible real semantic retrieval when the owner opts in.

## ADR-0013 — Require company scope for RAG, not for explicit vector debugging

- **Status:** Accepted and implemented
- **Date:** 2026-07-14
- **Decision:** `/api/rag/retrieve` requires `company_id`; the RAG UI has no
  all-company option. `/api/vector/search` retains nullable company scope for
  explicit index/debug inspection. RAG query construction may use the selected
  company, mandate and recent triggers, but final sources must remain inside the
  selected company.
- **Safety rule:** Retrieved passages are untrusted data. Injection-like
  instruction lines are removed, context is bounded and source-diverse, empty
  retrieval returns a safe empty result, and every success/empty/fallback is
  audited with digests and identifiers rather than unnecessary raw query text.
- **Reason:** Cross-company RAG can contaminate investment context, while a
  separately named debug endpoint still needs an operator-visible global mode.

## ADR-0014 — Own deterministic demo fixtures by stable natural keys

- **Status:** Accepted and implemented
- **Date:** 2026-07-14
- **Decision:** M2 fixtures use explicit seed ownership and stable natural keys,
  refuse collisions with unowned rows, and update owned rows idempotently. Test
  and HTTP automation resolves fixtures by natural key/domain rather than
  assuming database-generated primary keys.
- **Reason:** Primary keys are not stable across isolated schema/database
  rebuilds. Natural-key lookup preserves repeatability without deleting or
  overwriting developer-owned data.

## ADR-0015 — Keep news synchronization offline-first and server-controlled

- **Status:** Accepted and implemented
- **Date:** 2026-07-14
- **Decision:** News sources are selected only by `source_id` from the
  server-owned registry. The checked-in default enables a local mock fixture;
  RSS and public-page adapters remain disabled until an operator configures an
  exact HTTPS hostname allowlist. Requests cannot supply arbitrary URLs.
- **Safety rule:** Fetching enforces DNS/IP validation, redirect revalidation,
  MIME and response-size bounds, timeouts, retries and per-host pacing. XML is
  parsed with hardened libraries, HTML is treated as untrusted data, and tests
  use local transports rather than the public internet.
- **Operation rule:** M3 provides explicit API and CLI sync actions only. It
  does not add a scheduler or background daemon.
- **Reason:** A server-controlled, opt-in network boundary prevents the API
  from becoming an SSRF proxy and keeps local development and CI deterministic.

## ADR-0016 — Separate source transactions and article extraction lifecycle

- **Status:** Accepted and implemented
- **Date:** 2026-07-14
- **Decision:** Each configured source owns one top-level transaction, while
  individual articles use savepoints so one malformed item does not corrupt
  accepted siblings. Canonical URL/content hashes make ingestion idempotent.
  Revision 0004 records `pending`, `processed`, `no_trigger` and `failed`
  lifecycle state plus extraction version and timestamp, allowing a new
  version to reprocess rows without confusing “no event” with “not run.”
- **Audit rule:** Reports and audit rows store bounded counts, source/article/
  trigger identifiers and safe error categories; they do not persist response
  bodies, credentials or raw exception text.
- **Reason:** Explicit ownership makes rollback and retry behavior observable,
  while lifecycle versioning preserves deterministic batch semantics.

## ADR-0017 — Use canonical rule triggers with an optional validated LLM supplement

- **Status:** Accepted and implemented
- **Date:** 2026-07-14
- **Decision:** Deterministic rules are the default and emit only the 14
  canonical trigger categories. Negative status is derived by category, not
  accepted from external model output. Optional `hybrid` mode invokes an
  allowlisted LLM only when rules find no candidate, validates the structured
  response and requires evidence to occur in the article text.
- **Fallback rule:** Missing configuration, invalid endpoints, timeouts,
  provider failures and invalid output produce safe fallback codes; they do not
  fail ingestion or silently invent triggers. Duplicate article/type and
  near-duplicate company/event evidence are merged with bounded references.
- **Scope rule:** M3 detects and persists trigger evidence. Applying negative
  triggers to scoring and action recommendations remains Milestone 6 scope.
- **Reason:** This preserves an explainable offline path while making optional
  model assistance constrained, observable and non-authoritative.

## Compatibility and delivery risks frozen at baseline

| Risk | Evidence | Required control |
|---|---|---|
| Unversioned schema | No `alembic.ini`, migration directory or revision table | Baseline/stamp strategy and clean/existing DB tests |
| Import-time DDL | `apps/api/main.py` calls vector extension setup and `create_all()` at import | Move schema lifecycle out of app import after Alembic lands |
| Developer/test DB collision | One default URL in `apps/api/app/core/config.py` | Explicit environment and destructive-operation guard |
| Unpinned Python stack | Eight unconstrained lines in `apps/api/requirements.txt` | Pin/constrain versions after compatibility capture |
| Missing automated tests | No project test files; `pytest` absent from the venv | Add isolated unit/integration suites before feature work |
| Status vocabulary drift | Schema/service values differ from the target state machine | Add enum/transition compatibility tests and data migration |
| Weak API validation | Several request/path/query fields are unconstrained strings/ints | Add strict schemas without breaking response envelopes |
| Database portability limits | PostgreSQL `JSONB` and pgvector are used directly | Keep PostgreSQL as integration-test target; use pure unit tests elsewhere |
| Vector model mixing | Model string is filtered, but dimension/version lifecycle is manual | Provider registry, dimension checks and explicit reindexing |
| Missing vector ANN index | Only btree indexes exist on `document_chunks` | Add a safe pgvector HNSW migration after data/model validation |
| Raw/sensitive audit risk | Broad JSON snapshots and raw exception text are persisted | Central redaction and safe error metadata |
| N+1 agent-run listing | Each run performs separate company/score/draft queries | Preserve API shape while adding joined/batched repository access |
| Frontend/backend type duplication | `apps/web/src/lib/api.ts` manually mirrors Pydantic models | Contract tests or generated types after APIs stabilize |
| Planned/current ambiguity | Public READMEs can describe both the product and roadmap | Label verified/current versus planned behavior and defer implementation decisions to higher-authority documents |
| Seed coverage gap | Four companies/news/documents; no mandates/negative cases | Rerunnable 6–8 company scenario matrix in Milestone 2 |
| Approval bypass | Generic draft patch accepts status changes directly | Central transition service and explicit mock-send gate |
