# Milestone 2 Semantic Vector and Safe RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver Modules 4, 5 and 11 with isolated hashing/MiniLM embeddings, company-scoped safe RAG, deterministic demo seeds and honest retrieval evaluation, then pass the complete Milestone 2 checkpoint.

**Architecture:** Keep hashing as the tracked default and introduce a lazy typed provider registry with explicit semantic opt-in. Store multiple 384-dimensional model cohorts in `document_chunks`, filter on complete model and source identities, and use company-scoped RAG services for query construction, safety, context limits, citations and audit. Default automation uses deterministic fake providers; separately gated host and Docker probes use a pinned local MiniLM snapshot.

**Tech Stack:** Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL 16, pgvector, sentence-transformers 5.6.0, transformers 5.13.0, PyTorch 2.13.0, pytest, Next.js 16.2.10, TypeScript, Docker Compose.

---

## Execution rules

- Work directly on `main` because the repository owner explicitly authorized
  that workflow for this repository.
- Preserve all existing uncommitted Milestones 0 and 1 work.
- The owner's milestone policy overrides the generic frequent-commit guidance:
  do not commit M2 implementation code until the full M2 checkpoint passes.
- The already-approved design and this plan may remain separate documentation
  commits. Consolidate and commit M0/M1 first because its checkpoint has already
  passed and M2 needs a reproducible base.
- Never modify the real `.env`; pass the model cache through the process
  environment. Never reset the developer database. All destructive checks use
  a database whose name contains `test` and whose host/port/name identity differs
  from `DATABASE_URL`.
- Default automated tests must not download or load MiniLM. Real-model host and
  Docker probes are separate milestone gates and run offline after download.
- Stop after any repeated failing verification, diagnose it, fix it and rerun
  before continuing.

## Pinned semantic artifacts

- `sentence-transformers==5.6.0`
- `transformers==5.13.0`
- `torch==2.13.0`
- model: `sentence-transformers/all-MiniLM-L6-v2`
- model revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
- host cache: owner-supplied `${HF_MODEL_CACHE_DIR}` outside the repository
- embedding dimension: `384`
- deterministic runtime device: CPU

## File map

### New backend files

- `apps/api/app/core/content_identity.py`: canonical content hashes and legacy
  file-version sentinel.
- `apps/api/app/services/embeddings/base.py`: provider protocol, identity and
  validation helpers.
- `apps/api/app/services/embeddings/hashing.py`: deterministic hashing provider.
- `apps/api/app/services/embeddings/sentence_transformer.py`: lazy local-only
  MiniLM provider.
- `apps/api/app/services/embeddings/registry.py`: allowlisted provider resolution
  and explicit fallback metadata.
- `apps/api/app/services/rag_query_service.py`: company/mandate/trigger query
  construction.
- `apps/api/app/services/rag_context_service.py`: diversity, citation and context
  budgeting.
- `apps/api/app/services/rag_safety_service.py`: untrusted-content isolation and
  warnings.
- `apps/api/app/services/demo_seed_service.py`: session-injected rerunnable seed
  orchestration.
- `apps/api/app/services/retrieval_evaluation_service.py`: Recall@K/MRR/leakage
  evaluation.
- `apps/api/alembic/versions/0003_milestone2_vector_cohorts.py`: additive cohort,
  source-identity and partial-HNSW migration.
- `apps/api/scripts/download_embedding_model.py`: the only network-enabled model
  fetch command.
- `apps/api/scripts/evaluate_retrieval.py`: isolated-database evaluation report.
- `apps/api/scripts/semantic_probe.py`: real-model host/container checkpoint.
- `apps/api/scripts/prune_embedding_cohorts.py`: explicit export/prune prerequisite
  for an operator-approved multi-cohort downgrade.
- `apps/api/requirements-semantic.txt`: pinned optional semantic stack.
- `docker-compose.semantic.yml`: explicit read-only semantic cache override.
- focused tests under `apps/api/tests/unit/services/embeddings/`,
  `apps/api/tests/unit/rag/`, `apps/api/tests/integration/vector/`,
  `apps/api/tests/integration/rag/` and `apps/api/tests/integration/seed/`.
- deterministic fixture `apps/api/tests/fixtures/retrieval_evaluation.json`.
- seed files `data/seed/mandates.json`, `triggers.json`, `approvals.json` and
  `feedback.json`.
- `docs/RETRIEVAL_EVALUATION.md`: generated and reviewed quality evidence.

### Modified files

- `apps/api/app/core/migrations.py` and schema compatibility tests so an
  unversioned M1 database is stamped at `0002`, then truly upgraded through
  `0003` rather than stamped past it.
- `apps/api/app/api/routes_health.py`, `routes_integrations.py`,
  `apps/api/app/schemas/integration.py` and `apps/api/app/core/logging.py` for
  redacted semantic health and requested/effective identity events.
- settings, model, repository, schema, service and route files for document
  chunks, vector search and RAG.
- `apps/api/scripts/index_documents.py` and `seed_data.py` to remove `create_all()`
  and delegate to safe services.
- all existing `data/seed/*.json` files for the six-company scenario matrix.
- `apps/web/src/lib/api.ts`, `apps/web/src/app/rag/page.tsx` and
  `apps/web/src/components/company-rag-section.tsx` for the additive contract and
  mandatory company scope.
- `apps/api/Dockerfile`, `docker-compose.yml`, `Makefile`, `.env.example` and CI
  for deterministic defaults and explicit semantic probes.
- `apps/api/tests/unit/test_semantic_configuration_files.py` and focused health/
  logging tests for base/semantic Compose configuration and safe observability.
- `AGENTS.md`, architecture/status/plan documents and both public READMEs after
  behavior is verified.

### Preserved interfaces

- `EmbeddingService.embed_text()` and `model_name` remain compatibility shims.
- `/api/vector/search` retains `query`, nullable `company_id`, `top_k` and every
  existing response/result field.
- `/api/rag/retrieve` keeps its route and existing response fields but now uses a
  dedicated request with required `company_id`; new status/model/warning fields
  are additive.

---

### Task 0: Consolidate the verified Milestone 1 base

**Files:** All currently modified/untracked M0/M1 files except ignored local
environment files and already committed M2 design documents.

- [ ] **Step 1: Reconfirm the existing M1 worktree is the recorded checkpoint**

Run:

```bash
git status --short --branch
git diff --check
make test
make lint
cd apps/web && pnpm exec tsc --noEmit
cd ../.. && make build
```

Expected: 24 backend tests pass, lint/type/build pass, and no whitespace errors.
If counts differ because only documentation commits changed, diagnose before
staging.

- [ ] **Step 2: Inspect the complete M0/M1 diff**

Run `git diff --stat`, `git diff --name-status`, a changed-line secret scan and
review every untracked path. Confirm `.env`, model files, caches and credentials
are absent.

- [ ] **Step 3: Stage only the verified M0/M1 base**

Stage the explicit repository paths already documented in
`docs/IMPLEMENTATION_STATUS.md`; use `git diff --cached --name-status` and
`git diff --cached --check` to verify scope.

- [ ] **Step 4: Commit the already-passed M1 milestone**

```bash
git commit -m "feat: complete milestone 1 foundations"
```

Expected: one coherent M0/M1 base commit; no M2 implementation files included.

---

### Task 1: Freeze settings, optional dependencies and model download policy

**Files:**

- Create: `apps/api/requirements-semantic.txt`
- Create: `apps/api/scripts/download_embedding_model.py`
- Create: `apps/api/tests/unit/services/embeddings/test_download_model.py`
- Modify: `apps/api/app/core/config.py`
- Modify: `apps/api/tests/unit/test_config.py`
- Modify: `apps/api/requirements-dev.txt`
- Modify: `.env.example`
- Modify: `Makefile`
- Modify: `AGENTS.md`
- Modify: `docs/IMPLEMENTATION_STATUS.md`

- [ ] **Step 1: Write failing settings tests**

Cover default hashing, explicit semantic opt-in, pinned model/revision,
384-dimensional validation, positive batch/context bounds and a cache path that
is optional for hashing but required by the explicit download/probe command.

Representative assertions:

```python
assert Settings(_env_file=None).embedding_provider == "hashing"
assert Settings(_env_file=None).embedding_dimension == 384
assert Settings(_env_file=None).embedding_model_revision == (
    "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
)
```

- [ ] **Step 2: Run the focused test and verify failure**

Run `cd apps/api && .venv/bin/python -m pytest tests/unit/test_config.py -q`.
Expected: failure for missing embedding settings.

- [ ] **Step 3: Add minimal validated settings and exact requirements**

Use `Literal["hashing", "sentence_transformer"]`, keep hashing as tracked
default, and add bounded `embedding_batch_size`, `vector_min_similarity`,
`vector_max_top_k` and `rag_max_context_words` settings. Add configurable seed
and evaluation-fixture paths with repository defaults and container override
support. Put the three exact semantic pins in `requirements-semantic.txt`;
include that file from dev requirements but keep runtime imports lazy.

- [ ] **Step 4: Write and run the failing downloader tests**

Run `cd apps/api && .venv/bin/python -m pytest tests/unit/services/embeddings/test_download_model.py -q`.
Expected: collection/import failure because the downloader does not exist.

- [ ] **Step 5: Implement the explicit downloader**

The script requires `--cache-dir`, uses the pinned repository/revision, permits
network only in this command, initializes a CPU `SentenceTransformer`, verifies
one 384-dimensional vector and prints identity/target without printing secrets.
Mock the model class in default automation.

- [ ] **Step 6: Document commands without editing `.env`**

Add `HF_MODEL_CACHE_DIR` and semantic settings to `.env.example`; add
`semantic-install` and `semantic-download` Make targets that require an explicit
environment variable. Record M2 as started and add the owner's direct-`main`
workflow rule to `AGENTS.md`.

- [ ] **Step 7: Run focused config/downloader tests**

Expected: all focused tests pass without network and without importing Torch.

---

### Task 2: Add typed providers and deterministic fallback resolution

**Files:**

- Create: `apps/api/app/services/embeddings/__init__.py`
- Create: `apps/api/app/services/embeddings/base.py`
- Create: `apps/api/app/services/embeddings/hashing.py`
- Create: `apps/api/app/services/embeddings/sentence_transformer.py`
- Create: `apps/api/app/services/embeddings/registry.py`
- Create: `apps/api/tests/unit/services/embeddings/test_providers.py`
- Create: `apps/api/tests/unit/services/embeddings/test_registry.py`
- Modify: `apps/api/app/services/embedding_service.py`
- Modify: `apps/api/app/api/routes_health.py`
- Modify: `apps/api/app/schemas/integration.py`
- Create: `apps/api/tests/unit/test_embedding_health.py`

- [ ] **Step 1: Write failing contract tests**

Test normalized single/batch output, exact identity, empty batches, wrong row
counts, wrong dimensions, non-finite values, lazy semantic import, local-only
loading, explicit-selection failure and configured-primary fallback metadata.

- [ ] **Step 2: Run tests and verify provider modules are missing**

Run `cd apps/api && .venv/bin/python -m pytest tests/unit/services/embeddings -q`.

- [ ] **Step 3: Implement the provider boundary**

Core shape:

```python
@dataclass(frozen=True)
class EmbeddingIdentity:
    provider: str
    model: str
    version: str
    dimension: int

class EmbeddingProvider(Protocol):
    identity: EmbeddingIdentity
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...
```

Central validation returns plain `list[float]` values and rejects incompatible
batches before any repository write.

- [ ] **Step 4: Implement providers and registry**

Move the current hash algorithm unchanged. The semantic provider imports
`SentenceTransformer` only inside its loader, sets CPU, pinned revision and
`local_files_only=True`. Registry fallback is allowed only for implicit primary
resolution; explicit model selection fails rather than substituting a model.

- [ ] **Step 5: Preserve `EmbeddingService` compatibility and run tests**

Run provider tests plus existing backend unit tests. Expected: deterministic
hash vectors remain byte-for-byte compatible.

- [ ] **Step 6: Add redacted embedding integration health**

First run `cd apps/api && .venv/bin/python -m pytest tests/unit/test_embedding_health.py -q` and observe failure. Then add an `embeddings` component reporting
configured provider, effective hashing/semantic availability and safe fallback
category. Assert the response never contains the host cache path or raw loader
exception. Rerun the focused health and existing health tests; all must pass.

---

### Task 3: Add the model-cohort/source-identity migration

**Files:**

- Create: `apps/api/app/core/content_identity.py`
- Create: `apps/api/alembic/versions/0003_milestone2_vector_cohorts.py`
- Modify: `apps/api/app/models/document_chunk.py`
- Modify: `apps/api/app/core/migrations.py`
- Modify: `apps/api/app/core/schema_compatibility.py`
- Modify: `apps/api/tests/integration/db/test_migrations.py`
- Create: `apps/api/tests/unit/test_content_identity.py`

- [ ] **Step 1: Write canonical hash unit tests**

Verify CRLF/CR normalization to LF, no other rewriting, stable SHA-256, and the
`legacy-unversioned` sentinel.

- [ ] **Step 2: Add failing migration cases**

Cover clean upgrade, a baseline copy whose document hash/version is null,
known legacy hashing rows, unknown model refusal, mismatched content-hash
refusal, single-cohort downgrade/re-upgrade, multi-cohort downgrade refusal and
metadata drift. Add a regression where a fully compatible but unversioned M1
database is detected: it must stamp exactly `0002_milestone1_core`, then execute
`0003`; it must never stamp the new `head` directly.

- [ ] **Step 3: Run the focused migration suite and observe failure**

Run `cd apps/api && .venv/bin/python -m pytest tests/unit/test_content_identity.py tests/integration/db/test_migrations.py -q` against `pe_agent_test`.

- [ ] **Step 4: Implement additive upgrade and fail-closed downgrade**

Add `embedding_provider`, `embedding_model_version`, `embedding_dimension`,
`source_content_hash` and `source_file_version`; verify legacy model/vector
metadata before backfill. Compute canonical hashes for null legacy documents,
reject non-null mismatches, and use `legacy-unversioned` for null versions.

Replace uniqueness with document/chunk/full-model identity. Add a B-tree cohort
index and exact-identity partial HNSW indexes for hashing and the pinned MiniLM
revision when `vector` extension version supports HNSW. Never add a global mixed-
cohort ANN index.

- [ ] **Step 5: Mirror schema in SQLAlchemy and compatibility checks**

Use explicit `Index(..., postgresql_using="hnsw", postgresql_ops={"embedding":
"vector_cosine_ops"}, postgresql_where=...)` definitions aligned with Alembic.

Update `migrate_database()` so an unversioned full-M1 schema stamps
`0002_milestone1_core` and calls `upgrade(head)`. Add full-M2 compatibility
checks only for diagnostics; do not introduce a new direct-to-head stamp unless
every `0003` invariant and data value is independently verified.

- [ ] **Step 6: Rerun migration and full M1 regression tests**

Expected: normal migration cases pass; the two unsafe cases pass by proving the
operation is refused without data loss.

---

### Task 4: Make indexing batched, cohort-safe and stale-content-safe

**Files:**

- Modify: `apps/api/app/repositories/document_chunk_repository.py`
- Modify: `apps/api/app/services/document_indexing_service.py`
- Modify: `apps/api/scripts/index_documents.py`
- Create: `apps/api/scripts/prune_embedding_cohorts.py`
- Create: `apps/api/tests/integration/vector/test_indexing.py`
- Create: `apps/api/tests/unit/services/test_document_indexing.py`

- [ ] **Step 1: Write failing indexing tests**

Use deterministic fake providers to cover batch calls, dimension failure before
writes, two model cohorts, same-cohort replacement, transaction rollback,
semantic failure plus hashing success, and document-content changes.

- [ ] **Step 2: Verify tests fail against single-model indexing**

Run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/services/test_document_indexing.py tests/integration/vector/test_indexing.py -q
```

Expected: failures for missing batch/cohort/source-identity behavior, with no
changes to the long-lived developer database.

- [ ] **Step 3: Add identity-aware repository operations**

Implement exact-cohort delete/list, stale-source invalidation and current-source
search predicates. Never call the old broad `delete_by_document_id()` from the
new indexing path.

- [ ] **Step 4: Refactor indexing around complete validated batches**

Compute document source identity, invalidate stale cohorts, index requested
providers, report identities/failures/providers-requiring-reindex and update
`indexed_at` only for successful current content.

- [ ] **Step 5: Harden CLIs**

Remove `Base.metadata.create_all()` and extension creation from
`index_documents.py`. Require Alembic head, add provider/all-provider/force
options and make the prune command require explicit identity/export arguments.

- [ ] **Step 6: Run unit and PostgreSQL indexing tests**

Expected: changed old text cannot be retrieved; other current model cohorts are
preserved; no partial writes remain after failures.

Run the exact Step 2 command again. Expected: every collected test passes on
`pe_agent_test`; record the reported count.

---

### Task 5: Extend vector search without breaking its existing contract

**Files:**

- Modify: `apps/api/app/schemas/vector_search.py`
- Modify: `apps/api/app/services/vector_search_service.py`
- Modify: `apps/api/app/repositories/document_chunk_repository.py`
- Modify: `apps/api/app/api/routes_vector_search.py`
- Create: `apps/api/tests/integration/vector/test_vector_search.py`
- Modify: `apps/api/tests/integration/api/test_core_routes.py`

- [ ] **Step 1: Write failing request/response and repository tests**

Prove existing payloads still validate; optional document types, threshold and
registered identity work; global vector search remains available; company scope
excludes other companies; stale sources and wrong model versions never appear;
threshold and top-K are bounded.

Run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/integration/vector/test_vector_search.py tests/integration/api/test_core_routes.py -q
```

Expected: red failures for missing additive fields and cohort-safe behavior;
preserved M1 API tests remain green where unaffected.

- [ ] **Step 2: Add additive schemas**

Keep old fields and add optional `document_types`, `minimum_similarity`,
`embedding_provider`, `embedding_model` and `embedding_model_version`. Add
requested/effective identity, fallback flags and warnings to the response.

- [ ] **Step 3: Implement allowlisted selection and exact cohort SQL**

Implicit selection may fall back. Explicit selection must exist in the registry
and cannot fall back. Apply threshold in SQL or immediately after bounded SQL
results without returning below-threshold rows.

- [ ] **Step 4: Test adversarial mixed cohorts and exact-search fallback**

Insert a larger competing cohort and assert expected results/counts for each
partial-index identity and an unindexed identity using exact search.

- [ ] **Step 5: Run vector/API tests and M1 route regression**

Run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/integration/vector/test_vector_search.py tests/integration/api/test_core_routes.py -q
```

Expected: all tests pass; preserved vector payloads stay compatible, explicit
unknown identities return 400, and no cross-company/stale/mixed row appears.

---

### Task 6: Implement company-scoped safe RAG and retrieval audit

**Files:**

- Create: `apps/api/app/services/rag_query_service.py`
- Create: `apps/api/app/services/rag_context_service.py`
- Create: `apps/api/app/services/rag_safety_service.py`
- Modify: `apps/api/app/services/rag_retrieval_service.py`
- Modify: `apps/api/app/schemas/vector_search.py`
- Modify: `apps/api/app/api/routes_rag.py`
- Modify: `apps/api/app/repositories/audit_log_repository.py`
- Modify: `apps/api/app/core/logging.py`
- Create: `apps/api/tests/unit/rag/test_query.py`
- Create: `apps/api/tests/unit/rag/test_context.py`
- Create: `apps/api/tests/unit/rag/test_safety.py`
- Create: `apps/api/tests/integration/rag/test_rag_retrieval.py`
- Create: `apps/api/tests/unit/test_retrieval_logging.py`

- [ ] **Step 1: Write failing unit tests for three focused services**

Cover company/sector/geography/mandate/trigger composition, missing optional
facts, one-chunk-per-document diversity, context word budget, duplicate removal,
citations, prompt-injection line isolation and source warnings.

- [ ] **Step 2: Write failing integration/API tests**

Require `company_id`, reject nonexistent companies, exclude other companies and
disallowed types, represent `empty` plus `fallback_used=true`, retain all old
response fields and write safe audit metadata without raw passages/full query.
Simulate audit failure and assert no unaudited context is returned.

Run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/rag tests/unit/test_retrieval_logging.py tests/integration/rag/test_rag_retrieval.py -q
```

Expected: red failures for missing RAG services/fields/audit/log events.

- [ ] **Step 3: Implement dedicated request/response schemas**

Use `status: Literal["ok", "empty"]`; keep fallback boolean/reason separate.
Return query, count, source IDs, threshold, context budget, requested/effective
identity, context, citations and warnings.

Preserve the existing response `query` semantics as the normalized user-
submitted query. Keep the company/mandate/trigger-expanded retrieval query
internal; audit only its bounded digest/summary and never expose it through the
legacy field or logs.

- [ ] **Step 4: Implement orchestration and fail-closed audit**

Retrieve the company and optional mandate/triggers, call exact-cohort vector
search, build safe bounded context, insert one audit record and commit before
returning internal content. Roll back and raise a safe dependency error if audit
persistence fails.

Emit structured requested/effective identity, fallback category, company ID,
result count and correlation ID. Tests must prove cache paths, raw third-party
errors, full queries and document passages are absent from logs.

- [ ] **Step 5: Run RAG tests and full backend tests**

Expected: empty retrieval is successful, cross-company leakage is zero and
prompt-like source text is never emitted as an application instruction.

Run the exact Step 2 command, then
`cd apps/api && .venv/bin/python -m pytest tests/unit tests/integration/api/test_core_routes.py tests/integration/test_health.py -q`.
Expected: all collected tests pass; record both counts.

---

### Task 7: Synchronize the frontend RAG contract

**Files:**

- Read completely before editing:
  `apps/web/node_modules/next/dist/docs/01-app/03-api-reference/01-directives/use-client.md`
- Read completely before editing:
  `apps/web/node_modules/next/dist/docs/01-app/01-getting-started/05-server-and-client-components.md`
- Modify: `apps/web/src/lib/api.ts`
- Modify: `apps/web/src/app/rag/page.tsx`
- Modify: `apps/web/src/components/company-rag-section.tsx`

- [ ] **Step 1: Read the installed Next.js 16 guidance**

Do not rely on remembered framework behavior.

- [ ] **Step 2: Add distinct TypeScript request/response types**

Keep `VectorSearchRequest.company_id` nullable. Add `RAGRetrievalRequest` with a
required numeric company ID and additive status/fallback/identity/warning types.

- [ ] **Step 3: Remove global RAG submission**

Default to the first loaded company, require a selection before submit, remove
the `All companies` option and update explanatory copy. Show empty/fallback and
safety warnings without redesigning unrelated UI.

- [ ] **Step 4: Verify affected frontend boundaries**

Run:

```bash
cd apps/web
pnpm lint
pnpm exec tsc --noEmit
pnpm build
```

Expected: zero errors/warnings and 12/12 or the current exact route count built.

---

### Task 8: Build the six-company rerunnable seed matrix

**Files:**

- Create: `apps/api/app/services/demo_seed_service.py`
- Modify: `apps/api/scripts/seed_data.py`
- Modify: every existing `data/seed/*.json`
- Create: `data/seed/mandates.json`
- Create: `data/seed/triggers.json`
- Create: `data/seed/approvals.json`
- Create: `data/seed/feedback.json`
- Create: `apps/api/tests/integration/seed/test_seed_data.py`

- [ ] **Step 1: Write failing seed validation/idempotency tests**

Assert six companies, two mandates, 18 distinct persisted news records from 19
inputs, 18 documents, at least six contacts, at least 12 interactions, positive
and negative triggers, mandate assignments, all required document types,
high/medium/low cases, deliberately irrelevant documents, one three-document
RAG-empty/type-mismatch company, synthetic prompt-injection content, MCP/LLM
fallback metadata, multiple feedback types, pending draft status, and rejected/
`revision_requested` approval decisions. `pending` is never inserted as an
`Approval.decision`.

- [ ] **Step 2: Prove running seed twice currently fails the matrix**

Run only against the reset/migrated `pe_agent_test` fixture.

```bash
cd apps/api
.venv/bin/python -m pytest tests/integration/seed/test_seed_data.py -q
```

Expected: red failure because the six-company matrix and safe seed service do
not exist.

- [ ] **Step 3: Implement session-injected stable-ID upserts**

Move database-independent JSON loading/validation into the service. Upsert seed-
owned rows with `seed_owner=milestone2-demo-v1`. Companies/news/documents/
contacts/interactions/triggers use stable external or dedup IDs. Mandates and
feedback use seed IDs in `extra_data`; runs use a seed ID in `input_snapshot`;
scores/drafts/approvals are reached only through a seed-owned run/draft. If a
natural key collides with an unmarked user row, fail instead of updating it.
Skip the duplicate input and never delete unrelated rows. Preserve the current
approval vocabulary; future `changes_requested` appears only in metadata.

Compute canonical document `content_hash` and an explicit seed `file_version`.
When fixture content changes, update source identity so indexing invalidates old
cohorts. Insert an unrelated sentinel row before seeding and assert it is
byte-for-byte unchanged afterward.

- [ ] **Step 4: Remove schema mutation from the seed script**

The CLI verifies Alembic head and calls the service; it never calls
`create_all()`, drops, truncates or resets.

- [ ] **Step 5: Run the seed command twice on the test database**

Expected: identical row counts and stable primary keys on the second run.

Run the exact Step 2 pytest command after implementation. Its test calls the
session-injected service twice and asserts every approved scenario, unchanged
unrelated data, stable primary keys and exact distinct counts. Then invoke the
CLI once with an explicit safe `TEST_DATABASE_URL` and assert it refuses any
database whose identity fails the test guard.

Exact safe CLI invocation:

```bash
test -n "$DATABASE_URL"
test -n "$TEST_DATABASE_URL"
cd apps/api
DATABASE_URL="$DATABASE_URL" TEST_DATABASE_URL="$TEST_DATABASE_URL" .venv/bin/python -c "import os; from app.core.config import assert_safe_test_database_url; assert_safe_test_database_url(os.environ['TEST_DATABASE_URL'])"
DATABASE_URL="$DATABASE_URL" TEST_DATABASE_URL="$TEST_DATABASE_URL" .venv/bin/python scripts/seed_data.py --database-url "$TEST_DATABASE_URL"
```

---

### Task 9: Add deterministic retrieval evaluation

**Files:**

- Create: `apps/api/tests/fixtures/retrieval_evaluation.json`
- Create: `apps/api/app/services/retrieval_evaluation_service.py`
- Create: `apps/api/scripts/evaluate_retrieval.py`
- Create: `apps/api/scripts/semantic_probe.py`
- Create: `apps/api/tests/unit/services/test_retrieval_evaluation.py`
- Create: `apps/api/tests/integration/rag/test_evaluation_fixture.py`
- Create: `docs/RETRIEVAL_EVALUATION.md`

- [ ] **Step 1: Write failing metric and fixture tests**

Fixture cases include expected document, forbidden irrelevant/cross-company
documents, allowed types, threshold, Top-K, deterministic empty-by-type and
prompt-injection warning expectations. Test Recall@K, MRR, leakage, irrelevant
inclusion, empty, fallback and warning counts.

Run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/services/test_retrieval_evaluation.py tests/integration/rag/test_evaluation_fixture.py -q
```

Expected: red import/behavior failures; no MiniLM load or network request.

- [ ] **Step 2: Implement pure metrics and isolated evaluation orchestration**

The default integration case injects deterministic fake providers and verifies
the fixture contract without MiniLM. Report exact requested/effective identity.

- [ ] **Step 3: Add the real semantic probe entry point**

It asserts a safe test database, migrates/seeds it, indexes hashing and MiniLM,
runs the same fixture locally with `local_files_only=True`, fails on mixed-model
rows/cross-company leakage/expected-document miss, and writes a Markdown report.

- [ ] **Step 4: Run deterministic evaluation tests**

Expected: all pass without network/model cache.

Run the exact Step 1 command again and record the passing test count.

---

### Task 10: Install and download the real semantic stack, then run host probe

**Environment-only changes:** `apps/api/.venv` and the owner-supplied external
`${HF_MODEL_CACHE_DIR}`; neither is committed or printed in reports/logs.

- [ ] **Step 1: Obtain execution-level approval for external mutations**

The owner has approved the real-model design and external storage. Immediately
before package installation/network download/out-of-workspace directory
creation, use the execution tool's approval mechanism for those exact actions.
If approval is denied, stop: M2 cannot reach 100% without the required model
gate.

- [ ] **Step 2: Install exact semantic dependencies**

Run:

```bash
cd apps/api
.venv/bin/python -m pip install -r requirements-semantic.txt
.venv/bin/python -m pip check
```

Expected: sentence-transformers 5.6.0, transformers 5.13.0 and torch 2.13.0 are
installed without broken requirements. If the resolver rejects a pin, stop and
update the plan/spec with official compatibility evidence rather than loosening
versions silently.

- [ ] **Step 3: Create the approved external cache and download once**

Run with explicit environment, never `.env` mutation:

```bash
test -n "$HF_MODEL_CACHE_DIR"
HF_MODEL_CACHE_DIR="$HF_MODEL_CACHE_DIR" make semantic-download
```

Expected: pinned snapshot downloads, a CPU embedding has exactly 384 finite
values, and the script prints the full pinned revision.

- [ ] **Step 4: Prove offline reload**

Disable Hugging Face network access through offline environment flags and load
the provider from the same cache. Expected: successful identical-dimension
embedding and no network request.

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_MODEL_CACHE_DIR="$HF_MODEL_CACHE_DIR" make semantic-offline-smoke
```

- [ ] **Step 5: Run the host semantic probe against `pe_agent_test`**

Pass `TEST_DATABASE_URL` explicitly, index both cohorts, run the fixture and
review `docs/RETRIEVAL_EVALUATION.md`. Expected: required document retrieved,
irrelevant and cross-company sources excluded, zero mixed-model rows.

```bash
test -n "$DATABASE_URL"
test -n "$TEST_DATABASE_URL"
cd apps/api
DATABASE_URL="$DATABASE_URL" TEST_DATABASE_URL="$TEST_DATABASE_URL" .venv/bin/python -c "import os; from app.core.config import assert_safe_test_database_url; assert_safe_test_database_url(os.environ['TEST_DATABASE_URL'])"
cd ../..
DATABASE_URL="$DATABASE_URL" TEST_DATABASE_URL="$TEST_DATABASE_URL" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_MODEL_CACHE_DIR="$HF_MODEL_CACHE_DIR" make semantic-host-check
```

---

### Task 11: Add Docker semantic support without breaking base Compose

**Files:**

- Create: `docker-compose.semantic.yml`
- Modify: `apps/api/Dockerfile`
- Modify: `docker-compose.yml`
- Modify: `Makefile`
- Modify: `.github/workflows/ci.yml`
- Create: `apps/api/tests/unit/test_semantic_configuration_files.py`
- Create/Modify: Docker ignore files if model/cache exclusions are needed.

- [ ] **Step 1: Write configuration assertions**

Base `docker compose config` must have hashing default and no host bind. The
semantic override must require `HF_MODEL_CACHE_DIR`, set semantic provider/cache
inside the container and mount the host directory read-only.

Map `HF_HUB_OFFLINE: ${HF_HUB_OFFLINE:-1}` and
`TRANSFORMERS_OFFLINE: ${TRANSFORMERS_OFFLINE:-1}` into the API service. The
configuration test renders the override and asserts both container values are
`1`, not merely present in the host shell.

The override also mounts `./data/seed` at `/seed-data:ro` and
`./apps/api/tests/fixtures` at `/evaluation-fixtures:ro`, then sets explicit
container paths consumed by settings. This avoids widening the API Docker build
context and keeps fixtures out of the production image.

Run before implementation:

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/test_semantic_configuration_files.py -q
```

Expected: red failure because the override/config assertions do not exist.

- [ ] **Step 2: Install semantic dependencies in the API image**

Copy/install the semantic requirements and all required scripts. Never copy the
model into the image. Keep the non-root runtime user.

- [ ] **Step 3: Keep CI deterministic**

CI installs dependencies needed for import compatibility but runs only fake-
provider/default suites; it must not download or load MiniLM.

- [ ] **Step 4: Build and test base Compose**

Use only the disposable project `pe-agent-m2-check`, non-default host ports,
project-scoped new volumes and database names containing `test`. Never run the
gate against the long-lived default Compose project/volume.

Run these as separate commands from the repository root:

```bash
POSTGRES_DB=pe_agent_m2_app_test TEST_POSTGRES_DB=pe_agent_m2_test POSTGRES_PORT=55432 API_PORT=58000 WEB_PORT=53000 docker compose -p pe-agent-m2-check config --quiet
POSTGRES_DB=pe_agent_m2_app_test TEST_POSTGRES_DB=pe_agent_m2_test POSTGRES_PORT=55432 API_PORT=58000 WEB_PORT=53000 docker compose -p pe-agent-m2-check build api web
POSTGRES_DB=pe_agent_m2_app_test TEST_POSTGRES_DB=pe_agent_m2_test POSTGRES_PORT=55432 API_PORT=58000 WEB_PORT=53000 docker compose -p pe-agent-m2-check up -d --wait postgres
POSTGRES_DB=pe_agent_m2_app_test TEST_POSTGRES_DB=pe_agent_m2_test POSTGRES_PORT=55432 API_PORT=58000 WEB_PORT=53000 docker compose -p pe-agent-m2-check exec -T postgres createdb -U pe_agent pe_agent_m2_test
POSTGRES_DB=pe_agent_m2_app_test TEST_POSTGRES_DB=pe_agent_m2_test POSTGRES_PORT=55432 API_PORT=58000 WEB_PORT=53000 docker compose -p pe-agent-m2-check up -d --wait api web
curl -fsS http://localhost:58000/ready
curl -fsS http://localhost:58000/api/integrations/health
curl -fsS http://localhost:53000/
```

Expected: the newly created disposable services are healthy, embedding health
reports hashing, and no service/volume from the default Compose project is
started or migrated.

- [ ] **Step 5: Run the Docker semantic probe**

Use the same disposable project/database and both Compose files. Run as separate
commands with `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`:

```bash
HF_MODEL_CACHE_DIR="$HF_MODEL_CACHE_DIR" POSTGRES_DB=pe_agent_m2_app_test TEST_POSTGRES_DB=pe_agent_m2_test POSTGRES_PORT=55432 API_PORT=58000 WEB_PORT=53000 docker compose -p pe-agent-m2-check -f docker-compose.yml -f docker-compose.semantic.yml config --quiet
HF_MODEL_CACHE_DIR="$HF_MODEL_CACHE_DIR" POSTGRES_DB=pe_agent_m2_app_test TEST_POSTGRES_DB=pe_agent_m2_test POSTGRES_PORT=55432 API_PORT=58000 WEB_PORT=53000 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 docker compose -p pe-agent-m2-check -f docker-compose.yml -f docker-compose.semantic.yml run --rm api python -c "import os; assert os.environ['HF_HUB_OFFLINE'] == '1'; assert os.environ['TRANSFORMERS_OFFLINE'] == '1'"
HF_MODEL_CACHE_DIR="$HF_MODEL_CACHE_DIR" POSTGRES_DB=pe_agent_m2_app_test TEST_POSTGRES_DB=pe_agent_m2_test POSTGRES_PORT=55432 API_PORT=58000 WEB_PORT=53000 docker compose -p pe-agent-m2-check -f docker-compose.yml -f docker-compose.semantic.yml run --rm api sh -c 'test ! -w /models/huggingface'
HF_MODEL_CACHE_DIR="$HF_MODEL_CACHE_DIR" POSTGRES_DB=pe_agent_m2_app_test TEST_POSTGRES_DB=pe_agent_m2_test POSTGRES_PORT=55432 API_PORT=58000 WEB_PORT=53000 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 docker compose -p pe-agent-m2-check -f docker-compose.yml -f docker-compose.semantic.yml run --rm api python scripts/semantic_probe.py --no-write-report
HF_MODEL_CACHE_DIR="$HF_MODEL_CACHE_DIR" POSTGRES_DB=pe_agent_m2_app_test TEST_POSTGRES_DB=pe_agent_m2_test POSTGRES_PORT=55432 API_PORT=58000 WEB_PORT=53000 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 docker compose -p pe-agent-m2-check -f docker-compose.yml -f docker-compose.semantic.yml run --rm -e EMBEDDING_CACHE_DIR=/missing api python scripts/semantic_probe.py --expect-fallback --no-write-report
```

Expected: read-only assertion passes, exact revision loads offline, semantic
retrieval passes, and missing-cache mode reports hashing fallback.

- [ ] **Step 6: Tear down only the disposable project**

```bash
HF_MODEL_CACHE_DIR="$HF_MODEL_CACHE_DIR" POSTGRES_DB=pe_agent_m2_app_test TEST_POSTGRES_DB=pe_agent_m2_test POSTGRES_PORT=55432 API_PORT=58000 WEB_PORT=53000 docker compose -p pe-agent-m2-check -f docker-compose.yml -f docker-compose.semantic.yml down -v
```

Then run `docker compose ps` for the default project and confirm its prior state
was not altered. Rerun the Step 1 configuration pytest; it must pass.

---

### Task 12: Run the complete Milestone 2 checkpoint and synchronize docs

**Files:**

- Modify: `docs/ARCHITECTURE_DECISIONS.md`
- Modify: `docs/FINAL_IMPLEMENTATION_PLAN.md`
- Modify: `docs/IMPLEMENTATION_STATUS.md`
- Modify: `docs/RETRIEVAL_EVALUATION.md`
- Modify: `README.md`
- Modify: `README_ZH.md`

- [ ] **Step 1: Run all targeted unit suites**

Record exact test counts for provider, config, content identity, RAG safety,
context and evaluation tests.

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/test_config.py tests/unit/test_content_identity.py tests/unit/test_embedding_health.py tests/unit/test_retrieval_logging.py tests/unit/test_semantic_configuration_files.py tests/unit/services/embeddings tests/unit/services/test_document_indexing.py tests/unit/services/test_retrieval_evaluation.py tests/unit/rag -q
```

- [ ] **Step 2: Run all affected integration boundaries**

Record exact counts for migration, vector indexing/search, RAG audit/empty,
seed idempotency and deterministic evaluation fixtures.

```bash
cd apps/api
.venv/bin/python -m pytest tests/integration/db/test_migrations.py tests/integration/vector tests/integration/rag tests/integration/seed tests/integration/api/test_core_routes.py tests/integration/services/test_transaction_safety.py tests/integration/test_health.py -q
```

- [ ] **Step 3: Run complete backend regression and coverage**

```bash
cd apps/api
.venv/bin/python -m compileall app scripts alembic tests
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest --cov=app --cov-report=term-missing
```

- [ ] **Step 4: Run migration matrix on the isolated database**

Verify clean upgrade, compatible existing copy, null source-identity backfill,
single-cohort downgrade/re-upgrade, unsafe unknown metadata refusal, populated
multi-cohort downgrade refusal and post-prune downgrade only on disposable test
data. Run `alembic check` at the final head.

Run the migration pytest from Step 2, including the explicit unsafe multi-
cohort refusal selector. Then, only on the disposable test database already
populated by the host semantic probe, validate the operator-controlled path:

```bash
test -n "$DATABASE_URL"
test -n "$TEST_DATABASE_URL"
cd apps/api
DATABASE_URL="$DATABASE_URL" TEST_DATABASE_URL="$TEST_DATABASE_URL" .venv/bin/python -c "import os; from app.core.config import assert_safe_test_database_url; assert_safe_test_database_url(os.environ['TEST_DATABASE_URL'])"
DATABASE_URL="$DATABASE_URL" TEST_DATABASE_URL="$TEST_DATABASE_URL" .venv/bin/python scripts/prune_embedding_cohorts.py --database-url "$TEST_DATABASE_URL" --keep-provider hashing --keep-model local-hashing-384-v1 --keep-version 1 --export-path /private/tmp/m2-semantic-cohorts.json
DATABASE_URL="$TEST_DATABASE_URL" .venv/bin/alembic downgrade 0002_milestone1_core
DATABASE_URL="$TEST_DATABASE_URL" .venv/bin/alembic upgrade head
DATABASE_URL="$TEST_DATABASE_URL" .venv/bin/alembic check
```

Expected: export file exists and contains only removed semantic cohort metadata,
downgrade/re-upgrade/check all exit 0, and no unapproved row is deleted. Inspect
the disposable export, then delete only that generated `/private/tmp` file.

- [ ] **Step 5: Run frontend and build gates**

```bash
make lint
cd apps/web && pnpm exec tsc --noEmit
cd ../.. && make build
```

- [ ] **Step 6: Run real-model host and Docker gates**

Use the external cache and offline flags. Record model/package versions, full
snapshot SHA, Recall@K/MRR/leakage results, fallback result and read-only Docker
mount evidence.

Rerun Task 10 Step 5 exactly to rebuild both cohorts after the downgrade test.
Then rerun Task 11 Steps 4 and 5 exactly. Defer Task 11 Step 6 teardown until
after the HTTP probes below. Every command must pass; no required probe may be
skipped.

- [ ] **Step 7: Run Compose health and HTTP probes**

Validate base hashing startup and semantic override separately; probe `/health`,
`/ready`, `/api/integrations/health`, vector search, company-scoped RAG and Web
root/RAG page.

The semantic probe has seeded/indexed `pe_agent_m2_test` in the disposable
Compose PostgreSQL service. Recreate only API/Web against that test database,
first in base hashing mode and then semantic mode:

```bash
POSTGRES_DB=pe_agent_m2_test TEST_POSTGRES_DB=pe_agent_m2_aux_test POSTGRES_PORT=55432 API_PORT=58000 WEB_PORT=53000 docker compose -p pe-agent-m2-check up -d --wait --force-recreate api web
curl -fsS http://localhost:58000/health
curl -fsS http://localhost:58000/ready
curl -fsS http://localhost:58000/api/integrations/health
curl -fsS -o /private/tmp/m2-companies.json http://localhost:58000/api/companies
company_id=$(apps/api/.venv/bin/python -c "import json; rows=json.load(open('/private/tmp/m2-companies.json')); print(next(row['id'] for row in rows if row['domain']=='asteria.example'))")
curl -fsS -o /private/tmp/m2-vector.json -X POST http://localhost:58000/api/vector/search -H "Content-Type: application/json" -d "{\"query\":\"recurring revenue Germany expansion\",\"company_id\":${company_id},\"top_k\":3}"
COMPANY_ID="$company_id" apps/api/.venv/bin/python -c "import json, os; d=json.load(open('/private/tmp/m2-vector.json')); expected=int(os.environ['COMPANY_ID']); assert d['result_count'] > 0; assert all(r['company_id'] == expected for r in d['results']); assert d['effective_embedding']['provider'] == 'hashing'"
HF_MODEL_CACHE_DIR="$HF_MODEL_CACHE_DIR" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 POSTGRES_DB=pe_agent_m2_test TEST_POSTGRES_DB=pe_agent_m2_aux_test POSTGRES_PORT=55432 API_PORT=58000 WEB_PORT=53000 docker compose -p pe-agent-m2-check -f docker-compose.yml -f docker-compose.semantic.yml up -d --wait --force-recreate api web
curl -fsS http://localhost:58000/api/integrations/health
curl -fsS -o /private/tmp/m2-rag.json -X POST http://localhost:58000/api/rag/retrieve -H "Content-Type: application/json" -d "{\"query\":\"What evidence supports the company investment case?\",\"company_id\":${company_id},\"top_k\":3}"
COMPANY_ID="$company_id" apps/api/.venv/bin/python -c "import json, os; d=json.load(open('/private/tmp/m2-rag.json')); expected=int(os.environ['COMPANY_ID']); assert d['company_id'] == expected; assert d['status'] == 'ok'; assert d['fallback_used'] is False; assert d['effective_embedding']['provider'] == 'sentence_transformer'; assert all(r['company_id'] == expected for r in d['sources'])"
curl -sS -o /private/tmp/m2-rag-missing-company.json -w "%{http_code}\n" -X POST http://localhost:58000/api/rag/retrieve -H "Content-Type: application/json" -d '{"query":"test","top_k":3}'
curl -fsS http://localhost:53000/rag
```

Expected: liveness/readiness/health return 200; base vector search uses hashing
and only the company resolved from the stable Asteria seed domain; semantic RAG
uses the pinned semantic provider with no fallback and the same company scope;
the missing-company command prints `422`; Web RAG returns 200. Finally run Task
11 Step 6 exactly and delete only the four generated `/private/tmp/m2-*.json`
probe files. Never assume database-generated seed primary keys are stable across
isolated database rebuilds.

- [ ] **Step 8: Inspect the final diff**

Run `git diff --check`, status/name-status/stat, tracked-file deletion review,
added-line secret/private-key scan, dead-code/lint scan and unrelated-change
review. Confirm model files, caches, `.env` and test outputs are untracked or
ignored as intended.

- [ ] **Step 9: Update authoritative and public documentation**

Record every exact command and pass/fail/skip count in implementation status,
add confirmed architecture decisions, mark only verified M2 items complete and
synchronize both READMEs without promoting them to implementation authority.

- [ ] **Step 10: Rerun every gate affected by documentation/config changes**

At minimum rerun `git diff --check`, backend compile, frontend lint/type/build,
Compose config and any changed config tests.

- [ ] **Step 11: Commit Milestone 2 only after the checkpoint is green**

Every applicable M2 gate, including host MiniLM, Docker MiniLM, hashing fallback,
seed idempotency and migration safety, must pass with zero skipped required
checks. No limitation can waive a required gate for a 100% completion claim.

Stage the reviewed M2 implementation/docs, then run these post-staging checks:

```bash
git diff --cached --check
git diff --cached --name-status
git diff --cached --stat
git diff --cached --diff-filter=D --name-only
git diff --cached -U0
```

Review the final command specifically for credentials/private keys, host cache
paths, accidental generated/model files, dead code and unrelated changes. Only
after that review commit:

```bash
git commit -m "feat: complete milestone 2 semantic rag"
```

Expected: `docs/IMPLEMENTATION_STATUS.md` says M2 complete with evidence; M3
remains not started. If any required gate failed or was skipped, do not stage,
do not mark complete, do not commit and do not claim 100% completion.
