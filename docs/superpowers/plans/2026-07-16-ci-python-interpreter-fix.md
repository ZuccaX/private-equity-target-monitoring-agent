# GitHub Actions Python Interpreter Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the CLI integration test portable so the same 154-test backend suite passes locally and on GitHub-hosted Ubuntu runners.

**Architecture:** The test subprocesses inherit the interpreter running pytest through `sys.executable`; no CI-specific virtual environment or runtime code changes are introduced. Candidate and final validation run from detached exact-commit worktrees so unfinished local Milestone 4 files cannot affect evidence or enter the commit.

**Tech Stack:** Python 3.12, pytest 9, subprocess, FastAPI backend tests, PostgreSQL/pgvector, GitHub Actions, Git detached worktrees.

---

## File responsibility map

- Modify `apps/api/tests/integration/news/test_cli.py`: use the active pytest
  interpreter for both CLI subprocess probes.
- Create `docs/superpowers/specs/2026-07-16-ci-python-interpreter-fix-design.md`:
  reviewed design and rejected alternatives.
- Create `docs/superpowers/plans/2026-07-16-ci-python-interpreter-fix.md`: exact
  implementation and validation sequence.
- Modify `docs/IMPLEMENTATION_STATUS.md`: record the GitHub failure, root cause,
  corrective commands, results and remaining limitations after the first clean
  gate.
- Preserve without staging: all existing tracked/untracked Milestone 4 work.

## Task 1: Apply the portable interpreter repair

**Files:**
- Modify: `apps/api/tests/integration/news/test_cli.py:1-24`

- [ ] **Step 1: Confirm the failure contract and scope**

Verify the supplied GitHub log reports exactly one failure caused by the
missing `apps/api/.venv/bin/python`, with 153 other tests passing. Search the
test tree for all hard-coded repository-local interpreter paths:

```bash
rg -n 'API_ROOT / "\.venv"|\.venv.*/bin.*/python' apps/api/tests
```

Expected: only two matches in `tests/integration/news/test_cli.py`.

- [ ] **Step 2: Make the minimal test change**

Add `import sys` and change both subprocess argument lists from:

```python
str(API_ROOT / ".venv" / "bin" / "python")
```

to:

```python
sys.executable
```

Do not modify the CLI modules, CI workflow or dependency files.

- [ ] **Step 3: Inspect the exact repair diff**

```bash
git diff --check -- \
  apps/api/tests/integration/news/test_cli.py \
  docs/superpowers/specs/2026-07-16-ci-python-interpreter-fix-design.md \
  docs/superpowers/plans/2026-07-16-ci-python-interpreter-fix.md
git diff -- apps/api/tests/integration/news/test_cli.py
```

Expected: one import and two interpreter substitutions; no M4 path staged.

## Task 2: Create and inspect the candidate commit

**Files:**
- Stage only the test, design and plan listed above.

- [ ] **Step 1: Stage an explicit allowlist**

```bash
git add \
  apps/api/tests/integration/news/test_cli.py \
  docs/superpowers/specs/2026-07-16-ci-python-interpreter-fix-design.md \
  docs/superpowers/plans/2026-07-16-ci-python-interpreter-fix.md
```

Never use `git add .` or `git add -A` while M4 is present.

- [ ] **Step 2: Inspect the cached candidate**

```bash
git diff --cached --check
git diff --cached --name-status
git diff --cached --stat
```

Expected: exactly three paths and no secret, deletion or M4 implementation.

- [ ] **Step 3: Commit the candidate**

```bash
git commit -m "fix: use active Python interpreter in CLI test"
```

## Task 3: Run the first exact-candidate gate

**Files:**
- Detached temporary worktree at the candidate commit.
- Disposable test databases only.

Run Task 3 Steps 1–5 as one `set -e` persistent shell session. The separate
code fences are for readability only. Variables and the cleanup trap must stay
active until every candidate check finishes. If the shell is lost, confirm both
dedicated database names are absent and restart the gate.

- [ ] **Step 1: Create a detached worktree and offline dependencies**

Capture the immutable candidate object and create the fixed validation path:

```bash
export ORIGINAL_WORKSPACE=$(git rev-parse --show-toplevel)
export CANDIDATE_OID=$(git rev-parse main)
export CANDIDATE_WORKTREE=/private/tmp/pe-agent-ci-fix-candidate-20260716
git worktree add --detach "$CANDIDATE_WORKTREE" "$CANDIDATE_OID"
test "$(git -C "$CANDIDATE_WORKTREE" rev-parse HEAD)" = "$CANDIDATE_OID"
test -z "$(git -C "$CANDIDATE_WORKTREE" status --short)"
test ! -e "$CANDIDATE_WORKTREE/apps/api/.venv"
```

Do not add the backend venv link yet. Clone/copy `apps/web/node_modules` inside
the temporary worktree so Turbopack does not depend on source outside the
commit:

```bash
cp -cR apps/web/node_modules "$CANDIDATE_WORKTREE/apps/web/node_modules"
```

- [ ] **Step 2: Create isolated databases without reading `.env`**

Discover the running PostgreSQL container through exact Compose labels, require
one result, and use fixed candidate database names. The operator sets
`PUBLIC_DB_PASSWORD` directly in the process from the owner-provided local
password; never source or print `.env`.

```bash
export PUBLIC_POSTGRES_CONTAINER=$(docker ps \
  --filter label=com.docker.compose.project=private-equity-target-monitoring-agent \
  --filter label=com.docker.compose.service=postgres \
  --format '{{.ID}}')
test "$(printf '%s\n' "$PUBLIC_POSTGRES_CONTAINER" | sed '/^$/d' | wc -l | tr -d ' ')" = 1
export APP_DB=pe_agent_ci_fix_candidate_app_test
export TEST_DB=pe_agent_ci_fix_candidate_test
test -n "$PUBLIC_DB_PASSWORD"
```

First prove both names are absent. Only then install cleanup immediately before
the first create, so a failure during either creation cleans up only names this
gate proved it owns:

```bash
for database_name in "$APP_DB" "$TEST_DB"; do
  test -z "$(docker exec "$PUBLIC_POSTGRES_CONTAINER" psql -U pe_agent \
    -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${database_name}'")"
done
cleanup_ci_fix_databases() {
  for database_name in "$APP_DB" "$TEST_DB"; do
    docker exec "$PUBLIC_POSTGRES_CONTAINER" psql -U pe_agent -d postgres \
      -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${database_name}' AND pid <> pg_backend_pid();" >/dev/null || true
    docker exec "$PUBLIC_POSTGRES_CONTAINER" dropdb -U pe_agent \
      --if-exists "$database_name" || true
  done
}
trap cleanup_ci_fix_databases EXIT INT TERM
docker exec "$PUBLIC_POSTGRES_CONTAINER" createdb -U pe_agent "$APP_DB"
docker exec "$PUBLIC_POSTGRES_CONTAINER" createdb -U pe_agent "$TEST_DB"
export ENVIRONMENT=test
export DATABASE_URL="postgresql+psycopg://pe_agent:${PUBLIC_DB_PASSWORD}@localhost:5432/${APP_DB}"
export TEST_DATABASE_URL="postgresql+psycopg://pe_agent:${PUBLIC_DB_PASSWORD}@localhost:5432/${TEST_DB}"
```

- [ ] **Step 3: Run targeted and complete backend tests**

First run the affected test with the original workspace's active interpreter
while the detached source has no `.venv`. This prevents the validation setup
from masking a remaining hard-coded repository-local interpreter path:

```bash
cd "$CANDIDATE_WORKTREE/apps/api"
"$ORIGINAL_WORKSPACE/apps/api/.venv/bin/python" -m pytest \
  tests/integration/news/test_cli.py::test_cli_entrypoints_expose_safe_persisted_scope_only -q
test ! -e .venv
```

Only after that pass, add the ignored dependency link required by stable
Makefile commands and run the full gate:

```bash
ln -s "$ORIGINAL_WORKSPACE/apps/api/.venv" .venv
.venv/bin/python -m compileall -q app scripts alembic tests
.venv/bin/python -m pytest --cov=app --cov-report=term-missing -q
```

Expected: 1 targeted pass; 154 complete passes; zero failures/skips; 89% line
coverage.

- [ ] **Step 4: Run affected-boundary and build regression**

```bash
cd "$CANDIDATE_WORKTREE"
make lint
cd apps/web && pnpm exec tsc --noEmit
pnpm build
cd ../..
docker compose --env-file /dev/null config --quiet
git diff --check HEAD^
git status --short
```

Run the production build outside the restricted sandbox if Turbopack needs its
temporary local port. Expected: all exit 0, 12/12 routes, clean worktree.

- [ ] **Step 5: Inspect publication scope**

Run exact object/path checks from the candidate worktree:

```bash
test "$(git rev-parse HEAD)" = "$CANDIDATE_OID"
git merge-base --is-ancestor origin/main "$CANDIDATE_OID"
test "$(git diff --name-only origin/main.."$CANDIDATE_OID" | wc -l | tr -d ' ')" = 3
git diff --name-only origin/main.."$CANDIDATE_OID" | diff -u - <(printf '%s\n' \
  apps/api/tests/integration/news/test_cli.py \
  docs/superpowers/plans/2026-07-16-ci-python-interpreter-fix.md \
  docs/superpowers/specs/2026-07-16-ci-python-interpreter-fix-design.md)
! git ls-tree -r --name-only "$CANDIDATE_OID" | rg \
  '(^|/)(0005_milestone4|docker-compose\.mcp\.yml$|data/egnyte_mock/|apps/api/app/integrations/(crm|documents|mcp)/|apps/api/mcp_servers/|apps/api/tests/(integration|unit)/mcp/)'
! git grep -I -n -E -- '-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----' \
  "$CANDIDATE_OID" -- .
git diff --check origin/main.."$CANDIDATE_OID"
```

Also run fixed-string scans for the operator-supplied password, owner home
prefix and removable-volume prefix without printing those values. Any match
fails. The only committed credential assignment candidates remain documented
placeholders or CI-only values.

```bash
test -n "$PUBLIC_SCAN_DB_PASSWORD"
test -n "$PUBLIC_SCAN_HOME_PREFIX"
test -n "$PUBLIC_SCAN_VOLUME_PREFIX"
! git diff --no-ext-diff origin/main.."$CANDIDATE_OID" -- . | \
  rg -F "$PUBLIC_SCAN_DB_PASSWORD"
! git grep -I -n -F "$PUBLIC_SCAN_HOME_PREFIX" "$CANDIDATE_OID" -- .
! git grep -I -n -F "$PUBLIC_SCAN_VOLUME_PREFIX" "$CANDIDATE_OID" -- .
```

## Task 4: Record evidence and create the final commit object

**Files:**
- Modify: `docs/IMPLEMENTATION_STATUS.md`

- [ ] **Step 1: Record exact evidence**

Add a CI repair section containing the failing run/test, root cause, first-gate
commands, exact pass/fail/skip counts, build results and the fact that no schema
migration was introduced.

Before editing, prove this allowed file has no pre-existing M4 delta:

```bash
export ORIGINAL_WORKSPACE=$(git rev-parse --show-toplevel)
cd "$ORIGINAL_WORKSPACE"
git diff --quiet -- docs/IMPLEMENTATION_STATUS.md
test -z "$(git ls-files --others --exclude-standard -- docs/IMPLEMENTATION_STATUS.md)"
```

- [ ] **Step 2: Amend only the evidence file**

```bash
git add docs/IMPLEMENTATION_STATUS.md
test "$(git diff --cached --name-only)" = "docs/IMPLEMENTATION_STATUS.md"
git diff --cached --check
git diff --cached -- docs/IMPLEMENTATION_STATUS.md
git commit --amend --no-edit
```

The cached hunk review must contain only the newly written CI repair evidence;
stop on any unrelated text. Inspect the amended commit and confirm it contains
exactly the test, design, plan and implementation-status paths.

## Task 5: Rerun the complete final-commit gate

**Files:**
- A newly created detached worktree at the amended final commit.

Run Task 5 Steps 1–2 in one persistent shell session so the immutable object,
worktree path and cleanup trap remain bound to the same final gate.

- [ ] **Step 1: Recreate, do not reuse, the validation worktree**

Remove the first temporary worktree, create a fresh one from final `main`, and
recreate only the dependency links/copies. No output from the earlier candidate
worktree may be used as final evidence.

```bash
set -e
export ORIGINAL_WORKSPACE=$(git rev-parse --show-toplevel)
git worktree remove --force /private/tmp/pe-agent-ci-fix-candidate-20260716
export FINAL_OID=$(git rev-parse main)
export FINAL_WORKTREE=/private/tmp/pe-agent-ci-fix-final-20260716
git worktree add --detach "$FINAL_WORKTREE" "$FINAL_OID"
test "$(git -C "$FINAL_WORKTREE" rev-parse HEAD)" = "$FINAL_OID"
test -z "$(git -C "$FINAL_WORKTREE" status --short)"
test ! -e "$FINAL_WORKTREE/apps/api/.venv"
```

- [ ] **Step 2: Repeat the complete gate**

Run this entire block as one `set -e` persistent shell session. Set the three
scan values and database password directly in the operator process; never read
or print `.env`.

```bash
set -e
test -n "$PUBLIC_DB_PASSWORD"
test -n "$PUBLIC_SCAN_DB_PASSWORD"
test -n "$PUBLIC_SCAN_HOME_PREFIX"
test -n "$PUBLIC_SCAN_VOLUME_PREFIX"
cp -cR "$ORIGINAL_WORKSPACE/apps/web/node_modules" \
  "$FINAL_WORKTREE/apps/web/node_modules"
export PUBLIC_POSTGRES_CONTAINER=$(docker ps \
  --filter label=com.docker.compose.project=private-equity-target-monitoring-agent \
  --filter label=com.docker.compose.service=postgres \
  --format '{{.ID}}')
test "$(printf '%s\n' "$PUBLIC_POSTGRES_CONTAINER" | sed '/^$/d' | wc -l | tr -d ' ')" = 1
export APP_DB=pe_agent_ci_fix_final_app_test
export TEST_DB=pe_agent_ci_fix_final_test
for database_name in "$APP_DB" "$TEST_DB"; do
  test -z "$(docker exec "$PUBLIC_POSTGRES_CONTAINER" psql -U pe_agent \
    -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${database_name}'")"
done
cleanup_final_ci_fix_databases() {
  for database_name in "$APP_DB" "$TEST_DB"; do
    docker exec "$PUBLIC_POSTGRES_CONTAINER" psql -U pe_agent -d postgres \
      -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${database_name}' AND pid <> pg_backend_pid();" >/dev/null || true
    docker exec "$PUBLIC_POSTGRES_CONTAINER" dropdb -U pe_agent \
      --if-exists "$database_name" || true
  done
}
trap cleanup_final_ci_fix_databases EXIT INT TERM
docker exec "$PUBLIC_POSTGRES_CONTAINER" createdb -U pe_agent "$APP_DB"
docker exec "$PUBLIC_POSTGRES_CONTAINER" createdb -U pe_agent "$TEST_DB"
export ENVIRONMENT=test
export DATABASE_URL="postgresql+psycopg://pe_agent:${PUBLIC_DB_PASSWORD}@localhost:5432/${APP_DB}"
export TEST_DATABASE_URL="postgresql+psycopg://pe_agent:${PUBLIC_DB_PASSWORD}@localhost:5432/${TEST_DB}"
cd "$FINAL_WORKTREE/apps/api"
"$ORIGINAL_WORKSPACE/apps/api/.venv/bin/python" -m pytest \
  tests/integration/news/test_cli.py::test_cli_entrypoints_expose_safe_persisted_scope_only -q
test ! -e .venv
ln -s "$ORIGINAL_WORKSPACE/apps/api/.venv" .venv
.venv/bin/python -m compileall -q app scripts alembic tests
.venv/bin/python -m pytest --cov=app --cov-report=term-missing -q
cd "$FINAL_WORKTREE"
make lint
cd apps/web
pnpm exec tsc --noEmit
pnpm build
cd "$FINAL_WORKTREE"
docker compose --env-file /dev/null config --quiet
git diff --check origin/main.."$FINAL_OID"
test -z "$(git status --short)"
test "$(git rev-parse HEAD)" = "$FINAL_OID"
git merge-base --is-ancestor origin/main "$FINAL_OID"
test "$(git diff --name-only origin/main.."$FINAL_OID" | wc -l | tr -d ' ')" = 4
git diff --name-only origin/main.."$FINAL_OID" | diff -u - <(printf '%s\n' \
  apps/api/tests/integration/news/test_cli.py \
  docs/IMPLEMENTATION_STATUS.md \
  docs/superpowers/plans/2026-07-16-ci-python-interpreter-fix.md \
  docs/superpowers/specs/2026-07-16-ci-python-interpreter-fix-design.md)
! git ls-tree -r --name-only "$FINAL_OID" | rg \
  '(^|/)(0005_milestone4|docker-compose\.mcp\.yml$|data/egnyte_mock/|apps/api/app/integrations/(crm|documents|mcp)/|apps/api/mcp_servers/|apps/api/tests/(integration|unit)/mcp/)'
! git grep -I -n -E -- '-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----' \
  "$FINAL_OID" -- .
! git diff --no-ext-diff origin/main.."$FINAL_OID" -- . | \
  rg -F "$PUBLIC_SCAN_DB_PASSWORD"
! git grep -I -n -F "$PUBLIC_SCAN_HOME_PREFIX" "$FINAL_OID" -- .
! git grep -I -n -F "$PUBLIC_SCAN_VOLUME_PREFIX" "$FINAL_OID" -- .
```

Expected: targeted 1/1, complete backend 154/154 with 89% coverage, compile,
lint, typecheck, 12/12 production routes, Compose, scope, secret and whitespace
checks all pass. The EXIT trap drops only the two final repair databases.

- [ ] **Step 3: Restore push-ready local state**

Remove temporary worktrees, verify the staging area is empty and confirm the
pre-existing M4 tracked/untracked content remains present and unstaged.

- [ ] **Step 4: Verify remote fast-forward without pushing**

```bash
git push --dry-run origin main
```

Expected: a normal `main -> main` update. Report the exact real push command but
do not run it without the owner's instruction.
