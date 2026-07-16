# Milestone 4 MCP Enterprise Boundaries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add locally runnable, typed CRM and document MCP boundaries with safe read fallback, approval-gated fail-closed writes, protected mock Egnyte synchronization and incremental pgvector indexing.

**Architecture:** Existing CRM, document and indexing services remain the business/data implementation. Typed gateways select direct or MCP adapters; two independent stateless Streamable HTTP sidecars expose strict allowlisted tools through the official stable MCP Python SDK. A shared approval/execution service reserves one-time capabilities before any side effect, while the document source validates and extracts server-owned TXT/PDF/DOCX files before caller-owned transactional persistence and indexing.

**Tech Stack:** Python 3.12, FastAPI 0.139, Pydantic 2.13, SQLAlchemy 2.0, PostgreSQL 16, Alembic 1.18, pgvector 0.5, MCP Python SDK 1.28.1 (`<2` compatibility boundary), httpx 0.28.1, pypdf 6.14.2, python-docx 1.2.0, defusedxml 0.7.1, pytest 9.1, Docker Compose and Next.js 16 validation only.

**Authority:** Latest owner instructions; the owner-supplied `CODEX_MASTER_PROMPT_PE_AGENT.md`; repository/path `AGENTS.md`; `docs/FINAL_IMPLEMENTATION_PLAN.md`; `docs/ARCHITECTURE_DECISIONS.md`; `docs/IMPLEMENTATION_STATUS.md`. The approved and reviewed design is `docs/superpowers/specs/2026-07-14-milestone-4-mcp-boundaries-design.md`.

**Git rule:** Work directly on `main` per the owner's standing instruction. The repository checkpoint rule overrides the plan skill's generic frequent-commit guidance: do not create implementation commits between tasks. Create the single M4 implementation commit only after every mandatory checkpoint, documentation update and staged-diff review passes. The plan document itself may be committed separately before implementation.

**Dependency rule:** Editing pinned requirements is in scope. Before running any package installation or network command, request explicit owner approval. If approval is denied or installation cannot be validated, stop at the blocker and do not claim M4 complete.

---

## File responsibility map

### Create — shared MCP and approval foundation

- `apps/api/app/integrations/mcp/__init__.py` — supported integration/tool exports.
- `apps/api/app/integrations/mcp/errors.py` — closed safe error-category enum and typed integration errors.
- `apps/api/app/integrations/mcp/endpoint.py` — server-owned endpoint/host/path validation.
- `apps/api/app/integrations/mcp/client.py` — official SDK Streamable HTTP session, discovery and structured tool calls.
- `apps/api/app/integrations/mcp/approval.py` — canonical JSON digest and HMAC capability codec.
- `apps/api/app/models/integration_action_approval.py` — approval lifecycle model.
- `apps/api/app/models/integration_action_execution.py` — unique idempotent execution model.
- `apps/api/app/schemas/integration_action.py` — approval status, token-free arguments and execution-envelope primitives.
- `apps/api/app/repositories/integration_action_repository.py` — locked approval/execution lookup and transitions.
- `apps/api/app/services/integration_action_service.py` — CLI issuance/status and caller-owned side-effect execution state machine.
- `apps/api/app/services/integration_audit_service.py` — redacted MCP/fallback audit persistence.
- `apps/api/scripts/mcp_approval.py` — local `issue`/`status` CLI; no public issuance API.
- `apps/api/alembic/versions/0005_milestone4_mcp_boundaries.py` — additive approval/execution/source-file identity migration.

### Create — CRM MCP boundary

- `apps/api/app/integrations/crm/__init__.py` — CRM gateway exports.
- `apps/api/app/integrations/crm/contracts.py` — strict read/write argument and result schemas.
- `apps/api/app/integrations/crm/base.py` — async gateway protocol.
- `apps/api/app/integrations/crm/direct.py` — existing-service adapter.
- `apps/api/app/integrations/crm/mcp_client.py` — CRM allowlist and typed MCP result validation.
- `apps/api/app/integrations/crm/gateway.py` — mode selection, read fallback and write fail-closed policy.
- `apps/api/mcp_servers/__init__.py` — API-image MCP package.
- `apps/api/mcp_servers/common.py` — Starlette/FastMCP mounting and liveness helper.
- `apps/api/mcp_servers/crm/__init__.py` — CRM sidecar package.
- `apps/api/mcp_servers/crm/tools.py` — tool registration delegating to shared services.
- `apps/api/mcp_servers/crm/server.py` — CRM Streamable HTTP ASGI application.

### Create — document MCP boundary

- `apps/api/app/integrations/documents/__init__.py` — document gateway exports.
- `apps/api/app/integrations/documents/contracts.py` — strict document tool contracts and manifest schema.
- `apps/api/app/integrations/documents/base.py` — async gateway protocol.
- `apps/api/app/integrations/documents/direct.py` — direct document/sync/index adapter.
- `apps/api/app/integrations/documents/mcp_client.py` — document allowlist and typed MCP result validation.
- `apps/api/app/integrations/documents/gateway.py` — mode selection, read fallback and write fail-closed policy.
- `apps/api/app/integrations/documents/path_safety.py` — root containment, symlink/special-file rejection.
- `apps/api/app/integrations/documents/extractors.py` — bounded TXT/PDF/DOCX signature/MIME/extraction pipeline.
- `apps/api/app/integrations/documents/mock_egnyte.py` — strict manifest-backed local source.
- `apps/api/app/services/document_sync_service.py` — idempotent sync, explicit inactivation and version metadata refresh.
- `apps/api/mcp_servers/documents/__init__.py` — document sidecar package.
- `apps/api/mcp_servers/documents/tools.py` — document MCP tool registration.
- `apps/api/mcp_servers/documents/server.py` — document Streamable HTTP ASGI application.
- `data/egnyte_mock/manifest.json` — server-owned synthetic manifest.
- `data/egnyte_mock/asteria/mcp-market-note.txt` — safe searchable offline demo document.
- `docker-compose.mcp.yml` — optional two-sidecar Compose override.

### Create — tests

- `apps/api/tests/unit/mcp/test_config_and_errors.py`
- `apps/api/tests/unit/mcp/test_endpoint.py`
- `apps/api/tests/unit/mcp/test_client.py`
- `apps/api/tests/unit/mcp/test_approval_codec.py`
- `apps/api/tests/unit/crm/test_contracts.py`
- `apps/api/tests/unit/crm/test_gateway.py`
- `apps/api/tests/unit/documents/test_manifest_and_path_safety.py`
- `apps/api/tests/unit/documents/test_extractors.py`
- `apps/api/tests/unit/documents/test_gateway.py`
- `apps/api/tests/integration/mcp/test_approval_lifecycle.py`
- `apps/api/tests/integration/mcp/test_crm_mcp.py`
- `apps/api/tests/integration/mcp/test_crm_writes.py`
- `apps/api/tests/integration/mcp/test_document_sync.py`
- `apps/api/tests/integration/mcp/test_document_indexing.py`
- `apps/api/tests/integration/mcp/test_document_mcp.py`
- `apps/api/tests/integration/mcp/test_health_and_audit.py`
- `apps/api/tests/integration/mcp/test_route_compatibility.py`
- `apps/api/tests/helpers/document_fixtures.py` — runtime synthetic PDF/DOCX/unsafe fixture builders; no binary fixtures committed.

### Modify

- `apps/api/requirements.txt` — pin `mcp==1.28.1`, `pypdf==6.14.2`, `python-docx==1.2.0`.
- `.env.example`, `apps/api/app/core/config.py` — typed endpoints, timeout/retry, fallback, write, approval and extraction settings.
- `apps/api/app/models/__init__.py`, `document.py` — register M4 models and raw source hash.
- `apps/api/app/core/schema_compatibility.py` — M4 schema inspection.
- `apps/api/app/repositories/contact_repository.py`, `crm_interaction_repository.py` — write support and deterministic summary queries.
- `apps/api/app/repositories/document_repository.py`, `document_chunk_repository.py` — include-deleted lookup, active selection, inactivation and metadata-only chunk-version refresh.
- `apps/api/app/services/crm_service.py` — relationship summary, canonical CRM note and strength update without commits.
- `apps/api/app/services/document_indexing_service.py` — targeted caller-owned indexing plus compatible all-document wrapper.
- `apps/api/app/schemas/crm.py`, `document.py`, `integration.py` — compatible strict result types.
- `apps/api/app/api/routes_crm.py`, `routes_documents.py`, `routes_health.py`, `routes_integrations.py` — gateway adoption and real async health.
- `apps/api/Dockerfile`, `docker-compose.yml`, `Makefile` — copy sidecars, optional run targets and unchanged default stack.
- `apps/api/scripts/seed_data.py`, `index_documents.py`, `sync_news.py`, `extract_triggers.py` — require the M4 migration head.
- `apps/api/tests/conftest.py`, config/core schema/migration/health/API/seed tests — M4 fixtures and compatibility.
- `docs/FINAL_IMPLEMENTATION_PLAN.md`, `docs/ARCHITECTURE_DECISIONS.md`, `docs/IMPLEMENTATION_STATUS.md`, `README.md`, `README_ZH.md` — update only after checkpoint evidence exists.

---

### Task 1: Pin M4 dependencies and strict configuration

**Files:**
- Modify: `apps/api/requirements.txt`
- Modify: `apps/api/app/core/config.py`
- Modify: `.env.example`
- Create: `apps/api/app/integrations/mcp/errors.py`
- Create: `apps/api/app/integrations/mcp/endpoint.py`
- Create: `apps/api/app/integrations/mcp/__init__.py`
- Test: `apps/api/tests/unit/mcp/test_config_and_errors.py`
- Test: `apps/api/tests/unit/mcp/test_endpoint.py`
- Modify: `apps/api/tests/unit/test_config.py`

- [ ] **Step 1: Write failing settings and endpoint tests**

Cover direct defaults; exact default local endpoints; allowed-host parsing;
positive timeout/retry/TTL/size/page/archive bounds; default read fallback true;
write defaults false; a missing/short signing key with writes enabled produces a
derived `not_configured` write state without preventing application startup;
HTTPS endpoints; HTTP only for exact configured local/Compose hosts; and
rejection of userinfo, query, fragment, wrong path or unallowlisted host.

Use the target interface:

```python
configured = Settings(_env_file=None)
assert configured.crm_integration_mode == "direct"
assert configured.document_integration_mode == "direct"
assert configured.mcp_read_fallback_enabled is True
assert configured.crm_mcp_writes_enabled is False
misconfigured = Settings(
    crm_mcp_writes_enabled=True,
    mcp_approval_signing_key="",
    _env_file=None,
)
assert misconfigured.crm_mcp_write_configuration_status == "not_configured"
assert validate_mcp_endpoint(
    configured.crm_mcp_endpoint,
    allowed_hosts=set(configured.mcp_allowed_host_list),
).path == "/mcp"
```

- [ ] **Step 2: Run the focused red phase**

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/mcp/test_config_and_errors.py tests/unit/mcp/test_endpoint.py tests/unit/test_config.py -q
```

Expected: FAIL because M4 settings and MCP modules do not exist.

- [ ] **Step 3: Request dependency-install approval, then pin and install**

Add exactly:

```text
mcp==1.28.1
pypdf==6.14.2
python-docx==1.2.0
```

Before invoking pip or network access, ask the owner for explicit approval. After
approval:

```bash
cd apps/api
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip check
.venv/bin/python -c "import mcp, pypdf, docx; print(mcp.__version__, pypdf.__version__, docx.__version__)"
```

Expected: install succeeds, `pip check` reports no broken requirements, versions
resolve to `1.28.1`, `6.14.2`, `1.2.0`. If metadata exposes the MCP version
differently, assert it with `importlib.metadata.version("mcp")`; do not change
the pin speculatively.

- [ ] **Step 4: Implement the closed error enum and settings**

Implement `MCPErrorCategory(str, Enum)` exactly as approved, including
`extracted_content_too_large`. Add endpoint, allowed host, timeout, read retry,
fallback, write enable, approval TTL/signing key, document root and extraction
bounds. Do not make an enabled write flag plus missing/short signing key a
settings-construction error. Expose a derived per-integration write
configuration status; health reports `not_configured`, while approval issuance
and every attempted write reject with the same safe category before execution.

`.env.example` documents names and safe local defaults only. It contains no real
signing key, external endpoint, credential or personal path.

- [ ] **Step 5: Implement server-owned endpoint validation and rerun**

The validator returns a normalized URL and never accepts endpoint material from
API/tool arguments. The transport later consumes only this validated settings
value. Run Step 2 plus `pip check`; expected all pass.

Do not commit. Continue only with a clean targeted gate.

---

### Task 2: Add the M4 approval/execution migration and models

**Files:**
- Create: `apps/api/alembic/versions/0005_milestone4_mcp_boundaries.py`
- Create: `apps/api/app/models/integration_action_approval.py`
- Create: `apps/api/app/models/integration_action_execution.py`
- Modify: `apps/api/app/models/document.py`
- Modify: `apps/api/app/models/__init__.py`
- Create: `apps/api/app/schemas/integration_action.py`
- Create: `apps/api/app/repositories/integration_action_repository.py`
- Modify: `apps/api/app/core/schema_compatibility.py`
- Modify: `apps/api/tests/integration/db/test_migrations.py`
- Modify: `apps/api/tests/unit/test_core_schemas.py`

- [ ] **Step 1: Write failing migration and metadata tests**

Assert revision 0005 upgrades an M3 database without changing existing document
or chunk rows; adds both action tables and nullable `documents.source_file_hash`;
enforces integration/status/digest/expiry constraints; creates unique execution
identity; leaves legacy source hashes null; downgrades to 0004 without affecting
legacy data; re-upgrades; and passes `alembic check` and ORM metadata comparison.

Expected schema constants:

```python
MILESTONE_4_SCHEMA = {
    "documents": frozenset({"source_file_hash"}),
    "integration_action_approvals": frozenset(
        {"id", "integration", "tool_name", "arguments_digest", "status"}
    ),
    "integration_action_executions": frozenset(
        {"id", "integration", "tool_name", "idempotency_key", "status"}
    ),
}
```

- [ ] **Step 2: Run migration red phase**

```bash
cd apps/api
.venv/bin/python -m pytest tests/integration/db/test_migrations.py tests/unit/test_core_schemas.py -q
```

Expected: FAIL because revision 0005/models/schema map are absent.

- [ ] **Step 3: Implement additive models and repository primitives**

Use UUID primary keys, timezone-aware timestamps, JSONB safe result references,
closed check constraints and unique `(integration, tool_name, idempotency_key)`
on executions. Approval holds a nullable execution FK so multiple approvals can
reference one prior succeeded execution. Repository methods must include
`SELECT ... FOR UPDATE` approval lookup and exact terminal transitions; no
repository method commits.

- [ ] **Step 4: Implement migration upgrade/downgrade and compatibility map**

Create executions before approvals on upgrade and drop approvals before
executions on downgrade. Do not fabricate raw hashes for legacy documents.
Reject unsafe constraint violations before tightening data, but do not delete or
rewrite unrelated rows.

- [ ] **Step 5: Run the migration matrix**

Run Step 2. Then run a guarded isolated test DB downgrade from 0005 to 0004,
upgrade to head and `alembic check`. Expected all pass with existing data counts
unchanged. Do not touch the developer database.

---

### Task 3: Implement canonical capability issuance and atomic execution

**Files:**
- Create: `apps/api/app/integrations/mcp/approval.py`
- Create: `apps/api/app/services/integration_action_service.py`
- Create: `apps/api/scripts/mcp_approval.py`
- Test: `apps/api/tests/unit/mcp/test_approval_codec.py`
- Test: `apps/api/tests/integration/mcp/test_approval_lifecycle.py`

- [ ] **Step 1: Write failing codec tests**

Cover stable canonical JSON ordering; SHA-256 digest; base64url payload/signature;
HMAC constant-time verification; invalid signature; expiry; integration/tool/
digest/key mismatch; no secret in `repr`, exception or logs; and token-free
arguments separate from `ApprovedToolCall[Arguments]`.

```python
digest = canonical_arguments_digest(CreateCRMNoteArguments(...))
token = codec.issue(approval_payload)
assert codec.verify(token).arguments_digest == digest
```

- [ ] **Step 2: Run codec red phase, implement minimal codec, rerun**

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/mcp/test_approval_codec.py -q
```

Expected before implementation: FAIL. After implementation: all pass without
network or database.

- [ ] **Step 3: Write failing PostgreSQL lifecycle tests**

Cover exact transitions:

- `approved -> executing -> consumed` with execution `executing -> succeeded`;
- `approved -> executing -> failed` with durable safe category;
- `approved -> expired`;
- trusted argument/tool mismatch `approved -> failed`;
- invalid signature makes no row transition;
- prior succeeded result causes new `approved -> consumed` without rerunning;
- prior executing/failed key rejects and fails new approval;
- concurrent token reuse performs the callback once;
- crash simulation leaves durable `executing` and is not auto-retried.

For every rejected attempt, also assert one durable redacted integration audit
record with the safe rejection category: invalid signature, expired, reused,
argument/tool mismatch and idempotency rejection. Invalid signature must leave
the approval row untouched but still produce `approval_invalid`. No rejection
audit may contain the token, raw arguments, signing key or exception text.

- [ ] **Step 4: Implement `IntegrationActionService` with transaction ownership**

Expose:

```python
issue_approval(integration, tool_name, arguments, approved_by, ttl) -> IssuedApproval
get_status(approval_id) -> ApprovalStatusRead
execute_approved(envelope, operation: Callable[[Session, Arguments], Result]) -> Result
```

Reservation commits before invoking `operation`; successful business mutation,
safe result refs, execution success and approval consumption commit together in
the operation transaction. A separate transaction persists known failure. The
service never retries operations and never logs full arguments/token. Inject an
`IntegrationAuditService` backed by an independent session factory and persist
exactly one audit for every failed attempt independently of reservation or
business-transaction rollback. Invalid-signature auditing must not load or
transition an approval row. Successful attempts are audited in the authoritative
business transaction so the same write attempt is never double-audited.

- [ ] **Step 5: Implement the guarded CLI and tests**

`mcp_approval.py issue` requires explicit `--database-url`, integration, tool,
`--arguments-file`, approver, bounded TTL and typed confirmation. `status`
requires database URL and approval UUID. Check migration head 0005. Print the
token only once; status prints no token or raw arguments.

Run Task 3 unit/integration tests. Expected all pass.

---

### Task 4: Implement the shared MCP client and redacted audit service

**Files:**
- Create: `apps/api/app/integrations/mcp/client.py`
- Create: `apps/api/app/services/integration_audit_service.py`
- Test: `apps/api/tests/unit/mcp/test_client.py`
- Test: `apps/api/tests/integration/mcp/test_health_and_audit.py` (initial cases)

- [ ] **Step 1: Write failing client tests**

Inject the SDK stream/client factory. Cover initialization, required read tools,
conditional write tools, extra-tool warning/no call, missing-tool error,
`structuredContent` requirement, `isError`, invalid Pydantic output, exact call
timeout, read retry count, zero write retries, disabled redirect/environment
proxy and no raw response in errors.

- [ ] **Step 2: Implement `MCPToolClient`**

Use MCP 1.28.1 `streamable_http_client` and `ClientSession`; create a new session
per bounded attempt, call `initialize`, validate discovery, call one allowlisted
tool and validate `structuredContent` with the supplied result model. Wrap calls
with AnyIO timeout. Retry only categories approved for reads.

- [ ] **Step 3: Implement safe integration audit persistence**

Create one builder accepting integration/tool/mode/duration/outcome/digest,
bounded counts/entity IDs/fallback/error. It must reject forbidden keys such as
`token`, `content`, `summary`, `raw_payload`, `endpoint`, `exception` and
`signing_key`. `IntegrationActionService` owns the single authoritative audit for
every write attempt: success in the business transaction and failure in an
independent short-lived transaction. Read-tool successes are audited in their
service transaction; gateway transport failure/fallback uses an independent
short-lived audit session so it cannot commit the caller's transaction. Define
and test ownership explicitly so a server/gateway does not double-audit a write.

- [ ] **Step 4: Run Task 4 tests**

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/mcp/test_client.py tests/integration/mcp/test_health_and_audit.py -q
```

Expected all implemented cases pass. No public socket or internet is used.

---

### Task 5: Build CRM contracts, direct services and write operations

**Files:**
- Create: `apps/api/app/integrations/crm/contracts.py`
- Create: `apps/api/app/integrations/crm/base.py`
- Create: `apps/api/app/integrations/crm/direct.py`
- Create: `apps/api/app/integrations/crm/__init__.py`
- Modify: `apps/api/app/services/crm_service.py`
- Modify: `apps/api/app/repositories/contact_repository.py`
- Modify: `apps/api/app/repositories/crm_interaction_repository.py`
- Modify: `apps/api/app/schemas/crm.py`
- Test: `apps/api/tests/unit/crm/test_contracts.py`
- Test: `apps/api/tests/integration/mcp/test_crm_writes.py` (service cases)

- [ ] **Step 1: Write failing strict contract tests**

Test positive IDs, maximum list sizes, timezone-aware `since`/`occurred_at`,
sentiment -1..1, strength 0..100, bounded note/idempotency strings, `extra`
rejection, canonical `create_crm_note` name and absence of a
`record_interaction` alias.

- [ ] **Step 2: Write failing service behavior tests**

Assert deterministic contacts/interactions ordering; relationship summary;
company/contact consistency; canonical note stored as `interaction_type="note"`,
`direction="internal"`, `source="mcp_mock"` with empty raw payload; strength
previous/new result; and no service/repository commit.

- [ ] **Step 3: Implement focused repository and service methods**

Keep existing reads compatible. Add `update_relationship_strength`, canonical
note creation and summary calculation. Validate company/contact membership before
mutation. Do not place approval/MCP logic in `CRMService`.

- [ ] **Step 4: Implement direct adapter and rerun**

The async direct adapter returns the same typed results and delegates to
`CRMService`. Write methods accept an already authorized operation context only;
the integration action service remains the approval authority.

Run Task 5 tests. Expected all pass.

---

### Task 6: Build the CRM MCP server, client, gateway and compatible routes

**Files:**
- Create: `apps/api/app/integrations/crm/mcp_client.py`
- Create: `apps/api/app/integrations/crm/gateway.py`
- Create: `apps/api/mcp_servers/__init__.py`
- Create: `apps/api/mcp_servers/common.py`
- Create: `apps/api/mcp_servers/crm/__init__.py`
- Create: `apps/api/mcp_servers/crm/tools.py`
- Create: `apps/api/mcp_servers/crm/server.py`
- Modify: `apps/api/app/api/routes_crm.py`
- Modify: `apps/api/Dockerfile`
- Test: `apps/api/tests/unit/crm/test_gateway.py`
- Test: `apps/api/tests/integration/mcp/test_crm_mcp.py`
- Test: `apps/api/tests/integration/mcp/test_route_compatibility.py` (CRM cases)

- [ ] **Step 1: Write failing gateway policy tests**

Cover direct mode; MCP success; timeout/transport/protocol/schema read fallback;
fallback disabled; no fallback for `tool_not_allowed`; write disabled locally;
write timeout/error with no retry/direct call; safe fallback metadata and audit.

- [ ] **Step 2: Write failing SDK server/client contract tests**

Build the FastMCP app in-process and use an injected `httpx.AsyncClient` with
ASGI transport plus explicit lifespan context. This must exercise official MCP
initialization, discovery and Streamable HTTP message handling without a public
socket. Assert the three read tools; conditional two write tools; typed results;
unknown tool rejection; and successful server audit.

- [ ] **Step 3: Implement common ASGI mounting and CRM tools**

`mcp_servers/common.py` creates `FastMCP(..., stateless_http=True,
json_response=True).streamable_http_app()` with the SDK's default internal
`/mcp` route, then mounts that ASGI app at `/` after an explicit `/health` route.
The resulting public MCP URL must be exactly `/mcp`, never `/mcp/mcp`. Manage
the session-manager lifespan explicitly. Register read tools always and write
tools only when enabled. Each tool creates its own session and delegates to
`CRMService` or `IntegrationActionService`.

- [ ] **Step 4: Implement typed CRM client and gateway**

The client hard-codes the authoritative allowlist and result model per tool.
The gateway chooses direct/MCP once from settings; reads may fallback under the
approved categories; writes never retry/fallback. It returns domain-compatible
models plus private outcome metadata for audit/future graph warnings.

- [ ] **Step 5: Adopt the gateway in existing routes**

Convert route functions to async where required. Company-scoped requests use the
gateway. Unscoped list requests preserve the direct compatibility path and write
`direct_unscoped_compatibility` audit. Response models and status behavior remain
unchanged.

- [ ] **Step 6: Run CRM tests and route regressions**

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/crm tests/integration/mcp/test_crm_mcp.py tests/integration/mcp/test_crm_writes.py tests/integration/mcp/test_route_compatibility.py tests/integration/api/test_core_routes.py -q
```

Expected all pass; no LangGraph or public write API is added.

---

### Task 7: Implement controlled mock Egnyte manifests and safe extraction

**Files:**
- Create: `apps/api/app/integrations/documents/contracts.py`
- Create: `apps/api/app/integrations/documents/path_safety.py`
- Create: `apps/api/app/integrations/documents/extractors.py`
- Create: `apps/api/app/integrations/documents/mock_egnyte.py`
- Create: `apps/api/tests/helpers/document_fixtures.py`
- Create: `data/egnyte_mock/manifest.json`
- Create: `data/egnyte_mock/asteria/mcp-market-note.txt`
- Test: `apps/api/tests/unit/documents/test_manifest_and_path_safety.py`
- Test: `apps/api/tests/unit/documents/test_extractors.py`

- [ ] **Step 1: Write failing manifest/path tests**

Cover stable company domain, external ID, relative path, exact MIME/version/state,
duplicate identity, missing file, traversal, absolute path, symlink, special
file, root disappearance, missing entry versus explicit inactive and rejection
of request-supplied paths/MIME.

- [ ] **Step 2: Implement strict manifest source**

Resolve company ID to the stable company domain, then select entries. Resolve
paths and prove containment under `DOCUMENT_MCP_ROOT`. Never infer inactivation
from absence. The checked-in manifest contains synthetic content only and no
personal path or real internal material.

- [ ] **Step 3: Write failing extractor tests with runtime fixtures**

Generate PDF/DOCX fixtures under pytest `tmp_path` using the pinned libraries;
do not commit binary files. Cover:

- `.txt` + `text/plain`, UTF-8/BOM, invalid bytes and NUL;
- `.pdf` + `application/pdf`, signature, encryption, page and byte bounds;
- `.docx` exact OOXML MIME/signature/required entries;
- extension/MIME mismatch;
- DOCX entry count, individual/total expanded size, ratio, traversal, symlink,
  external relationship, embedded object, macro and encrypted archive;
- extracted text over limit rejects without truncation;
- no partial result after any failure.

- [ ] **Step 4: Implement preflight-first extraction**

Hash exact raw bytes before parsing, enforce every bound before allocating or
extracting, then return normalized text and both hashes. Use pypdf for PDF,
ZIP preflight plus python-docx for DOCX and hardened XML checks via defusedxml.
Never evaluate links or embedded content.

- [ ] **Step 5: Run all document safety unit tests**

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/documents/test_manifest_and_path_safety.py tests/unit/documents/test_extractors.py -q
```

Expected all pass, with no network or repository writes outside fixtures.

---

### Task 8: Implement idempotent document sync and version-only chunk refresh

**Files:**
- Create: `apps/api/app/services/document_sync_service.py`
- Modify: `apps/api/app/models/document.py`
- Modify: `apps/api/app/repositories/document_repository.py`
- Modify: `apps/api/app/repositories/document_chunk_repository.py`
- Modify: `apps/api/app/schemas/document.py`
- Test: `apps/api/tests/integration/mcp/test_document_sync.py`

- [ ] **Step 1: Write failing sync integration tests**

Cover initial create, exact repeat unchanged, raw-file-only change, version-only
change with identical normalized content, content change, explicit inactive,
missing manifest/root without deletion, unsafe entry isolation, company scope and
transaction rollback.

For version-only change assert:

```python
assert document.file_version == "v2"
assert {chunk.source_file_version for chunk in chunks} == {"v2"}
assert chunk_ids_after == chunk_ids_before
assert embeddings_after == embeddings_before
assert rag_result.count > 0
```

- [ ] **Step 2: Implement repository primitives**

Add include-deleted external-ID lookup, restore/update/inactivate methods, active
company selection and `refresh_source_file_version(document_id, from_version,
to_version)` with a row-count assertion. Chunk deletion remains explicit for
content change/inactivation.

- [ ] **Step 3: Implement caller-owned sync service**

The service accepts a session and source, performs savepoints per manifest item,
returns bounded safe counts/IDs/categories and never commits. Raw-byte changes
update `source_file_hash`; normalized content changes update `content_hash` and
mark cohorts stale; version-only changes atomically update document/chunk source
versions without embedding work.

- [ ] **Step 4: Run sync and existing M2 retrieval regression tests**

```bash
cd apps/api
.venv/bin/python -m pytest tests/integration/mcp/test_document_sync.py tests/unit/services/test_document_indexing.py tests/integration/rag -q
```

Expected all pass using the verified current test paths.

---

### Task 9: Refactor indexing for targeted caller-owned transactions

**Files:**
- Modify: `apps/api/app/services/document_indexing_service.py`
- Modify: `apps/api/app/repositories/document_repository.py`
- Modify: `apps/api/app/repositories/document_chunk_repository.py`
- Modify: `apps/api/scripts/index_documents.py`
- Test: `apps/api/tests/integration/mcp/test_document_indexing.py`
- Modify: existing document-indexing and retrieval tests

- [ ] **Step 1: Write failing targeted-index tests**

Assert company/document ownership, active-only selection, explicit provider,
unchanged cohort skip, stale cohort replacement, all-provider failure rollback,
safe result summary and no internal commit. Test that the legacy
`index_all_documents()` wrapper still commits for the CLI and returns its current
shape.

- [ ] **Step 2: Run red phase**

```bash
cd apps/api
.venv/bin/python -m pytest tests/integration/mcp/test_document_indexing.py -q
```

Expected: FAIL because targeted caller-owned indexing is absent.

- [ ] **Step 3: Split compute/mutation from CLI transaction ownership**

Implement a non-committing method such as:

```python
index_company_documents(
    company_id: int,
    document_ids: list[int] | None,
    embedding_services: Sequence[EmbeddingService],
) -> DocumentIndexingSummary
```

Do not catch-and-commit inside it. Retain `index_all_documents()` as a compatible
wrapper that begins/commits and rolls back for the existing script. Explicit
semantic requests fail safely if the pinned model is unavailable; do not silently
mix/fallback cohorts.

- [ ] **Step 4: Prove sync → index → RAG**

With a test approval/operation transaction, sync the checked-in TXT, index with
hashing, then call company-scoped RAG and assert the new document/chunk IDs and
citation. Repeat sync/index and assert no duplicate rows/chunks.

- [ ] **Step 5: Run indexing/RAG regression tests**

Run:

```bash
cd apps/api
.venv/bin/python -m pytest tests/integration/mcp/test_document_indexing.py tests/unit/services/test_document_indexing.py tests/unit/services/embeddings tests/integration/vector tests/integration/rag -q
```

Expected all pass with hashing default and no model/network dependency.

---

### Task 10: Build the document MCP server, client, gateway and routes

**Files:**
- Create: `apps/api/app/integrations/documents/base.py`
- Create: `apps/api/app/integrations/documents/direct.py`
- Create: `apps/api/app/integrations/documents/mcp_client.py`
- Create: `apps/api/app/integrations/documents/gateway.py`
- Create: `apps/api/app/integrations/documents/__init__.py`
- Create: `apps/api/mcp_servers/documents/__init__.py`
- Create: `apps/api/mcp_servers/documents/tools.py`
- Create: `apps/api/mcp_servers/documents/server.py`
- Modify: `apps/api/app/api/routes_documents.py`
- Test: `apps/api/tests/unit/documents/test_gateway.py`
- Test: `apps/api/tests/integration/mcp/test_document_mcp.py`
- Test: `apps/api/tests/integration/mcp/test_route_compatibility.py` (document cases)

- [ ] **Step 1: Write failing gateway and discovery tests**

Cover the three required read tools, conditional two write tools, result bounds,
direct/MCP selection, read fallback categories, fallback disabled, write disabled,
write fail-closed, timeout/no retry and safe audit.

- [ ] **Step 2: Write failing official SDK contract tests**

Exercise the document ASGI app through official MCP Streamable HTTP using the
same in-process transport/lifespan technique as CRM. Assert list/metadata/content
and approved sync/index. Verify no tool accepts a path, MIME, endpoint or root.

- [ ] **Step 3: Implement direct/MCP adapters and server tools**

Read tools delegate to `DocumentService`; sync delegates to caller-owned
`DocumentSyncService`; index delegates to targeted `DocumentIndexingService`.
Wrap only writes in `IntegrationActionService`. Successful reads/writes audit
safe IDs/counts only. Reuse the common root mount so the SDK's internal `/mcp`
route is exposed exactly once at public `/mcp`, with no `/mcp/mcp` nesting.

- [ ] **Step 4: Implement gateway and compatible routes**

Company-scoped lists and document-by-ID reads use the gateway. The unscoped list
remains the audited direct compatibility path. Preserve `DocumentSummaryRead`,
`DocumentRead`, 404 behavior and current response bodies.

- [ ] **Step 5: Run document boundary tests**

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/documents tests/integration/mcp/test_document_mcp.py tests/integration/mcp/test_document_sync.py tests/integration/mcp/test_document_indexing.py tests/integration/mcp/test_route_compatibility.py -q
```

Expected all pass.

---

### Task 11: Implement real integration health and optional Compose sidecars

**Files:**
- Modify: `apps/api/app/api/routes_health.py`
- Modify: `apps/api/app/api/routes_integrations.py`
- Modify: `apps/api/app/schemas/integration.py`
- Create or modify: `apps/api/app/services/integration_health_service.py`
- Modify: `apps/api/Dockerfile`
- Create: `docker-compose.mcp.yml`
- Modify: `docker-compose.yml`
- Modify: `Makefile`
- Test: `apps/api/tests/integration/mcp/test_health_and_audit.py`
- Modify: `apps/api/tests/integration/test_health.py`

- [ ] **Step 1: Write failing health tests**

Assert direct mode probes only database/service and reports `ok/direct` without
MCP initialization. MCP mode performs initialize/discover; healthy is `ok`; MCP
failure with direct fallback is `degraded`; fallback disabled/direct failure is
`unavailable`; missing endpoint or enabled writes without key is
`not_configured`; CRM/documents are independent; details are safe categories,
not endpoints/exceptions. Constructing settings with writes enabled and a
missing/short key must succeed; the health result, approval issuance and write
call—not application startup—enforce `not_configured`.

- [ ] **Step 2: Implement async health service and thin routes**

Keep `/health` and `/ready` behavior. Move integration assembly to a focused
service with injected gateways/clients for tests. `/api/integrations/health`
awaits it and preserves the existing component schema; only safe `mode/detail`
values change.

- [ ] **Step 3: Add the optional Compose override**

`docker-compose.mcp.yml` adds `crm-mcp` and `documents-mcp`, each using the API
build, its own uvicorn command/port/healthcheck, API-healthy dependency and the
same database. It overrides API modes/endpoints only when the file is used. Mount
`./data:/data:ro`; use `/data/egnyte_mock`; do not add a signing key value.

Base `docker-compose.yml` remains direct and starts no sidecar. Dockerfile copies
`mcp_servers`. Add Make targets that require an explicit M4 test DB URL for
approval/status operations; do not default to the developer DB.

- [ ] **Step 4: Validate Compose rendering and health tests**

```bash
docker compose config --quiet
docker compose -f docker-compose.yml -f docker-compose.mcp.yml config --quiet
cd apps/api
.venv/bin/python -m pytest tests/integration/test_health.py tests/integration/mcp/test_health_and_audit.py -q
```

Expected both configurations render; tests pass without external network.

---

### Task 12: Update migration-head consumers and complete affected integration regressions

**Files:**
- Modify: `apps/api/scripts/seed_data.py`
- Modify: `apps/api/scripts/index_documents.py`
- Modify: `apps/api/scripts/sync_news.py`
- Modify: `apps/api/scripts/extract_triggers.py`
- Modify: `apps/api/tests/integration/seed/test_seed_data.py`
- Modify: `apps/api/tests/integration/news/test_cli.py`
- Modify: other exact-head assertions found by `rg`
- Complete: all `apps/api/tests/integration/mcp/` suites

- [ ] **Step 1: Find and update every current-head assertion**

```bash
rg -n "0004_milestone3_news_triggers" apps/api --glob '*.py'
```

Update runtime/current-head checks to `0005_milestone4_mcp_boundaries`. Preserve
intentional migration references to 0004 in downgrade/upgrade tests.

- [ ] **Step 2: Run affected legacy boundaries**

```bash
cd apps/api
.venv/bin/python -m pytest tests/integration/db tests/integration/seed tests/integration/news tests/integration/triggers tests/integration/api/test_core_routes.py -q
```

Expected all prior M1–M3 behavior passes on the M4 head.

- [ ] **Step 3: Run the complete M4 unit and integration groups**

```bash
cd apps/api
.venv/bin/python -m pytest tests/unit/mcp tests/unit/crm tests/unit/documents -q
.venv/bin/python -m pytest tests/integration/mcp -q
```

Expected zero failures/skips. Record exact counts for status documentation.

- [ ] **Step 4: Inspect audit/log redaction explicitly**

Use sentinel note/document/token/exception strings in tests. Query `audit_logs`
and capture test logs; assert none contains the full sentinel, token, signing key,
endpoint or raw exception. Assert approved safe digests/counts/IDs are present.

---

### Task 13: Run the isolated full-stack M4 gate

**Files:**
- No production edits unless the gate exposes a defect.
- Temporary outputs: `/private/tmp` only; never repository secrets or model files.

- [ ] **Step 1: Create an isolated disposable Compose project**

Use distinct project name, database names containing `test`, host ports and
volume. Build API/Web/sidecars with the MCP override. Configure a test-only
32+ character signing key through the command environment, never a tracked file.
Migrate/seed the isolated database explicitly.

- [ ] **Step 2: Prove live MCP reads and isolation**

Through the existing HTTP API, query company-scoped CRM and documents and assert
MCP-backed compatible responses. Check `/health`, `/ready` and integration health.
Stop only `crm-mcp`; verify CRM is degraded and direct fallback works while
documents remains MCP `ok`. Restart it and verify recovery.

- [ ] **Step 3: Prove fail-closed, single-use writes**

Issue a test capability through the CLI for `create_crm_note`, call the live MCP
tool, verify one row/audit/execution and reject reuse. Test tampered arguments.
Stop the server during a write call and prove no direct write occurred. Repeat
for document sync/index approval at least once.

- [ ] **Step 4: Prove document sync/index/RAG**

Sync the checked-in TXT, repeat unchanged, perform the version-only fixture
scenario, index with hashing and retrieve it through company-scoped RAG. Assert
no duplicate documents/chunks, chunk IDs/vectors survive version-only refresh
and the citation references the new document.

- [ ] **Step 5: Inspect services, database, logs and teardown**

Record health states, row/count invariants and audit categories. Search API and
sidecar logs for test token/full note/full document/signing key and require no
match. Tear down only the disposable project/volume. Confirm default Compose
services and the repository worktree are unchanged.

Any failed probe stops later work. Diagnose, fix, rerun targeted tests, then
rerun this full gate from a fresh disposable project.

---

### Task 14: Execute the mandatory M4 checkpoint, synchronize docs and commit

**Files:**
- Modify: `docs/FINAL_IMPLEMENTATION_PLAN.md`
- Modify: `docs/ARCHITECTURE_DECISIONS.md`
- Modify: `docs/IMPLEMENTATION_STATUS.md`
- Modify: `README.md`
- Modify: `README_ZH.md`
- Review: every M4 changed/untracked file

- [ ] **Step 1: Run targeted and complete backend tests**

Run the exact M4 unit/integration commands from Task 12, then:

```bash
cd apps/api
.venv/bin/python -m compileall -q app scripts alembic mcp_servers tests
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest --cov=app --cov=mcp_servers --cov-report=term-missing -q
.venv/bin/python -m pip check
```

Expected: every test passes, zero required skips, coverage does not regress below
the recorded 89% without a documented and owner-approved reason. The final test
count must be recorded, not predicted.

- [ ] **Step 2: Run migration and frontend/build gates**

Run the isolated 0005 downgrade/upgrade/check matrix, then:

```bash
make lint
cd apps/web
pnpm exec tsc --noEmit
pnpm build
cd ../..
docker compose config --quiet
docker compose -f docker-compose.yml -f docker-compose.mcp.yml config --quiet
docker compose build api web
docker compose -f docker-compose.yml -f docker-compose.mcp.yml build crm-mcp documents-mcp
```

Use approved sandbox exceptions if local PostgreSQL or Turbopack internal ports
are blocked. Environmental failures are rerun and documented, never waived.

- [ ] **Step 3: Update authoritative and public documentation from evidence**

Mark M4 complete only after all gates pass. Add ADRs for independent Streamable
HTTP sidecars, read fallback/write fail-closed policy, CLI single-use approval
capabilities and explicit-inactive document lifecycle. Record exact commands,
counts, failures/fixes/skips and limitations in `IMPLEMENTATION_STATUS.md`.
Synchronize both READMEs as public overviews; do not treat them as specifications.
State M5 has not started.

- [ ] **Step 4: Run final diff and secret/scope review**

```bash
git diff --check
git status --short
git diff --name-status
git diff --stat
```

Inspect every untracked file. Search changed content for secrets, test capability
tokens, signing keys, personal paths, full sensitive fixture text, TODO/FIXME,
dead code and unrelated edits. Require no tracked deletion unless explicitly
planned. Stage only reviewed M4 files, then run `git diff --cached --check`,
cached name/status/stat/deletion and secret/dead-code/scope scans.

- [ ] **Step 5: Create the single M4 implementation commit**

Only after every prior step is green:

```bash
git commit -m "feat: complete milestone 4 mcp boundaries"
git status --short
git log -3 --oneline --decorate
```

Expected: commit succeeds on `main`, worktree is clean, M4 status evidence is
committed and M5 remains unstarted.
