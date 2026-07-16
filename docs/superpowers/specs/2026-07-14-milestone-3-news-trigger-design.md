# Milestone 3 News and Trigger Intelligence Design

**Date:** 2026-07-14
**Status:** Approved by the repository owner and independent document review
**Scope:** Modules 7 and 8 only

## 1. Objective

Milestone 3 adds a safe, deterministic and idempotent news-ingestion pipeline
and hybrid trigger extraction without starting the MCP, LangGraph, scoring or
frontend-completion milestones. The default project remains offline and free to
run. Real RSS and public-page fetching exists only as an explicit server-side
opt-in.

Success means:

- mock, RSS/Atom and configured static public-page sources share one typed
  adapter boundary;
- callers cannot make the API fetch an arbitrary URL;
- news is sanitized, normalized, company-matched, deduplicated and upserted;
- positive and negative triggers include evidence, dates, methods and stable
  deduplication identities;
- optional LLM extraction is schema-validated and always has a deterministic
  rule fallback;
- repeated sync/extraction is count-stable and does not create uncontrolled
  duplicate events;
- CLI and API actions return an honest quality report and safe audit evidence;
- every required M3 checkpoint passes with zero required skips.

## 2. Confirmed product decisions

1. Default operation is fully offline. Checked-in configuration enables only a
   local mock source.
2. RSS and public-page adapters are implemented, but they may fetch only HTTPS
   sources defined in server-owned configuration and allowed by the global host
   allowlist.
3. Automated tests use a local HTTP mock transport and never require internet,
   paid APIs or real credentials.
4. M3 exposes manual CLI and API actions. It does not add a scheduler, worker,
   queue or automatic background fetch loop.
5. Deterministic rules run by default. An optional LLM provider is enabled only
   by explicit model/endpoint/key configuration, and invalid/unavailable LLM
   output falls back to rules.
6. The pipeline is layered rather than monolithic or queue-driven.
7. News source URLs are not request parameters. The API accepts only enabled
   `source_id` values from server configuration.
8. M3 makes negative events reliable downstream inputs but does not implement
   the M6 risk-scoring weights.

## 3. Existing compatibility baseline

The existing layered FastAPI route → service → repository → SQLAlchemy design
remains authoritative. Existing list endpoints and response fields are
preserved additively.

M1 already added most M3 persistence fields:

- `news_articles`: canonical URL, content hash, language, source reliability,
  company-match confidence, ingestion status/time and external ID;
- `triggers`: event date, evidence sentence, extraction method, deduplication
  key, negative flag and review status.

M3 adds an explicit extraction lifecycle to `news_articles` because the absence
of a trigger row cannot distinguish an unprocessed article from a processed
article that legitimately produced zero triggers. The lifecycle contains
`trigger_extraction_status` (`pending`, `processed`, `no_trigger`, `failed`),
`trigger_extracted_at` and a version identifier used to select intentional
reprocessing after rule changes.

M2 owns the deterministic six-company fixtures and natural-key safety rules.
M3 reuses those companies and expands ingestion/extraction fixtures without
overwriting unowned data. A new migration is limited to proven constraints,
indexes, safe backfills or nullability gaps. It must not drop/recreate tables or
rewrite unrelated status vocabularies.

The existing news and trigger pages continue to consume compatible list
responses. Dedicated sync UI belongs to the frontend milestone; M3 requires API,
CLI and live mock HTTP verification, not a new page.

## 4. Architecture

```text
CLI / POST /api/news-articles/sync
              |
      NewsSyncOrchestrator
              |
  configured enabled source IDs
              |
 MockAdapter / RSSAdapter / PublicPageAdapter
              |
       RawNewsItem (untrusted)
              |
 URL safety -> parse/sanitize -> normalize -> company match
              |
       NewsIngestionService
              |
 deterministic identity lookup + idempotent database write
              |
       TriggerExtractionService
              |
 rules + optional validated LLM supplement/fallback
              |
 trigger event merge + per-source audit + SyncReport
```

### 4.1 Adapter boundary

`app/integrations/news/` owns source configuration, the typed raw-item contract,
safe HTTP behavior and source-specific parsing. Adapters do not import ORM
repositories or commit transactions.

Required adapters:

- `mock`: reads deterministic local fixture items;
- `rss`: accepts bounded RSS 2.0 or Atom XML from a configured source;
- `public_page`: uses server-configured CSS selectors to parse a static public
  news listing page.

Pages requiring login, CAPTCHA, paywall bypass, arbitrary JavaScript execution
or browser automation are unsupported. M3 does not add Playwright or Firecrawl.

### 4.2 News ingestion boundary

`NewsIngestionService` accepts normalized candidates and owns company matching,
content hashing and deterministic identity lookup. It uses repositories for
database operations but does not perform HTTP requests.

### 4.3 Trigger provider boundary

`app/services/trigger_providers/` contains:

- a provider protocol and strict candidate schema;
- a deterministic rule provider;
- an optional LLM provider whose untrusted output must validate before use.

`TriggerExtractionService` orchestrates providers, verifies evidence against
the sanitized article, derives negativity server-side and delegates persistence
identity lookups to the trigger repository.

### 4.4 Orchestration and entry points

`NewsSyncOrchestrator` calls adapters, ingestion and trigger extraction and
returns an aggregate `SyncReport`. The API and CLI remain thin entry points and
share this service. Trigger extraction is also available separately for already
persisted articles.

## 5. Source configuration and URL safety

Source configuration is a strict server-owned JSON document. Each source has:

- unique `source_id`;
- adapter type: `mock`, `rss` or `public_page`;
- enabled flag;
- URL for network sources;
- exact allowed host;
- optional bound `company_domain` or deterministic company aliases;
- reliability score;
- language default;
- public-page selectors when applicable;
- mock fixture path when applicable.

API callers may select enabled source IDs and a bounded item limit. They cannot
submit URLs, hosts, selectors, fixture paths, headers or credentials.

Before every HTTP request and redirect hop:

- scheme must be HTTPS;
- normalized host must match both the source and global allowlists;
- credentials, fragments and unsupported ports are rejected;
- IP literals, localhost, loopback, private, link-local, multicast, reserved and
  otherwise non-global resolved addresses are rejected;
- redirect count is bounded and every location is revalidated;
- only GET is permitted.

HTTP behavior has explicit connect/read/overall timeouts, a bounded streamed
response size, MIME allowlists, per-host minimum interval and bounded exponential
backoff for timeouts, 429 and selected 5xx failures. The client does not log
response bodies or secrets.

DNS preflight checks reduce SSRF exposure but are not presented as a complete
defense against hostile DNS rebinding. Production deployment still requires
network egress controls.

## 6. Parsing, sanitization and normalization

All fetched content is untrusted data.

RSS/Atom parsing accepts only the bounded response and extracts source item ID,
title, link, summary/content and published/updated time. XML parsing must avoid
external entity expansion.

Public-page parsing uses only configured selectors. Script/style/template
content, HTML event attributes and markup are discarded. The normalized title,
summary and retained text are length-bounded. Directive-like text remains data
and never changes application behavior.

URL normalization:

- lowercases and IDNA-normalizes the host;
- removes fragments and default ports;
- normalizes path encoding and redundant separators safely;
- drops tracking parameters and retains only explicitly allowed query keys;
- never converts an unapproved destination into an approved one.

Times become timezone-aware UTC values. Language uses an explicit source value
or deterministic lightweight detection and falls back to `und`; M3 does not add
machine translation.

## 7. Company matching

Matching is deterministic and fail-closed:

1. A company-specific source binds directly to its configured company domain.
2. An aggregate feed compares normalized company name, domain and configured
   aliases against title and sanitized summary/content.
3. Exactly one qualifying match is accepted and receives a documented
   confidence value.
4. No match or multiple qualifying companies is rejected with a safe category;
   the pipeline does not guess.

The API does not allow callers to override the company selected by source
configuration or matching rules.

## 8. News identity and idempotent upsert

For persistence, a source item external identity is namespaced by source ID.
Existing rows are resolved in this order:

1. namespaced source external ID;
2. company plus canonical URL;
3. company plus canonical content hash.

The content hash covers normalized title and sanitized summary/content. A
syndicated copy with a different URL but identical normalized content is a
duplicate, not a second article. A known article may safely update mutable
metadata such as title, sanitized summary, published time, reliability and
source payload metadata. It may not change company ownership silently.

The repository preserves the existing uniqueness contracts and adds only the
indexes/constraints needed to make these identities safe under concurrent or
repeated execution. Integrity conflicts are resolved by re-reading the winner,
not by duplicating it.

## 9. Trigger extraction

One article may produce zero, one or multiple candidates.

Canonical positive types:

- `market_expansion`
- `product_launch`
- `partnership`
- `customer_win`
- `funding`
- `leadership_hire`
- `acquisition`

Canonical negative types:

- `layoffs`
- `profit_warning`
- `customer_loss`
- `regulatory_issue`
- `management_departure`
- `cyber_incident`
- `litigation`

The rule provider identifies the concrete sentence containing a matched pattern.
Event date uses an explicit supported date in the evidence when present,
otherwise the article publication time. Confidence is deterministic and bounded.
`is_negative` is derived from the canonical type and cannot be supplied by an
adapter or trusted from an LLM.

When hybrid mode is enabled, the LLM is used only for rule-uncovered or
ambiguous content. Its structured result must pass all of these checks:

- valid Pydantic schema;
- allowlisted canonical type;
- finite 0–1 confidence;
- bounded fields and timezone-aware date;
- evidence sentence exists in the sanitized article text;
- no caller-supplied or model-supplied negative override.

Invalid, timed-out or unavailable LLM output is discarded, a safe fallback
category is reported, and deterministic rule results remain authoritative. Raw
model output and full article text are not written to logs or audit rows.

## 10. Trigger deduplication and merge

Deduplication has two layers:

1. same article plus canonical trigger type;
2. cross-article event fingerprint using company, canonical type, normalized
   event date window and normalized event subject/action tokens.

Cross-article candidates merge only when their type, date proximity and token
similarity pass deterministic thresholds. Ambiguous candidates remain separate
rather than being destructively combined.

On merge:

- retain the earliest trigger row as primary;
- add the new article to bounded, unique evidence references;
- keep the higher validated confidence;
- preserve a manually confirmed or rejected review state;
- expose `triggers_created` and `triggers_merged` separately.

Existing M2 seed trigger vocabulary remains readable for backward compatibility.
New automatic extraction emits only the M3 canonical types.

## 11. Transactions, audit and error handling

Each source is an independent transaction boundary containing its news writes,
trigger writes and audit record. An audit persistence failure rolls back that
source. A failed source does not roll back other successfully committed sources.

Audit data contains source ID, safe configuration identity, counts, article and
trigger IDs, adapter/provider modes, fallback categories, timing and safe error
categories. It excludes response bodies, full article text, raw LLM output,
credentials and unnecessary URLs/query strings.

Aggregate status:

- `ok`: every requested source succeeded;
- `partial`: at least one source succeeded and at least one failed;
- `failed`: no requested source succeeded.

Unknown/disabled source IDs are request validation errors. All-source dependency
failure produces a safe API dependency error and nonzero CLI exit. Partial
success returns the report normally. Error items contain source ID, category,
retryability and optional HTTP status only.

For standalone extraction, each selected article is an independent transaction
containing trigger writes, the article extraction lifecycle update and an audit
record. Audit failure rolls back that article. One failed article does not roll
back other completed articles; the aggregate result uses the same
`ok`/`partial`/`failed` meanings, all-article failure returns a safe dependency
error/nonzero CLI exit, and a valid `no_trigger` result counts as a successful
processed article rather than a failure.

When extraction runs inside a source sync, the source transaction remains the
outer owner. Article-level savepoints isolate candidate failures, extraction
does not commit independently, and the source audit records article outcomes.
This preserves the promise that an audit failure rolls back the corresponding
source while still allowing standalone extraction to isolate articles.

## 12. API and CLI contracts

### 12.1 News sync API

`POST /api/news-articles/sync`

Request fields:

- `source_ids`: optional nonempty unique list of configured IDs; omission means
  all enabled default sources;
- `extract_triggers`: boolean, default true;
- `max_items_per_source`: bounded positive integer.

The production sync action is disabled by default and requires explicit server
configuration. The local development default permits the checked-in mock source.

### 12.2 Trigger extraction API

`POST /api/triggers/extract`

The request selects already persisted articles by bounded unique article IDs,
company ID or extraction lifecycle status/version. “Unprocessed” means
`trigger_extraction_status='pending'` for the current extraction version; a
`no_trigger` article is not selected again unless the caller explicitly requests
reprocessing under an allowed newer version. The request does not accept
arbitrary article text or URLs.

### 12.3 Report

The typed report includes status, source request/success counts, fetched,
accepted, created, updated, duplicate, rejected and failed counts, trigger
created/merged counts, fallback counts and safe errors.

Article counter invariants are fixed:

- `accepted = created + updated + duplicates`;
- for successfully fetched candidates,
  `fetched = accepted + rejected + failed`;
- `created` means a new row, `updated` means a material mutation of an existing
  identity, and `duplicates` means an existing identity required no mutation;
- `rejected` means deterministic policy/validation/company-match rejection;
- `failed` means an operational or persistence failure after an item was
  fetched. A source-level fetch failure is reported as a source error and does
  not invent an article failure count.

### 12.4 CLI

- `scripts/sync_news.py`: source selection, bounded max items and optional
  trigger extraction; returns nonzero if all sources fail;
- `scripts/extract_triggers.py`: selects a safe persisted scope; returns nonzero
  on validation or total processing failure.

CLI and API call the same services and do not duplicate business logic.

## 13. Configuration

Tracked configuration documents only safe defaults and placeholders:

- source configuration path;
- global allowed hosts;
- HTTP timeouts, redirect count, max response bytes, retry count/backoff and
  per-host interval;
- maximum items per source;
- match threshold and event merge thresholds/window;
- trigger provider mode: rules or hybrid;
- optional LLM endpoint/model and environment-only credential name;
- sync API enabled flag with production fail-safe behavior.

No real credentials, cookies, private feeds, personal paths or production source
URLs are committed. Default Compose and tests use the mock source without
network.

## 14. Migration strategy

Revision 0004 is created only for demonstrated persistence gaps. Expected work:

- backfill safe trigger deduplication keys where legacy rows are null;
- validate and constrain confidence to 0–1;
- add and backfill the news trigger-extraction lifecycle columns;
- validate extraction method, review status and news ingestion status values
  while retaining explicit legacy/seed compatibility values;
- add lookup/concurrency indexes or uniqueness needed by canonical URL and
  article/type event identity;
- make fields non-null only after a deterministic compatible backfill.

The migration must:

- upgrade a clean database;
- upgrade an existing M2 database without deleting rows;
- reject irreconcilable invalid values before partial mutation;
- downgrade/re-upgrade isolated test data;
- leave ORM metadata and Alembic head aligned.

## 15. Testing strategy

### 15.1 Unit tests

- source configuration and unknown/disabled ID validation;
- HTTPS/host/address/redirect URL safety;
- timeout, retry, size, MIME and rate-limit controls;
- mock, RSS/Atom and static page parsing;
- sanitization, URL/time/language normalization;
- direct, unique, missing and ambiguous company matching;
- external ID, URL and content-hash identity resolution;
- all 14 canonical positive/negative trigger categories and evidence sentences;
- valid/invalid LLM schema, type, confidence, evidence and fallback;
- same-article and cross-article event fingerprints/merge decisions.

### 15.2 Integration tests

- 0004 clean/existing/invalid/downgrade/re-upgrade/metadata migration matrix;
- repeated mock sync: second run adds no articles or triggers;
- syndicated different-URL duplicate collapses correctly;
- same event across articles merges evidence;
- source transaction isolation and audit-failure rollback;
- standalone per-article extraction transaction, audit and partial-failure
  behavior, including stable `no_trigger` lifecycle handling;
- sync and extraction API/OpenAPI contracts;
- unknown source, all-failed and partial-result semantics;
- negative trigger reaches repository/service consumers as `is_negative=true`;
- CLI zero/nonzero exit behavior;
- no test performs an internet request.

### 15.3 Milestone checkpoint

After targeted development checks, run:

1. all new/modified unit tests;
2. all affected news/trigger/migration/audit/API integration boundaries;
3. the complete M0–M2 backend regression and coverage suite;
4. backend compilation;
5. isolated Alembic migration matrix and `alembic check`;
6. frontend lint, TypeScript and production build;
7. base Compose configuration/build/health plus live mock sync HTTP probes;
8. `git diff --check`, tracked deletion review, secret/private-path scan,
   generated/cache/model scan, dead-code and unrelated-change review;
9. documentation synchronization and every affected gate rerun;
10. staged-diff review and M3 commit only with zero required skips.

Every new failure is fixed and the relevant checkpoint rerun before proceeding.
M4 does not start as part of this work.

## 16. Explicit non-goals and limitations

- no scheduler, worker, queue or automatic polling;
- no arbitrary URL fetch API;
- no browser automation, login, paywall or CAPTCHA bypass;
- no language translation or broad NLP platform;
- no MCP integration;
- no LangGraph orchestration;
- no risk-weight or scoring rewrite;
- no production authentication system or frontend sync-management UI;
- no claim that application-layer DNS checks replace deployment egress policy.
