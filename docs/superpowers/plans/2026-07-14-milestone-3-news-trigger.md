# Milestone 3 News and Trigger Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a default-offline, server-configured news sync pipeline with safe RSS/public-page adapters, idempotent news persistence, hybrid validated trigger extraction and controlled event deduplication.

**Architecture:** Thin CLI/API entry points call one `NewsSyncOrchestrator`. Typed adapters return untrusted raw items; safety, parsing, normalization, matching, ingestion, trigger extraction and audit remain separate units. Each source is an isolated transaction, while standalone extraction isolates each article. No scheduler, queue, arbitrary-URL API, MCP, LangGraph or scoring rewrite is introduced.

**Tech Stack:** Python 3.12, FastAPI 0.139, Pydantic 2.13, SQLAlchemy 2.0, PostgreSQL 16, Alembic 1.18, httpx 0.28.1, beautifulsoup4 4.15.0, defusedxml 0.7.1, pytest 9.1, Next.js 16 validation only.

**Authority:** Latest owner instructions; the owner-supplied `CODEX_MASTER_PROMPT_PE_AGENT.md`; root/path `AGENTS.md`; `docs/FINAL_IMPLEMENTATION_PLAN.md`; `docs/ARCHITECTURE_DECISIONS.md`; `docs/IMPLEMENTATION_STATUS.md`. The approved design is `docs/superpowers/specs/2026-07-14-milestone-3-news-trigger-design.md`. The master prompt is intentionally owner-supplied rather than repository-tracked; its availability was verified before planning.

**Git rule:** Work directly on `main` per the owner's standing instruction. Do not create implementation commits between tasks. The mandatory milestone policy permits the M3 commit only after every required checkpoint and staged-diff review passes.

---

## File responsibility map

### Create

- `apps/api/alembic/versions/0004_milestone3_news_triggers.py` — compatible extraction lifecycle, constraints and indexes.
- `apps/api/app/integrations/news/__init__.py` — public adapter exports.
- `apps/api/app/integrations/news/base.py` — source/raw-item types, adapter protocol and adapter errors.
- `apps/api/app/integrations/news/config.py` — strict source-file loader and enabled-source registry.
- `apps/api/app/integrations/news/url_safety.py` — HTTPS/host/address/redirect validation.
- `apps/api/app/integrations/news/http_client.py` — bounded GET, MIME, retry and per-host interval.
- `apps/api/app/integrations/news/normalization.py` — URL/text/time/language normalization and hashing.
- `apps/api/app/integrations/news/mock.py` — repository-local fixture adapter.
- `apps/api/app/integrations/news/rss.py` — defused RSS/Atom parser.
- `apps/api/app/integrations/news/public_page.py` — configured static-page parser and sanitization.
- `apps/api/app/services/news_company_matcher.py` — deterministic direct/alias company matching.
- `apps/api/app/services/news_ingestion_service.py` — three-level identity and idempotent upsert.
- `apps/api/app/services/news_sync_service.py` — `NewsSyncOrchestrator`, per-source transactions, audit and aggregate report.
- `apps/api/app/services/trigger_providers/__init__.py` — provider exports.
- `apps/api/app/services/trigger_providers/base.py` — canonical types, candidate schema and provider protocol.
- `apps/api/app/services/trigger_providers/rules.py` — 14-category deterministic extraction.
- `apps/api/app/services/trigger_providers/llm.py` — optional OpenAI-compatible structured provider.
- `apps/api/app/services/trigger_batch_service.py` — standalone per-article extraction lifecycle/transaction/audit.
- `apps/api/scripts/sync_news.py` — thin news sync CLI.
- `apps/api/scripts/extract_triggers.py` — thin persisted-article extraction CLI.
- `data/news_sources.json` — checked-in mock-only source registry.
- `data/seed/news_sync_items.json` — deterministic no-network demo source items.
- `apps/api/tests/fixtures/news/rss.xml` — bounded RSS fixture.
- `apps/api/tests/fixtures/news/atom.xml` — bounded Atom fixture.
- `apps/api/tests/fixtures/news/public_page.html` — static page fixture.
- `apps/api/tests/unit/news/` — configuration, safety, client, parser, normalization and matching tests.
- `apps/api/tests/unit/triggers/` — rules, LLM validation and merge tests.
- `apps/api/tests/integration/news/` — ingestion, sync transactions, API and CLI tests.
- `apps/api/tests/integration/triggers/` — batch lifecycle, audit and idempotency tests.

### Modify

- `apps/api/requirements.txt` — pin httpx/Beautiful Soup/defusedxml runtime dependencies.
- `.env.example`, `apps/api/app/core/config.py`, `docker-compose.yml` — safe offline news/trigger settings.
- `apps/api/app/models/news_article.py`, `trigger.py` — M3 lifecycle and constraints.
- `apps/api/app/repositories/news_article_repository.py`, `trigger_repository.py`, `company_repository.py` — identity and selection queries.
- `apps/api/app/schemas/news_article.py`, `trigger.py` — request/report/read contracts.
- `apps/api/app/services/news_article_service.py`, `trigger_extraction_service.py`, `trigger_service.py` — preserve reads and add M3 orchestration.
- `apps/api/app/api/routes_news_articles.py`, `routes_triggers.py`, `main.py` — thin action routes and OpenAPI.
- `apps/api/app/core/exceptions.py` — safe invalid-request/disabled-action errors if needed.
- `apps/api/app/services/demo_seed_service.py`, `data/seed/news_articles.json`, `data/seed/triggers.json` — preserve M2 ownership and compatible M3 lifecycle defaults.
- `apps/api/tests/conftest.py`, migration/API/core schema/config tests — M3 boundaries and logging/database isolation.
- `Makefile` — `sync-news` and `extract-triggers` targets.
- `docs/FINAL_IMPLEMENTATION_PLAN.md`, `ARCHITECTURE_DECISIONS.md`, `IMPLEMENTATION_STATUS.md`, `README.md`, `README_ZH.md` — only after the checkpoint evidence exists.

---

### Task 1: Freeze M3 dependencies, settings and source contracts

**Files:**
- Modify: `apps/api/requirements.txt`
- Modify: `apps/api/app/core/config.py`
- Modify: `.env.example`
- Create: `apps/api/app/integrations/news/base.py`
- Create: `apps/api/app/integrations/news/config.py`
- Create: `apps/api/app/integrations/news/__init__.py`
- Create: `data/news_sources.json`
- Create: `data/seed/news_sync_items.json`
- Test: `apps/api/tests/unit/news/test_source_config.py`
- Modify: `apps/api/tests/unit/test_config.py`

- [ ] **Step 1: Write failing configuration tests**

Assert default development configuration is mock-only/offline, production sync
API is disabled unless explicitly enabled, bounds reject zero/negative/oversized
values, duplicate source IDs fail, network sources require HTTPS plus an exact
host, public-page sources require selectors, and mock fixture paths cannot escape
the configured fixture root.

Use the target interface:

```python
configured = Settings(_env_file=None)
assert configured.news_source_config.name == "news_sources.json"
assert configured.news_sync_api_effective is True
assert Settings(environment="production", _env_file=None).news_sync_api_effective is False

registry = NewsSourceRegistry.load(configured.news_source_config)
assert registry.enabled_ids == ("demo_mock",)
with pytest.raises(ValueError, match="duplicate"):
    NewsSourceRegistry([...same source_id twice...])
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/news/test_source_config.py tests/unit/test_config.py -q
```

Expected: FAIL because M3 settings/source classes do not exist.

- [ ] **Step 3: Pin the minimal dependencies, then obtain install approval**

Add exactly:

```text
httpx==0.28.1
beautifulsoup4==4.15.0
defusedxml==0.7.1
```

Pinning is a repository edit and may proceed. Before any package install or
network access, obtain explicit owner approval as required by the master prompt
and `AGENTS.md`. Only after approval, install from `requirements.txt`, run
`pip check`, and record any network or compatibility failure rather than
changing versions speculatively. If approval is denied, stop M3 at that blocker;
do not claim the dependency or milestone checkpoint passed.

- [ ] **Step 4: Implement strict settings and source types**

Add bounded settings for source path, fixture root, allowed hosts, HTTP timeouts,
redirect/retry/response/item limits, rate interval, company-match threshold,
event merge window/similarity, trigger mode/version, optional LLM endpoint/model/
credential and tri-state sync API enablement. `news_sync_api_effective` defaults
true outside production and false in production when no explicit override exists.

Implement `RawNewsItem`, `NewsSourceConfig`, `NewsFetchError`, `NewsAdapter`
protocol and `NewsSourceRegistry`. Requests can resolve enabled IDs only; they
never create a source from request data.

Checked-in `data/news_sources.json` contains only `demo_mock` and a repository-
relative fixture. No production URL, personal path or credential is tracked.

- [ ] **Step 5: Run focused tests and dependency validation**

Run the Step 2 command plus:

```bash
.venv/bin/python -m pip check
.venv/bin/python -c "import httpx, bs4, defusedxml; print(httpx.__version__, bs4.__version__, defusedxml.__version__)"
```

Expected: all tests pass; versions are `0.28.1 4.15.0 0.7.1`.

---

### Task 2: Implement URL safety and bounded HTTP transport

**Files:**
- Create: `apps/api/app/integrations/news/url_safety.py`
- Create: `apps/api/app/integrations/news/http_client.py`
- Test: `apps/api/tests/unit/news/test_url_safety.py`
- Test: `apps/api/tests/unit/news/test_http_client.py`

- [ ] **Step 1: Write failing URL-safety tests**

Cover HTTPS success; HTTP, userinfo, fragments, unsupported ports, IP literals,
localhost, `.local`, loopback/private/link-local/multicast/reserved/non-global DNS
answers, unallowlisted hosts and redirect-to-private rejection. Inject a resolver
so no test performs DNS.

- [ ] **Step 2: Run URL tests and verify failure**

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/news/test_url_safety.py -q
```

Expected: FAIL because `URLSafetyPolicy` is missing.

- [ ] **Step 3: Implement `URLSafetyPolicy`**

Normalize host with IDNA, require exact source/global allowlist membership,
resolve all addresses through an injected resolver and require every answer to
be globally routable. Return a normalized validated URL; never mutate a rejected
destination into an allowed one.

- [ ] **Step 4: Write failing HTTP-client tests**

Use `httpx.MockTransport`, injected monotonic clock/sleeper and resolver to cover:

- allowed HTML/XML MIME and body;
- wrong MIME;
- content-length and streamed overflow;
- connect/read timeout category;
- retry for timeout/429/502 with bounded backoff;
- no retry for other 4xx;
- manual redirect validation and redirect limit;
- per-host minimum interval;
- `trust_env=False`, GET only and no response-body error leakage.

- [ ] **Step 5: Implement bounded client and rerun tests**

Implement a small synchronous client returning `FetchedDocument(url, status,
content_type, body)`. Read via `client.stream`, stop once the configured byte
limit is exceeded and close every response. Map failures to safe typed categories.

Run both Task 2 test files. Expected: all pass without network.

---

### Task 3: Implement mock, RSS/Atom and public-page adapters

**Files:**
- Create: `apps/api/app/integrations/news/normalization.py`
- Create: `apps/api/app/integrations/news/mock.py`
- Create: `apps/api/app/integrations/news/rss.py`
- Create: `apps/api/app/integrations/news/public_page.py`
- Create: `apps/api/tests/fixtures/news/rss.xml`
- Create: `apps/api/tests/fixtures/news/atom.xml`
- Create: `apps/api/tests/fixtures/news/public_page.html`
- Test: `apps/api/tests/unit/news/test_normalization.py`
- Test: `apps/api/tests/unit/news/test_adapters.py`

- [ ] **Step 1: Write failing normalization tests**

Assert tracking/fragment/default-port removal, allowed-query retention, UTC date
parsing, HTML/script/style/event-attribute removal, whitespace/length bounds,
`und` language fallback and deterministic content hash over normalized title and
sanitized content.

- [ ] **Step 2: Implement normalization utilities**

Before implementation, run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/news/test_normalization.py -q
```

Expected red phase: FAIL because the normalization module is missing.

Keep each pure function typed and deterministic. Do not fetch, resolve companies
or write the database.

- [ ] **Step 3: Write failing adapter tests**

Fixtures must cover RSS 2.0, Atom namespaces, malformed/DTD/entity XML rejection,
static CSS selectors, relative links resolved only against an already validated
base URL, missing required fields, max-item truncation and mock path safety.

- [ ] **Step 4: Implement adapters**

Before implementation, run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/news/test_adapters.py -q
```

Expected red phase: FAIL because the adapters are missing.

Use `defusedxml.ElementTree.fromstring` for XML and Beautiful Soup with the
stdlib HTML parser for static pages. Convert output only to `RawNewsItem`.
Public-page selectors come only from `NewsSourceConfig`; missing selector values
reject an item safely rather than guessing.

- [ ] **Step 5: Run the Task 3 suite**

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/news/test_normalization.py tests/unit/news/test_adapters.py -q
```

Expected: all pass; no socket/DNS call occurs.

---

### Task 4: Add compatible M3 persistence lifecycle and constraints

**Files:**
- Create: `apps/api/alembic/versions/0004_milestone3_news_triggers.py`
- Modify: `apps/api/app/models/news_article.py`
- Modify: `apps/api/app/models/trigger.py`
- Modify: `apps/api/app/core/schema_compatibility.py` only if the tested bootstrap needs it
- Modify: `apps/api/tests/integration/db/test_migrations.py`
- Modify: `apps/api/tests/unit/test_core_schemas.py`

- [ ] **Step 1: Write failing ORM/schema assertions**

Require `trigger_extraction_status`, `trigger_extracted_at` and
`trigger_extraction_version` on news reads/ORM. Require non-null trigger
deduplication keys for new ORM rows and model constraints matching the target
migration.

- [ ] **Step 2: Add migration tests before the migration**

Extend the matrix to prove:

- clean zero → head;
- existing populated 0003 → 0004 preserves IDs/counts/content;
- null trigger dedup keys receive deterministic `legacy:<id>` identities;
- existing news receives a safe pending extraction lifecycle;
- duplicate non-null company/canonical URL, invalid confidence, unknown status,
  extraction method or review status is rejected before partial mutation;
- downgrade to 0003 removes only M3 columns/constraints/indexes and re-upgrade
  succeeds;
- `alembic check` reports no operations.

- [ ] **Step 3: Run migration tests and verify failure**

```bash
cd apps/api
.venv/bin/python -m pytest tests/integration/db/test_migrations.py -q
```

Expected: FAIL because revision 0004 is absent.

- [ ] **Step 4: Implement revision 0004 and ORM alignment**

Add:

- news extraction lifecycle columns and index on status/version;
- unique company/canonical-URL identity where URL is non-null;
- trigger confidence check;
- trigger ingestion/extraction/review status checks with explicit legacy `seed`
  compatibility;
- deterministic null dedup backfill then non-null;
- same-article/type uniqueness (nullable article IDs retain legacy seed rows);
- no destructive data rewrite.

Validate incompatible data before adding constraints. Downgrade reverses only
0004 artifacts.

- [ ] **Step 5: Run migration/schema tests**

Run Task 4 tests plus `DATABASE_URL="$TEST_DATABASE_URL" .venv/bin/alembic check`
only against the asserted safe test database. Expected: pass and no drift.

---

### Task 5: Implement deterministic company matching and news upsert

**Files:**
- Modify: `apps/api/app/repositories/company_repository.py`
- Modify: `apps/api/app/repositories/news_article_repository.py`
- Create: `apps/api/app/services/news_company_matcher.py`
- Create: `apps/api/app/services/news_ingestion_service.py`
- Test: `apps/api/tests/unit/news/test_company_matcher.py`
- Test: `apps/api/tests/unit/news/test_ingestion.py`
- Test: `apps/api/tests/integration/news/test_ingestion.py`

- [ ] **Step 1: Write failing company-match tests**

Cover configured direct domain; aggregate-feed matches against normalized company
name, company domain and aliases; word/token boundaries; collisions for each
input category; threshold miss; ambiguous matches; and deleted-company exclusion.
A caller cannot override a direct source binding.

- [ ] **Step 2: Implement matcher**

Before implementation, run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/news/test_company_matcher.py -q
```

Expected red phase: FAIL because the matcher is missing.

Return a typed accepted match or safe rejection category. Confidence is
deterministic and bounded; there is no fuzzy external service or LLM.

- [ ] **Step 3: Write failing identity/upsert tests**

Cover resolution priority:

1. namespaced `source_id:source_item_id`;
2. company plus canonical URL;
3. company plus content hash.

Assert created/updated/duplicate classification, company ownership immutability,
material-update detection, syndicated duplicate collapse, integrity-conflict
re-read and counter invariant `accepted = created + updated + duplicates`.

- [ ] **Step 4: Implement repository queries and ingestion service**

Before implementation, run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/news/test_ingestion.py tests/integration/news/test_ingestion.py -q
```

Expected red phase: FAIL because M3 identity/upsert behavior is missing.

Use parameterized ORM queries. Store only bounded sanitized raw metadata, never
full HTML. New articles start `trigger_extraction_status='pending'` with null
version/time. A material article change resets extraction to pending; a pure
duplicate does not.

- [ ] **Step 5: Run Task 5 tests**

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/news/test_company_matcher.py tests/unit/news/test_ingestion.py tests/integration/news/test_ingestion.py -q
```

Expected: pass with stable row counts on repeat.

---

### Task 6: Replace one-trigger keywords with typed 14-category rules

**Files:**
- Create: `apps/api/app/services/trigger_providers/base.py`
- Create: `apps/api/app/services/trigger_providers/rules.py`
- Create: `apps/api/app/services/trigger_providers/__init__.py`
- Modify: `apps/api/app/services/trigger_extraction_service.py`
- Test: `apps/api/tests/unit/triggers/test_rules.py`
- Test: `apps/api/tests/unit/triggers/test_candidate_validation.py`

- [ ] **Step 1: Write failing parameterized rule tests**

One case per canonical type (7 positive + 7 negative), plus multiple events in
one article, no-event article, word-boundary false positives, concrete evidence
sentence, explicit date extraction and published-time fallback.

- [ ] **Step 2: Define typed provider contracts**

Before implementation, run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/triggers/test_rules.py tests/unit/triggers/test_candidate_validation.py -q
```

Expected red phase: FAIL because the provider contracts/rules are missing.

Implement frozen canonical type sets, `TriggerCandidate` Pydantic validation,
`TriggerProviderResult` with warnings/fallbacks and a provider protocol. Candidate
does not accept `is_negative`; expose a server-derived property instead.

- [ ] **Step 3: Implement deterministic rules**

Rules are ordered and versioned (`m3-rules-v1`), emit at most one candidate per
canonical type per article and return the exact bounded sanitized sentence.
Confidence is finite and clamped 0–1.

- [ ] **Step 4: Adapt `TriggerExtractionService` without database writes yet**

Preserve the public class name for compatibility, but make pure candidate
extraction return a list. Do not commit or create ORM objects in this task.

- [ ] **Step 5: Run Task 6 tests**

Expected: all 14 categories, negative derivation and multi-candidate behavior pass.

---

### Task 7: Add optional validated LLM supplement with rule fallback

**Files:**
- Create: `apps/api/app/services/trigger_providers/llm.py`
- Modify: `apps/api/app/core/config.py`
- Modify: `.env.example`
- Modify: `apps/api/app/services/trigger_extraction_service.py`
- Test: `apps/api/tests/unit/triggers/test_llm_provider.py`
- Test: `apps/api/tests/unit/triggers/test_hybrid_extraction.py`

- [ ] **Step 1: Write failing LLM boundary tests**

Use `httpx.MockTransport`. Cover disabled rules-only mode, HTTPS/allowlisted
endpoint, missing key, timeout, non-2xx, invalid JSON/schema/type/confidence/date,
evidence absent from article, valid supplemental result and no secret/raw-output
logging.

- [ ] **Step 2: Implement the optional provider**

Before implementation, run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/triggers/test_llm_provider.py -q
```

Expected red phase: FAIL because the LLM provider is missing.

Use an injected HTTP client and an OpenAI-compatible chat-completions response
shape without adding an OpenAI SDK. Send bounded sanitized text and a fixed
structured prompt. Read the key only from the configured environment variable.
Validate URL via the same safety policy and validate every candidate locally.

- [ ] **Step 3: Implement hybrid orchestration**

Before implementation, run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/triggers/test_hybrid_extraction.py -q
```

Expected red phase: FAIL because hybrid fallback behavior is missing.

Rules always run. In hybrid mode call LLM only for rule-uncovered or ambiguous
content. Invalid/unavailable output adds a safe fallback category; it never
removes valid rule candidates or changes server-derived negativity.

- [ ] **Step 4: Run Task 7 tests**

Expected: rules-only needs no key/network; every simulated LLM failure falls back
safely; valid supplemental candidates pass strict evidence validation.

---

### Task 8: Persist trigger identity, event merge and extraction lifecycle

**Files:**
- Modify: `apps/api/app/repositories/trigger_repository.py`
- Modify: `apps/api/app/repositories/news_article_repository.py`
- Modify: `apps/api/app/services/trigger_extraction_service.py`
- Create: `apps/api/app/services/trigger_batch_service.py`
- Modify: `apps/api/app/models/trigger.py`
- Test: `apps/api/tests/unit/triggers/test_event_identity.py`
- Test: `apps/api/tests/integration/triggers/test_extraction_lifecycle.py`
- Test: `apps/api/tests/integration/triggers/test_transaction_safety.py`

- [ ] **Step 1: Write failing event-identity tests**

Assert deterministic same-article/type identity, company/type/date/token event
fingerprint, merge within configured date/Jaccard thresholds, non-merge for
ambiguous candidates, bounded unique evidence refs, max confidence and preserved
manual confirmed/rejected review status.

- [ ] **Step 2: Implement identity and repository lookups**

Before implementation, run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/triggers/test_event_identity.py -q
```

Expected red phase: FAIL because event identity/merge behavior is missing.

Hash only normalized non-sensitive identity material. Query same article/type and
candidate event windows deterministically. Do not compare raw full text in SQL.

- [ ] **Step 3: Write failing lifecycle/transaction tests**

Cover pending → processed, pending → no_trigger, failure → failed, current-version
no_trigger not reselected, explicit newer-version reprocessing, per-article audit
atomicity, audit failure rollback and partial batch success.

- [ ] **Step 4: Implement persistence and standalone batch service**

Before implementation, run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/integration/triggers/test_extraction_lifecycle.py tests/integration/triggers/test_transaction_safety.py -q
```

Expected red phase: FAIL because lifecycle and transaction ownership are missing.

`TriggerExtractionService` gets a no-commit `extract_and_persist(article)` method.
`TriggerBatchService` owns one transaction per article, including trigger writes,
article lifecycle and digest/ID-only audit. A no-trigger result is successful.

- [ ] **Step 5: Run Task 8 tests**

Expected: repeat extraction is count-stable, audit failure leaves article/trigger
state unchanged, and negative rows persist with `is_negative=true`.

---

### Task 9: Build per-source sync orchestration and safe reports

**Files:**
- Create: `apps/api/app/services/news_sync_service.py`
- Modify: `apps/api/app/services/news_article_service.py`
- Modify: `apps/api/app/repositories/audit_log_repository.py` only if a focused helper is justified
- Test: `apps/api/tests/unit/news/test_sync_report.py`
- Test: `apps/api/tests/integration/news/test_sync_service.py`
- Test: `apps/api/tests/integration/news/test_sync_transactions.py`

- [ ] **Step 1: Write failing report-invariant tests**

Test immutable report/error schemas and invariants, including requested and
succeeded source counts, `triggers_created`, `triggers_merged`, fallback counts,
and safe per-source error fields limited to `source_id`, category, retryability
and optional HTTP status:

```text
accepted = created + updated + duplicates
fetched = accepted + rejected + failed
```

Source fetch failure does not invent an item failure. Aggregate status is ok,
partial or failed according to source outcomes. Repeated sync keeps article and
trigger counts stable; reports/audits never include article bodies, raw URLs with
queries, credentials or raw model output.

- [ ] **Step 2: Write failing orchestration tests**

Inject adapter registry, matcher, ingestion and trigger services. Cover selected/
all enabled sources, max item bound, trigger toggle, unknown/disabled IDs, one
failed plus one successful source, all failed, source audit failure rollback and
retry-safe repeated sync.

- [ ] **Step 3: Implement `NewsSyncOrchestrator`**

Before implementation, run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/news/test_sync_report.py tests/integration/news/test_sync_service.py tests/integration/news/test_sync_transactions.py -q
```

Expected red phase: FAIL because orchestration and report contracts are missing.

Implement the approved orchestrator as class `NewsSyncOrchestrator` in
`news_sync_service.py`. For each source: fetch raw items, process items under
nested savepoints, optionally
extract triggers without independent commit, create source audit, then commit the
source. On source error rollback only that source and continue. Audit contains
IDs/counts/categories, never bodies, credentials or full URLs with query data.

- [ ] **Step 4: Run Task 9 tests**

Expected: partial source isolation, atomic audit and count invariants pass.

---

### Task 10: Add API and CLI actions without arbitrary URL inputs

**Files:**
- Modify: `apps/api/app/schemas/news_article.py`
- Modify: `apps/api/app/schemas/trigger.py`
- Modify: `apps/api/app/api/routes_news_articles.py`
- Modify: `apps/api/app/api/routes_triggers.py`
- Modify: `apps/api/app/core/exceptions.py`
- Create: `apps/api/scripts/sync_news.py`
- Create: `apps/api/scripts/extract_triggers.py`
- Modify: `Makefile`
- Modify: `apps/api/tests/integration/api/test_core_routes.py`
- Create: `apps/api/tests/integration/news/test_api.py`
- Create: `apps/api/tests/integration/news/test_cli.py`

- [ ] **Step 1: Write failing request/response/OpenAPI tests**

Require:

- `POST /api/news-articles/sync` and `POST /api/triggers/extract`;
- no URL/host/selector/content fields in request schemas (`extra='forbid'`);
- sync accepts only bounded unique enabled `source_id` values and an item limit;
- standalone extraction selects by bounded unique `article_ids`, `company_id`,
  or lifecycle `status` plus the configured/current extraction version;
- current-version pending/failed selection is explicit, current-version
  processed/no-trigger rows are not silently reselected, and reprocessing is
  allowed only for an explicitly permitted newer extraction version;
- unknown/disabled source 422;
- production-disabled sync action 403;
- all-dependency failure 503 with safe detail;
- partial report 200;
- preserved GET response fields plus additive M3 lifecycle fields.

- [ ] **Step 2: Implement thin routes and Pydantic schemas**

Before implementation, run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/integration/api/test_core_routes.py tests/integration/news/test_api.py -q
```

Expected red phase: FAIL because the action routes/contracts are missing.

Routes construct services from server settings and the DB dependency. They do not
contain parsing, matching, dedupe or transaction logic. Map typed domain errors
through the existing handler without exposing stack traces.

- [ ] **Step 3: Write and implement CLI tests/entry points**

CLI parsers accept source IDs/item bounds for sync and article IDs, `company_id`,
lifecycle status/current-or-explicitly-newer extraction version and bounds for
extraction. They never accept company domains or URLs. Test `extra='forbid'`,
all-article failure, partial success, current-version non-reselection and
`no_trigger` as success. Direct script and `python -m` invocation work.
Success/partial returns 0; total failure or invalid persisted scope returns
nonzero. JSON output is the same typed report.

Before implementation, run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/integration/news/test_cli.py -q
```

Expected red phase: FAIL because the CLI entry points are missing.

- [ ] **Step 4: Add Make targets and run Task 10 tests**

Do not run either mutating target with default settings. First provision a fresh,
migrated, isolated database whose name contains `test`, set explicit distinct
`DATABASE_URL`/`TEST_DATABASE_URL`, and call `assert_safe_test_database_url`.
Only then smoke the targets against `demo_mock` and the isolated database:

```bash
DATABASE_URL="$M3_TEST_DATABASE_URL" make sync-news
DATABASE_URL="$M3_TEST_DATABASE_URL" make extract-triggers
```

Tests and smokes must override safe test DB/source settings; they must not mutate
developer data or contact the network.

---

### Task 11: Reconcile deterministic seeds and perform affected regression

**Files:**
- Modify: `apps/api/app/services/demo_seed_service.py`
- Modify: `data/seed/news_articles.json`
- Modify: `data/seed/triggers.json`
- Modify: `apps/api/tests/integration/seed/test_seed_data.py`
- Modify: `apps/api/tests/integration/test_health.py` if news mode is reported
- Modify: `docker-compose.yml`

- [ ] **Step 1: Write failing seed compatibility assertions**

M2 seed remains 6 companies/18 deduplicated news and its owned triggers remain
readable. Rerun preserves IDs. Seeded news has valid ingestion/extraction
lifecycle defaults; seed triggers have non-null dedupe keys, valid confidence,
`extraction_method='seed'` and valid review status.

- [ ] **Step 2: Implement minimal seed/config alignment**

Before implementation, run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/integration/seed/test_seed_data.py -q
```

Expected red phase: FAIL because M3 seed lifecycle compatibility is missing.

Do not replace the M2 owner or delete rows. Add only fields required by 0004.
Base Compose explicitly remains mock/offline and does not start a scheduler.

- [ ] **Step 3: Run all targeted M3 unit tests**

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/news tests/unit/triggers tests/unit/test_config.py tests/unit/test_core_schemas.py -q
```

Record the exact count.

- [ ] **Step 4: Run all affected M3 integration boundaries**

```bash
cd apps/api
.venv/bin/python -m pytest tests/integration/db/test_migrations.py tests/integration/news tests/integration/triggers tests/integration/seed tests/integration/api/test_core_routes.py tests/integration/test_health.py -q
```

Record the exact count. Fix every failure before Task 12.

---

### Task 12: Run the complete M3 milestone checkpoint

**Files:**
- Modify only after evidence: `docs/FINAL_IMPLEMENTATION_PLAN.md`
- Modify only after evidence: `docs/ARCHITECTURE_DECISIONS.md`
- Modify only after evidence: `docs/IMPLEMENTATION_STATUS.md`
- Modify only after evidence: `README.md`
- Modify only after evidence: `README_ZH.md`

- [ ] **Step 1: Backend compile and full regression/coverage**

```bash
cd apps/api
.venv/bin/python -m compileall -q app scripts alembic tests
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest --cov=app --cov-report=term-missing
.venv/bin/python -m pip check
```

Expected: all pass, zero required skips. Record exact test count and coverage.

- [ ] **Step 2: Isolated migration operator matrix**

Run the migration test selector, then only on the guarded test database:

```bash
DATABASE_URL="$TEST_DATABASE_URL" .venv/bin/alembic downgrade 0003_milestone2_vector_cohorts
DATABASE_URL="$TEST_DATABASE_URL" .venv/bin/alembic upgrade head
DATABASE_URL="$TEST_DATABASE_URL" .venv/bin/alembic check
```

First assert `TEST_DATABASE_URL` is safe and distinct. Re-seed only the test DB
after downgrade/re-upgrade. Never mutate the developer DB for this gate.

- [ ] **Step 3: Frontend regression**

```bash
make lint
cd apps/web && pnpm exec tsc --noEmit
cd ../.. && make build
```

Expected: ESLint/TypeScript exit 0 and all Next.js routes build.

- [ ] **Step 4: Disposable Compose mock-only full-stack gate**

Use a unique project, volume, DB names and ports. Build API/Web, create the test
DB, start healthy services, then verify:

- `/health`, `/ready`, `/api/integrations/health` return 200;
- POST sync with `demo_mock` succeeds and reports no network adapter;
- repeat POST sync returns stable database counts and duplicates/updates only;
- POST extraction is count-stable and negative triggers are present;
- unknown source returns 422;
- request containing `url` returns 422;
- Web news and trigger pages return 200;
- API logs/audit contain no full article body or credential.

Tear down only the disposable project and volume. Confirm default Compose project
state is unchanged.

- [ ] **Step 5: Inspect the implementation diff before documentation**

Run:

```bash
git diff --check
git status --short
git diff --name-status
git diff --stat
git diff --diff-filter=D --name-only
```

Scan added lines and untracked files for credentials, private/internal URLs,
personal paths, `.env`, models/caches, response fixtures containing sensitive
content, TODO/FIXME/dead debug code and unrelated M4+ changes.

- [ ] **Step 6: Synchronize authoritative and public documentation**

Record exact commands/counts/failures/fixes/limitations in implementation status;
add confirmed M3 ADRs; mark only M3 complete in the final plan; update both
README product summaries without treating either README as implementation
authority. Explicitly state default offline/mock, manual sync only, optional
configured network/LLM modes, no scheduler and M4 not started.

- [ ] **Step 7: Rerun every documentation/config-affected gate**

At minimum rerun:

```bash
git diff --check
cd apps/api && .venv/bin/python -m compileall -q app scripts alembic tests
.venv/bin/python -m pytest tests/unit/news tests/unit/triggers tests/unit/test_config.py tests/unit/test_core_schemas.py -q
cd ../.. && make lint
cd apps/web && pnpm exec tsc --noEmit
cd ../.. && make build
docker compose config --quiet
```

- [ ] **Step 8: Stage and inspect the complete M3 diff**

Stage only reviewed M3 files, then run:

```bash
git diff --cached --check
git diff --cached --name-status
git diff --cached --stat
git diff --cached --diff-filter=D --name-only
git diff --cached -U0
```

Repeat secret/private path/generated/dead-code/unrelated-change review on the
cached diff, including every newly added file.

- [ ] **Step 9: Commit only after the complete gate is green**

```bash
git commit -m "feat: complete milestone 3 news triggers"
git status --short
git log -1 --oneline
```

Expected: clean worktree, M3 committed, M4 not started. If any required gate
failed or was skipped, do not mark M3 complete and do not commit.
