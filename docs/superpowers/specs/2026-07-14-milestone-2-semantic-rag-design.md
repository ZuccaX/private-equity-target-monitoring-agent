# Milestone 2 Semantic Vector and Safe RAG Design

Date: 2026-07-14
Status: Approved by the repository owner
Scope: Modules 4, 5 and 11 only

## Authority and delivery boundary

This design follows, in order, the repository owner's latest instructions,
`CODEX_MASTER_PROMPT_PE_AGENT.md`, repository `AGENTS.md`,
`docs/FINAL_IMPLEMENTATION_PLAN.md`, confirmed architecture decisions and the
Milestone 1 implementation evidence.

Milestone 2 delivers semantic embeddings, isolated model cohorts, safe RAG,
deterministic seed scenarios and retrieval evaluation. It does not implement
news intelligence, MCP transports, LangGraph orchestration, mandate-aware
scoring, LLM drafting or approval transitions assigned to later milestones.
Seed data may describe those future fallback scenarios without implementing
their behavior.

The repository owner explicitly authorized implementation directly on `main`
for this and future repository work unless a later instruction says otherwise.
Existing uncommitted Milestones 0 and 1 changes must be preserved.

## Goals

- Keep the deterministic 384-dimensional hashing provider as an immediate,
  offline fallback.
- Add real `sentence-transformers/all-MiniLM-L6-v2` support and exercise it in
  host and Docker checkpoint tests.
- Store hashing and MiniLM embeddings as separate, queryable model cohorts
  without silently mixing their vector spaces.
- Add batch indexing, strict dimension checks, similarity thresholds,
  document filters, bounded retrieval and a safe HNSW index.
- Make RAG company-scoped, source-diverse, context-bounded, auditable and safe
  when retrieved text contains prompt-injection-like instructions.
- Expand deterministic, rerunnable demo data and measure retrieval behavior
  honestly with versioned evaluation fixtures.
- Keep normal runtime and tests network-free after the explicit model download
  step completes.

## Non-goals

- Replacing the existing synchronous agent workflow.
- Implementing live crawlers, LLM calls, MCP servers or real email delivery.
- Redesigning the frontend beyond the compatibility change needed to prevent
  cross-company RAG retrieval.
- Mutating or resetting the long-lived developer database during automated
  tests. Destructive checks use `pe_agent_test` only.

## Embedding provider architecture

Create a typed provider boundary under `app/services/embeddings/`:

- `base.py` defines an immutable embedding identity and a provider protocol.
  The identity contains provider, model, resolved model version and dimension.
- `hashing.py` moves the current deterministic implementation behind that
  protocol and preserves `local-hashing-384-v1` compatibility.
- `sentence_transformer.py` lazily loads MiniLM from a configured cache,
  performs batch encoding and validates every returned vector.
- `registry.py` resolves the configured primary provider and explicit fallback,
  returning structured fallback metadata rather than silently substituting a
  model.

The existing `EmbeddingService` remains as a compatibility adapter so current
imports and single-text callers do not break while indexing and search move to
the provider interface.

The semantic dependency is isolated in a pinned semantic requirements file.
Development and production Docker installs include it for Milestone 2 checks,
while the core provider registry can still start and use hashing if the package
or model is unavailable.

The tracked default provider is hashing for host development, base Docker and
CI. MiniLM becomes primary only through an explicit semantic provider setting
or semantic Compose override. Configuration tests cover default hashing,
semantic opt-in and semantic-unavailable fallback.

### Model storage and network policy

The host cache is an owner-configured directory outside the repository. Tracked
files expose only a configurable cache variable; they do not contain the
owner's absolute path.
The cache variable is documented in `.env.example` and may be supplied directly
through the process environment or an owner-managed ignored `.env`. This
implementation does not edit the real `.env` without a separate explicit
authorization for that file mutation. Base Docker Compose does not require an
external bind mount and remains runnable with hashing. An explicit semantic
Compose override/profile requires the host cache variable and mounts it
read-only at a stable container path such as `/models/huggingface` for the
approved real-model probe.

A dedicated download command is the only supported operation that fetches the
model. API startup, indexing, evaluation and test commands use local-only model
loading after download. A missing drive, missing snapshot or load failure is
reported as degraded semantic availability and activates the hashing provider.

The configured model revision and the resolved local snapshot/version are
stored with chunks and emitted in indexing and retrieval summaries. A bare
model name is not treated as a sufficient identity.

## Model-cohort data design

Add Alembic revision `0003` after `0002_milestone1_core`.

`document_chunks` retains its fixed `vector(384)` column because both approved
providers are 384-dimensional. Add or normalize these identity columns:

- `embedding_provider`;
- existing `embedding_model`;
- `embedding_model_version`;
- `embedding_dimension`;
- `source_content_hash`;
- `source_file_version`.

Before backfill, verify every legacy row has exactly the known
`local-hashing-384-v1` model and a 384-dimensional vector. Unknown model
metadata fails closed instead of being relabelled. Known legacy rows receive
the explicit hashing provider and version identity before new fields become
non-null.

Source identity uses a canonical SHA-256 of `content_text` after newline
normalization (`CRLF`/`CR` to `LF`) without other semantic rewriting. During
upgrade, a null `documents.content_hash` is computed and stored from that
canonical text. A non-null value must match the canonical value or migration
fails closed for operator review. Each legacy chunk receives the verified
document hash. A missing document file version is represented on chunks by the
stable `legacy-unversioned` sentinel; retrieval compares it with
`COALESCE(documents.file_version, 'legacy-unversioned')`. Baseline-copy tests
include documents with null hash/version and prove their chunks remain
retrievable after upgrade.

Replace the current `(document_id, chunk_index)` uniqueness rule with one
covering document, chunk index and the complete embedding identity. Add a
B-tree lookup index for that identity. Before finalizing the migration, pin one
exact MiniLM snapshot revision. Create separate partial cosine HNSW indexes for
the complete hashing and pinned MiniLM identities only when the database
reports a pgvector version with HNSW support. Exact identity predicates must
appear in indexed queries. Unsupported or unrecognized identities use exact
cosine ordering with the B-tree filter instead of a global ANN index.

All queries filter the complete embedding identity and dimension before vector
ordering. Equal dimensions never imply compatible vector spaces. Adversarial
integration data with a larger competing cohort verifies result count and
recall for each partial index and exact-search fallback.

Downgrade is lossless only while the table contains the single legacy hashing
cohort accepted by the old uniqueness constraint. The migration refuses a
multi-cohort downgrade with a clear prerequisite rather than deleting semantic
rows. Tests cover clean migration, known legacy data, unknown metadata refusal,
single-cohort downgrade/re-upgrade and populated multi-cohort downgrade refusal.
An explicit separately invoked cohort export/pruning command can prepare an
operator-approved database for downgrade; Alembic never makes that destructive
choice implicitly.

## Indexing behavior

Indexing accepts one or more explicit providers and embeds chunks in batches.
Every chunk is bound to the document's current content hash and file version.
For each document and provider identity, replacement is transactional:

1. split the current document content;
2. create and validate the complete embedding batch;
3. compare the current content identity with all existing cohorts;
4. invalidate/remove every stale-content cohort before it can be retrieved;
5. replace the matching current-content provider/model/version cohort;
6. report any other provider identities that now require rebuilding;
7. update indexing metadata and return counts, identities and warnings.

A failed semantic batch rolls back that cohort. If fallback is enabled, hashing
can still be indexed and the summary reports semantic failure. It must never
write hashing vectors under a MiniLM identity. Retrieval also requires chunk
content hash/file version to match the current document, providing a second
guard against stale passages. A document-change integration test proves old
text is no longer retrievable before every provider is rebuilt.

The reindex CLI removes its legacy `create_all()` call and requires an Alembic
schema at head. It supports provider selection, all-provider indexing and
explicit force behavior. The seed CLI also stops managing schema lifecycle.

## Vector search

The low-level `/api/vector/search` endpoint preserves optional global search
for explicit administrative and development diagnostics. Its request gains
optional document-type, minimum-similarity and registered provider/model
selection fields without removing current fields. `top_k` remains bounded.
Omitted selection resolves through configured primary/fallback behavior; an
explicit selection must match the registry allowlist and never silently falls
through to another identity.

The service:

- embeds the query with the selected provider;
- searches only the exact matching cohort;
- filters company and document type in SQL;
- applies the configured/requested minimum similarity;
- returns requested and effective model identities plus fallback warnings;
- returns an empty result rather than borrowing vectors from another model.

## Company-scoped RAG

`/api/rag/retrieve` uses a dedicated request schema with required `company_id`.
This intentionally resolves a conflict with the current RAG page, which offers
an `All companies` option. Global vector diagnostics remain available, but
business RAG cannot combine internal evidence from different target companies.
The RAG page and its API types are updated only as needed to enforce this rule.

`rag_query_service.py` builds a bounded query from the user's question and the
selected company's name, sector, geography, mandate and recent trigger facts.
Missing optional data does not fail retrieval.

`rag_context_service.py` applies document filters, similarity filtering,
source diversity and a configured context budget. It selects one qualifying
chunk per document before filling remaining capacity, avoids duplicate chunks,
and stops before the context limit. Citations retain document/chunk IDs, title,
type, source, similarity and model identity.

The additive RAG response retains current fields and adds:

- `status`: `ok` or `empty`;
- `fallback_used` and a safe optional `fallback_reason`;
- requested and effective model identities;
- threshold and context-budget metadata;
- structured citations and warnings.

No qualifying evidence returns an `empty` status and a safe empty-context
message. Fallback metadata is independent, so a response can accurately report
both `empty` and `fallback_used=true`. It does not fail an agent workflow.

API contract tests prove existing vector request/response fields remain,
vector search remains optionally global, unregistered identity selection is
rejected, RAG deterministically rejects a missing company, and the frontend no
longer sends a global RAG request.

## Untrusted-content handling and audit

`rag_safety_service.py` treats all retrieved and crawled text as data. It
detects common instruction-override patterns, removes or isolates instruction-
like lines from constructed context, wraps evidence in an explicit untrusted
data boundary and emits source-specific warnings. It does not claim that string
matching alone is a complete security boundary; later prompt construction must
still keep application rules outside retrieved content.

RAG retrieval writes an audit event for successful, empty and fallback
outcomes. The event stores company, model identity, counts, document/chunk IDs,
thresholds, warnings and a bounded query digest/summary. It does not persist an
unnecessary full query or duplicate full document passages. Audit failure rolls
back the audit transaction and prevents returning unaudited internal context.

## Deterministic seed matrix

Preserve current stable external IDs where possible and expand to six companies,
two mandates, three distinct persisted news items per company, three documents
per company, at least one contact per company and at least two CRM interactions
per company. This satisfies the required 6–8 company and 3–5 item ranges while
keeping the fixture reviewable.

The matrix covers:

- high, medium and low priority examples;
- positive and negative trigger records;
- duplicate news inputs with stable canonical/content identities: one extra
  duplicate input is skipped/upserted, leaving 18 distinct persisted rows;
- relevant and deliberately irrelevant documents;
- an RAG-empty company scenario;
- MCP and LLM fallback scenario metadata for later milestones;
- pending, rejected and `revision_requested` approval examples, preserving the
  current vocabulary until Milestone 6; fixture metadata may use the future
  label `changes_requested` without persisting that value;
- RAG relevance and other feedback examples.

Document types include investment memo, market review, management notes, CRM
note, commercial due diligence and risk review. Prompt-injection-like text is
included only in a clearly synthetic safety fixture. The RAG-empty company
still owns three documents; its evaluation query requests a document type that
none of them has, producing a deterministic empty result without relying on an
unstable similarity score.

Seed operations are stable-ID upserts. Running the complete seed command twice
must preserve row counts and update owned fixture fields without deleting
unrelated user rows. Automated seed checks use the isolated test database.
Changing the long-lived developer database requires a separate explicit action.

## Retrieval evaluation

Versioned fixtures identify each query, company, expected relevant document,
forbidden irrelevant/cross-company documents, allowed document types, threshold
and Top-K. Evaluation runs separately for MiniLM and hashing where meaningful.

The report records at least:

- Recall@K;
- mean reciprocal rank;
- cross-company leakage count;
- irrelevant-source inclusion count;
- empty-result behavior;
- fallback count and reason;
- prompt-injection warning coverage;
- requested/effective model identity.

The real MiniLM checkpoint must retrieve the expected document, exclude the
forbidden irrelevant source, respect company scope and show zero mixed-model
rows. Hashing results are reported as a deterministic fallback baseline, not
described as semantic quality.

## Error handling and observability

- Invalid provider configuration or dimension mismatch fails before database
  writes and uses safe error messages.
- Semantic load failure records the cause category without exposing local paths
  or raw third-party exception details.
- Indexing summaries distinguish indexed, skipped, failed and fallback counts.
- Retrieval responses and structured logs include requested/effective identity,
  fallback state, result count and correlation identifiers.
- Integration health exposes semantic model availability, cache state and the
  active fallback without exposing the host cache path.

## Test and milestone gate

Development is test-first. The default automated suite remains deterministic
and model-independent: injected fake providers cover provider contracts, batch
and dimension validation, registry fallback, query building, context budgets,
source diversity and safety filtering without downloading or loading MiniLM.

PostgreSQL integration suites use deterministic fake embeddings to cover
migration paths, partial-HNSW/exact-search behavior, model-cohort isolation,
transactional indexing, stale-content invalidation, filters/thresholds, audit,
empty RAG and seed idempotency. A deliberately unavailable model path verifies
hashing fallback without any real-model dependency.

Real MiniLM validation is a separately named host and Docker milestone probe,
not part of the default automated test suite. It uses the pre-downloaded,
local-only snapshot through the external cache and semantic Compose override,
and must retrieve expected evidence without live network access. Its exact
commands and results still gate Milestone 2 and are recorded alongside the
automated tests.

The final Milestone 2 checkpoint runs:

1. all new and modified unit tests;
2. vector, RAG, seed and migration integration tests;
3. the complete backend regression suite;
4. backend compilation and frontend lint, typecheck and production build;
5. clean/existing/downgrade/re-upgrade Alembic validation on `pe_agent_test`;
6. Docker builds, Compose health and real semantic/fallback probes;
7. `git diff --check` plus deletion, secret, dead-code and scope review;
8. documentation synchronization and exact result recording in
   `docs/IMPLEMENTATION_STATUS.md`.

Any newly introduced failure blocks completion and Milestone 3. Milestone 2 is
complete only after the full checkpoint passes; code completion alone is not
sufficient.

## Documentation synchronization

Update architecture decisions with the multi-model cohort, company-scoped RAG
and external-cache decisions. Update implementation status with exact commands,
counts, fallbacks and limitations. Update both READMEs only after behavior is
verified, keeping them public overviews rather than implementation authority.
