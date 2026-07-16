# GitHub Actions Python Interpreter Compatibility Fix

## Context

The first public GitHub Actions run for commit `3725a23` completed frontend
validation successfully, but the backend job reported one failure and 153
passes. The sole failure was
`tests/integration/news/test_cli.py::test_cli_entrypoints_expose_safe_persisted_scope_only`.
The test starts two CLI help commands through a repository-local
`apps/api/.venv/bin/python` path. That path exists in the developer workspace
but is not created by `actions/setup-python`, so the Ubuntu runner raises
`FileNotFoundError` before either CLI is executed.

## Options considered

1. **Use `sys.executable` in the test (selected).** The subprocess uses the
   exact interpreter that is running pytest. This is portable across local
   virtual environments, GitHub-hosted Python, containers and other operating
   systems, while preserving the purpose of the integration test.
2. **Resolve `python` from `PATH`.** This avoids a repository-local path but can
   select an interpreter different from the one running pytest, including one
   without the installed project dependencies.
3. **Create `.venv` in GitHub Actions.** This makes the current test pass but
   encodes a local directory convention into CI and leaves the test needlessly
   environment-specific.

## Design

Import `sys` in `tests/integration/news/test_cli.py` and replace both hard-coded
interpreter arguments with `sys.executable`. Do not change the CLI modules,
their flags, the workflow file, dependencies, database schema or runtime
behavior. Search the test tree for other repository-local interpreter paths;
none may remain after the repair.

The current Milestone 4 work stays unstaged and uncommitted. Only this test,
this design/plan evidence and the applicable implementation-status record may
enter the CI repair commit.

## Validation

1. Create the candidate commit from an explicit allowlist containing only the
   reviewed CI repair and its documentation. Do not run or claim the complete
   gate from the dirty M4 worktree.
2. Create a detached worktree at the exact candidate commit and run the affected
   CLI integration test there.
3. In that clean worktree, run the complete backend regression with coverage
   against an isolated test database; expect 154 passes, zero failures/skips
   and 89% line coverage.
4. In the same clean worktree, compile backend source/tests and run frontend
   lint, TypeScript and production-build regression because the repository
   checkpoint policy applies to every committed repair.
5. Run Compose configuration validation, repository/security scope checks and
   `git diff --check` against the exact candidate commit.
6. Record the exact gate evidence in `docs/IMPLEMENTATION_STATUS.md`, stage only
   that file and amend the candidate commit. Recreate the detached worktree at
   the amended commit and rerun Steps 2–5 in full; no tracked change may follow
   this final run.
7. Confirm a normal push using `git push --dry-run`; do not perform the real
   push without the owner's instruction.

No Alembic migration is added, so migration upgrade/downgrade validation is not
applicable to the change itself. The full backend regression continues to run
the existing migration tests.
