# Public Repository Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a normal-push-ready public `main` containing the checkpoint-verified Milestone 3 snapshot, accurate READMEs, no local secrets/artifacts, and all required frontend source, while restoring unfinished Milestone 4 work locally without content loss.

**Architecture:** Treat the publishable Git tree and the local Milestone 4 worktree as separate artifacts. Build and validate the public tree while M4 is protected outside the worktree, replace all unpublished descendants of `origin/main` with one sanitized M3 snapshot commit, then restore M4 with binary-diff and SHA-256 equality gates. Work directly on `main` as required by `AGENTS.md`; do not push in this plan.

**Tech Stack:** Git 2.54, Markdown, Next.js 16/TypeScript/pnpm, FastAPI/Python 3.12/pytest, Alembic, PostgreSQL 16, Docker Compose, POSIX archive/hash tools.

---

## File responsibility map

### Create

- `docs/superpowers/plans/2026-07-16-public-repository-preparation.md`: this execution plan.
- `apps/web/src/lib/api.ts`: tracked M3 frontend API contracts/client required by committed pages.
- `apps/web/src/lib/utils.ts`: tracked Tailwind class-name helper.
- `apps/web/src/lib/mock-data.ts`: tracked deterministic UI mock types/data retained by the M3 frontend.
- `/private/tmp/pe-agent-public-prep-*`: local-only recovery bundle, binary diff, untracked archive, manifests and validation worktree; never stage or push.

### Modify

- `.gitignore`: public-repository ignore rules and the `apps/web/src/lib/` source exception.
- `apps/api/alembic.ini`: replace the real local password with the exact public placeholder.
- `README.md`: concise English recruiter/developer landing page for the verified M3 snapshot.
- `README_ZH.md`: detailed Chinese verified product overview and setup guide.
- `apps/web/README.md`: replace create-next-app boilerplate with repository-specific frontend documentation.
- `docs/IMPLEMENTATION_STATUS.md`: distinguish local M4 WIP from the verified public M3 snapshot and record publication-gate evidence.
- `docs/superpowers/specs/2026-07-14-milestone-2-semantic-rag-design.md`: replace an owner-specific external-cache path with generic wording.
- `docs/superpowers/plans/2026-07-14-milestone-3-news-trigger.md`: replace an owner-specific master-prompt path with authority-only wording.
- `docs/superpowers/plans/2026-07-14-milestone-4-mcp-boundaries.md`: replace an owner-specific master-prompt path with authority-only wording.

### Remove from tracking and unpublished history

- `.DS_Store`
- `apps/.DS_Store`
- `data/.DS_Store`
- `.vscode/settings.json`

### Preserve locally but exclude from the public commit

- all current tracked/untracked Milestone 4 changes shown by `git status --short`;
- `data/egnyte_mock/` and `docker-compose.mcp.yml` (M4 fixtures/config);
- `output/` (role-specific CV source/PDF and generated artifacts);
- the ignored real `.env` and `apps/web/.env.local`.

This plan file must be reviewed and committed before Task 1. It is therefore
not part of the untracked M4 baseline or an allowed untracked-to-tracked
transition during recovery.

## Task 1: Capture a content-safe recovery baseline

**Files:**
- Read: current worktree and Git metadata.
- Create outside repository: `/private/tmp/pe-agent-public-prep-*` recovery artifacts.

- [ ] **Step 1: Record immutable starting refs and status**

Run:

```bash
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
git merge-base --is-ancestor origin/main HEAD
git status --short
```

Expected: branch `main`; ancestor check exits 0; record the two commit IDs in the operator log.

- [ ] **Step 2: Save the tracked M4 delta losslessly**

Run Git's native binary-safe output, excluding the modified tracked macOS
metadata that will be intentionally removed:

```bash
git diff --binary --output=/private/tmp/pe-agent-public-prep-tracked.patch -- . ':!.DS_Store' ':!apps/web/src/lib/api.ts' ':!apps/web/src/lib/utils.ts' ':!apps/web/src/lib/mock-data.ts'
shasum -a 256 /private/tmp/pe-agent-public-prep-tracked.patch
```

Expected: non-empty patch and one SHA-256.

- [ ] **Step 3: Archive and hash the ignored frontend library before reconstruction**

Create a NUL-delimited list containing only the three paths, archive it with
`tar --null -T`, list the resulting archive, and record path/content SHA-256
values. Assert the archive contains exactly those three files and no `.env` or
`output/` member.

Run:

```bash
printf '%s\0' apps/web/src/lib/api.ts apps/web/src/lib/utils.ts apps/web/src/lib/mock-data.ts > /private/tmp/pe-agent-public-frontend-lib.nul
tar --null -T /private/tmp/pe-agent-public-frontend-lib.nul -czf /private/tmp/pe-agent-public-frontend-lib.tgz
tar -tzf /private/tmp/pe-agent-public-frontend-lib.tgz
while IFS= read -r -d '' file; do shasum -a 256 "$file"; done < /private/tmp/pe-agent-public-frontend-lib.nul
```

Expected: three archived files and three content hashes.

- [ ] **Step 4: Archive and hash every untracked M4 file**

Generate a raw NUL-delimited list with
`git ls-files --others --exclude-standard -z`. Produce a second M4-only list by
removing `output/` and the three separately archived frontend-library paths.
The already committed plan must not appear. Use `tar --null -T` to create the
archive, verify its member list, and generate a NUL-safe sorted SHA-256 manifest
whose records contain both digest and repository-relative path.

Run an explicit filter equivalent to:

```bash
git ls-files --others --exclude-standard -z > /private/tmp/pe-agent-public-untracked-raw.nul
while IFS= read -r -d '' file; do
  case "$file" in
    output/*|apps/web/src/lib/api.ts|apps/web/src/lib/utils.ts|apps/web/src/lib/mock-data.ts) ;;
    *) printf '%s\0' "$file" ;;
  esac
done < /private/tmp/pe-agent-public-untracked-raw.nul > /private/tmp/pe-agent-public-untracked-m4.nul
tar --null -T /private/tmp/pe-agent-public-untracked-m4.nul -czf /private/tmp/pe-agent-public-untracked-m4.tgz
while IFS= read -r -d '' file; do
  digest=$(shasum -a 256 "$file" | awk '{print $1}')
  printf '%s  %s\0' "$digest" "$file"
done < /private/tmp/pe-agent-public-untracked-m4.nul > /private/tmp/pe-agent-public-untracked-m4.sha256.nul
```

List the tar archive and assert its path set exactly matches the NUL list.
Hash the archive itself as a second integrity check.

Expected: the manifest covers every untracked M4 source/test/migration/fixture/Compose file and contains no `.env`, `output/`, model cache or CV path.

- [ ] **Step 5: Create a local history recovery bundle**

Run:

```bash
git bundle create /private/tmp/pe-agent-public-prep-before.bundle main
git bundle verify /private/tmp/pe-agent-public-prep-before.bundle
shasum -a 256 /private/tmp/pe-agent-public-prep-before.bundle
```

Expected: bundle verification succeeds. Never add this bundle to Git.

## Task 2: Repair the publishable source and ignore boundary

**Files:**
- Modify: `.gitignore`
- Modify: `apps/api/alembic.ini`
- Create/track: `apps/web/src/lib/api.ts`
- Create/track: `apps/web/src/lib/utils.ts`
- Create/track: `apps/web/src/lib/mock-data.ts`
- Remove: `.DS_Store`, `apps/.DS_Store`, `data/.DS_Store`, `.vscode/settings.json`

- [ ] **Step 1: Update root ignore rules**

Add scoped rules for environment overrides (with `!.env.example`), `/output/`, editor/OS artifacts, local DB/key/log files and model artifacts. Add explicit exceptions:

```gitignore
!apps/web/src/lib/
!apps/web/src/lib/**
```

Do not ignore `data/seed/` or `data/egnyte_mock/` by category.

- [ ] **Step 2: Verify ignore behavior before staging**

Run:

```bash
git check-ignore -v .env apps/web/.env.local output/
git check-ignore -v apps/web/src/lib/api.ts
```

Expected: the first command identifies ignore rules; the second exits 1 with no output because source must be trackable.

- [ ] **Step 3: Replace the Alembic password deterministically**

Set exactly:

```ini
sqlalchemy.url = postgresql+psycopg://pe_agent:replace-with-a-local-password@localhost:5432/pe_agent_db
```

Do not modify or inspect the real `.env`.

- [ ] **Step 4: Reconstruct the M3 frontend library**

Review current exports against committed M3 imports and backend M3 response shapes. Track only the current M3 API client/types and generic helpers; reject any MCP/action-approval/document-sync symbols. Force-add the files only if the corrected ignore rule has not yet been staged.

- [ ] **Step 5: Remove local metadata from tracking**

Remove the three `.DS_Store` files and `.vscode/settings.json`. Preserve no editor-specific replacement.

- [ ] **Step 6: Validate the repaired source boundary**

Run:

```bash
git ls-files apps/web/src/lib
git status --short
git diff --check
```

Expected: exactly the three library files are trackable/staged later; no whitespace errors.

## Task 3: Synchronize public documentation

**Files:**
- Modify: `README.md`
- Modify: `README_ZH.md`
- Modify: `apps/web/README.md`
- Modify: `docs/IMPLEMENTATION_STATUS.md`
- Modify: `docs/superpowers/specs/2026-07-14-milestone-2-semantic-rag-design.md`
- Modify: `docs/superpowers/plans/2026-07-14-milestone-3-news-trigger.md`
- Modify: `docs/superpowers/plans/2026-07-14-milestone-4-mcp-boundaries.md`

- [ ] **Step 1: Rewrite the English landing page**

Keep it concise and recruiter-facing. Include verified M3 product value, current architecture, UI/API surface, mock/offline safety, quick start, 154-test/89%-coverage checkpoint evidence, limitations, screenshot/demo guidance, and links to Chinese/authoritative documents. State that M4 has an approved design and local WIP but is not in the public snapshot or a completed capability.

- [ ] **Step 2: Update the detailed Chinese overview**

Synchronize product pages, M3 capabilities, data flow, setup, safety, limitations, milestone roadmap and public-snapshot wording. Do not advertise MCP implementation, LangGraph, real enterprise integrations or email sending as complete.

- [ ] **Step 3: Replace the frontend boilerplate README**

Document pnpm commands, `.env.local` API base URL, available routes, backend dependency, frontend structure, lint/type/build validation and the current absence of a dedicated component/browser test suite.

- [ ] **Step 4: Correct authoritative status wording**

Change the M4 ledger entry from “Not started” to “Local implementation in progress — checkpoint incomplete; excluded from public M3 snapshot.” Add a public-preparation section with the ignore/source/history findings and pending validation commands. Keep M3 as the last completed gate.

Remove or relabel every stale pre-squash local commit ID in the status document;
the public snapshot must not point readers to objects that are retained only in
the local recovery bundle.

- [ ] **Step 5: Sanitize owner-specific documentation paths**

Replace owner-home/removable-volume paths in the M2 design, M3 plan, M4 plan and
status document with generic `owner-supplied` or
`/absolute/path/outside/this/repository` wording. Scan all tracked Markdown,
not only these known files, before staging.

- [ ] **Step 6: Validate documentation locally**

Check all relative Markdown links exist; verify the two root READMEs cross-link; scan for contradictory `M4 has not started`, unsupported `253 tests`, `MCP complete`, personal paths and the real password.

## Task 4: Commit only the public M3 preparation changes

**Files:**
- Stage only files listed in Tasks 2–3 plus this plan/spec as already committed.
- Exclude all M4 implementation files.

- [ ] **Step 1: Review the exact candidate set**

Run `git status --short`, `git diff --name-only`, and `git diff --stat`. Compare every candidate path with the file responsibility map.

- [ ] **Step 2: Stage an explicit allowlist**

Use explicit `git add`/`git rm` paths. Never use `git add .` or `git add -A` while M4 is present.

- [ ] **Step 3: Inspect the cached diff**

Run:

```bash
git diff --cached --check
git diff --cached --name-status
git diff --cached --stat
```

Scan added lines for passwords, tokens, private-key markers, personal absolute paths, CV content, M4-only symbols and accidental deletion.

- [ ] **Step 4: Commit the public preparation**

Commit with a documentation/security-oriented message. This commit does not claim M4 completion.

## Task 5: Protect M4 and replace unpublished history with one clean snapshot

**Files:**
- Git metadata and recovery artifacts only while M4 is stashed.

- [ ] **Step 1: Stash the remaining M4 work without ignored personal artifacts**

Run `git stash push --include-untracked` after confirming `/output/` is ignored. Record the stash object ID. Confirm the worktree is clean.

- [ ] **Step 2: Protect the completed public-preparation commit separately**

Record the pre-rewrite `main` commit, create and verify a second recovery bundle
containing it, and confirm the original M4 stash object remains available. If a
later step fails before the new snapshot is committed, return to this commit
only after the worktree is clean and the stash remains intact.

- [ ] **Step 3: Replace only local descendants with one sanitized snapshot**

With M4 stashed and the worktree clean, run `git reset --soft origin/main`,
inspect the complete staged tree, and commit it once as the verified M3 public
snapshot. This discards only unpublished commit topology; all retained source,
tests and documentation remain in the snapshot.

Expected: `origin/main` is unchanged and the new snapshot is its direct child.

- [ ] **Step 4: Confirm normal-push topology**

Run:

```bash
git rev-parse origin/main
git merge-base --is-ancestor origin/main main
git log --reverse --oneline origin/main..main
```

Expected: recorded `origin/main` unchanged; ancestor check exits 0;
`git rev-list --count origin/main..main` reports `1`; normal push remains
possible.

- [ ] **Step 5: Scan every to-be-pushed commit and blob**

Use `git rev-list --objects origin/main..main`, `git cat-file --batch-check`,
`git ls-tree -r`, and `git grep` against the exact snapshot to enumerate every
object name, blob size and text candidate. Any known local-password match,
private-key block, owner-specific home/removable-volume path, tracked
`.DS_Store`, `.vscode/settings.json`, `output/`, real `.env`, M4
code/fixtures/Compose overlay, or blob at least 5 MiB fails the gate. Allow only
documented placeholders, empty commented provider keys and the test digest
`abcdef0123456789`. Store the known secret/path scan needles only in the
operator process or recovery area, never in a tracked file.

Fail closed with commands equivalent to:

```bash
test -n "$PUBLIC_SCAN_DB_PASSWORD"
test -n "$PUBLIC_SCAN_HOME_PREFIX"
git rev-list --objects origin/main..main > /private/tmp/pe-agent-public-objects.txt
git cat-file --batch-check='%(objecttype) %(objectsize) %(rest)' < /private/tmp/pe-agent-public-objects.txt > /private/tmp/pe-agent-public-object-sizes.txt
! awk '$1 == "blob" && $2 >= 5242880 {print; found=1} END {exit found ? 0 : 1}' /private/tmp/pe-agent-public-object-sizes.txt
! git grep -I -n -F "$PUBLIC_SCAN_DB_PASSWORD" main -- .
! git grep -I -n -F "$PUBLIC_SCAN_HOME_PREFIX" main -- .
! git log --format='%H%n%an%n%ae%n%B' origin/main..main | rg -F "$PUBLIC_SCAN_HOME_PREFIX"
! git ls-tree -r --name-only main | rg '(^|/)(\.DS_Store|\.vscode/|output/|\.env$|docker-compose\.mcp\.yml$)'
```

Also scan for private-key headers, credential assignment candidates and the
runtime-supplied removable-volume prefix. Review public placeholders through a
small explicit allowlist; any remaining candidate exits nonzero.

## Task 6: Run the clean publishable-tree gate

**Files:**
- Detached temporary worktree at the exact sanitized commit.
- Modify after first run: `docs/IMPLEMENTATION_STATUS.md` only.

- [ ] **Step 1: Create a detached validation worktree**

Create it under `/private/tmp` from `main`. Verify `git status --short` is empty and all three frontend library files are tracked.

Link only dependency directories from the original workspace into the detached
tree:

```bash
ln -s <original-workspace>/apps/api/.venv apps/api/.venv
ln -s <original-workspace>/apps/web/node_modules apps/web/node_modules
```

These ignored dependency-only links permit offline validation but cannot supply
source files.

- [ ] **Step 2: Assert publication scope**

Assert the clean tree has no `0005` migration, M4 integration/action services, M4 tests, `data/egnyte_mock/`, `docker-compose.mcp.yml`, `output/`, `.env`, OS metadata or editor settings.

- [ ] **Step 3: Run M3 backend and migration regression**

Using two newly created disposable PostgreSQL databases named
`pe_agent_public_snapshot_app_test` and `pe_agent_public_snapshot_test`, set
`DATABASE_URL` and `TEST_DATABASE_URL` explicitly in the command environment.
Do not source/read the real `.env`. Stop if either database already exists;
create them through the running PostgreSQL container and remove only these two
databases after both validation cycles.

Discover the running PostgreSQL container without invoking Compose (which would
implicitly load the real `.env`). Use `docker ps` with both exact labels
`com.docker.compose.project=private-equity-target-monitoring-agent` and
`com.docker.compose.service=postgres`, require exactly one running result, and
store its ID in `PUBLIC_POSTGRES_CONTAINER`. All database create/check/drop
commands use `docker exec` against that recorded container, independent of the
detached worktree's Compose project resolution. Before creation, query
`pg_database`; if either name exists, stop rather than dropping it. Create both
with `createdb -U pe_agent`.

Set the known local password only in the operator process as
`PUBLIC_DB_PASSWORD` and construct both explicit localhost URLs from it; never
source/read `.env`. Install an EXIT/INT/TERM cleanup handler immediately after
creation that terminates connections only to those two exact database names and
runs `dropdb -U pe_agent` for them. The cleanup runs after success or failure.
The owner approved this disposable test-database lifecycle through the reviewed
design.

Run exactly:

```bash
cd apps/api && .venv/bin/python -m compileall -q app scripts alembic tests
cd apps/api && .venv/bin/python -m pytest --cov=app --cov-report=term-missing -q
cd apps/api && .venv/bin/alembic upgrade head
cd apps/api && .venv/bin/alembic downgrade 0003_milestone2_vector_cohorts
cd apps/api && .venv/bin/alembic upgrade head
cd apps/api && .venv/bin/alembic check
```

Expected: 154 tests pass, 0 fail, 0 required skip, 89% line coverage, and no
schema drift. All database commands use the disposable URLs explicitly.

- [ ] **Step 4: Run frontend and Compose validation**

Run:

```bash
make lint
cd apps/web && pnpm exec tsc --noEmit
cd apps/web && pnpm build
docker compose config --quiet
git diff --check
```

Expected: all exit 0; 12 routes generate; no ignored local source is needed.

- [ ] **Step 5: Smoke-check README instructions**

Validate commands/configuration with disposable variables or a temporary `.env.example` copy only. Do not read the real `.env`.

- [ ] **Step 6: Record evidence and amend the sanitized snapshot**

Update `docs/IMPLEMENTATION_STATUS.md` with exact clean-tree commands and
pass/fail/skip counts. Stage only that file and amend the single sanitized
snapshot commit without changing its message. Verify
`git rev-list --count origin/main..main` remains `1`.

- [ ] **Step 7: Recreate the worktree from the new final commit and rerun the full gate**

Remove the first validation worktree, create a new detached one from final `main`, and repeat Steps 1–5 plus deterministic history/secret/link/large-file scans. No tracked change follows this final run.

## Task 7: Restore M4 and prove byte-equivalent recovery

**Files:**
- Restore the recorded stash/untracked files into the main worktree.

- [ ] **Step 1: Apply, do not pop, the recorded stash**

Run `git stash apply <recorded-stash-id>`. If any conflict occurs, run
`git reset --merge` only to abort the failed apply while the stash remains,
verify the clean public snapshot, and stop for owner review; do not overwrite
the archived M4 baseline.

- [ ] **Step 2: Restore any ignored frontend-library M4-only delta**

Compare the public M3 versions with the separately archived originals. Restore only a proven local M4 delta; do not overwrite the newly tracked M3 baseline blindly.

- [ ] **Step 3: Compare tracked and untracked content**

Generate a new binary diff with the same exclusion and require its SHA-256 to
equal the original tracked-M4 patch. Regenerate the NUL-safe M4-only untracked
manifest and require byte-for-byte equality with the original. Compare the three
frontend-library originals separately: the tracked public M3 versions must
equal their archived hashes unless a separately documented M4-only delta was
identified before Task 2. The three library paths remain excluded from both
tracked-patch generations; their restoration is proven only by their separate
path/content hash manifest. No other set transition is allowed.

- [ ] **Step 4: Keep recovery artifacts and stash**

Do not drop the stash or delete the bundle/archive. Report their local paths and IDs so the owner can retain them until after the first successful GitHub push.

- [ ] **Step 5: Final push-readiness report**

Report final `main` commit, unchanged `origin/main`, ahead count, exact normal push command, committed public scope, remaining local M4 changes and all validation results. Do not run `git push`.
