# Public Repository Preparation Design

**Date:** 2026-07-16
**Status:** Owner-selected approach: publish the checkpoint-verified Milestone 3 snapshot while preserving unfinished Milestone 4 work locally.

## Goal

Prepare `main` for a public GitHub push without publishing credentials,
personal artifacts, generated files, or implementation code that has not passed
its milestone checkpoint. Keep the current Milestone 4 worktree intact so that
development can resume after the public snapshot is prepared.

## Authority and truthful public scope

The repository documentation precedence in `AGENTS.md` remains unchanged.
Public READMEs describe the last checkpoint-verified implementation: Milestones
0–3 complete and Milestone 4 designed but not yet checkpoint-complete. They do
not treat local uncommitted Milestone 4 code as a shipped capability.

The public snapshot includes committed Milestone 0–3 implementation and the
approved Milestone 4 design/plan documents. Uncommitted Milestone 4 source,
migration, tests, fixtures, and Compose changes remain local and unstaged.

`docs/IMPLEMENTATION_STATUS.md` must distinguish these two views explicitly:
Milestone 3 is the last checkpoint-verified and publishable snapshot, while
Milestone 4 implementation exists only as local work in progress, has not passed
its checkpoint, and is excluded from this publication. The READMEs use the same
wording and do not claim that Milestone 4 work has never started.

## Ignore and tracked-file policy

Update the root `.gitignore` to:

- ignore root and nested environment overrides while retaining the tracked
  `.env.example` template;
- ignore `output/`, which currently contains a role-specific CV and generated
  PDF;
- ignore macOS metadata, local editor state, logs, local databases, private-key
  formats, coverage/build caches, and common downloaded model artifacts;
- preserve source directories such as `apps/web/src/lib/` by adding an explicit
  exception to the broad Python-template `lib/` rule;
- keep deterministic repository fixtures under `data/seed/` and
  `data/egnyte_mock/` trackable.

Remove already-tracked `.DS_Store` files and the personal
`.vscode/settings.json`. Ignore rules alone are insufficient for files already
in Git history.

The ignore bug has already hidden required frontend source files:
`apps/web/src/lib/api.ts`, `apps/web/src/lib/utils.ts`, and
`apps/web/src/lib/mock-data.ts` exist locally but are absent from both the M3
commit and `HEAD`. Reconstruct and review checkpoint-appropriate M3 versions,
reject M4-only API or integration symbols, add the three files to the public
snapshot, and prove that the committed tree builds without help from ignored or
restored files.

## Credential and history sanitation

Replace the real local PostgreSQL password embedded in
`apps/api/alembic.ini` with this exact non-secret template value:

```ini
sqlalchemy.url = postgresql+psycopg://pe_agent:replace-with-a-local-password@localhost:5432/pe_agent_db
```

The real `.env` remains ignored and is not read, printed, staged, or modified.

Because the secret-bearing commits and commits containing local metadata are
ahead of `origin/main` and have not been pushed, sanitize that unpublished
history before pushing. A commit-by-commit rewrite has too many independent
introduction points to prove safe. After creating recovery artifacts, replace
all unpublished descendants with one reviewed snapshot commit on top of the
unchanged `origin/main`. The snapshot retains the complete verified M3 tree and
its implementation-status/design evidence, but not the unsafe unpublished
intermediate objects.

Before rewriting:

1. record the original branch, `HEAD`, `origin/main`, status, tracked diff and
   untracked file list;
2. create a local Git bundle of `main` under `/private/tmp` and record its
   SHA-256; the bundle is recovery-only and must never be pushed;
3. save the tracked worktree as a binary diff using Git's `--output` option;
4. separately archive and hash the currently ignored, baseline-less
   `apps/web/src/lib/api.ts`, `utils.ts`, and `mock-data.ts` before any
   reconstruction; preserve any identified M4-only delta for restoration after
   publication preparation;
5. archive every untracked M4 file outside the repository and record a SHA-256
   manifest for both paths and contents;
6. verify that ignored `.env` and `output/` are absent from all recovery
   archives.

Stash only the remaining tracked/untracked Milestone 4 work. The newly ignored
`output/` directory remains outside the stash. Restore with `stash apply`, not
`stash pop`; compare the restored binary diff and all untracked file hashes with
the pre-rewrite records, and retain the stash and bundle until every comparison
passes. If rewriting or restoration fails, reset the local branch ref to the
recorded original `HEAD`, restore from the retained stash/archive or bundle, and
stop for owner review. Drop no recovery artifact during this task.

Do not force-push: before declaring success, confirm that the unchanged recorded
`origin/main` is the direct parent of the sanitized snapshot and remains an
ancestor of `main`, so a normal push is possible.

## README responsibilities

Update every repository README:

- `README.md`: concise English landing page for international recruiters and
  developers, with product value, verified M3 capabilities, architecture,
  demo/setup, testing evidence, limitations, and links to authoritative docs;
- `README_ZH.md`: detailed Chinese product overview with the same verified
  status, fuller workflow/API/setup explanations, safety boundaries, roadmap,
  and cross-link to the English README;
- `apps/web/README.md`: replace the create-next-app boilerplate with a focused
  frontend guide covering routes, local configuration, commands, API dependency,
  and the absence of a dedicated frontend automated test suite.

No README substitutes for `docs/FINAL_IMPLEMENTATION_PLAN.md`. Exact test counts
remain the Milestone 3 checkpoint evidence (154 backend tests, 89% line
coverage) until Milestone 4 passes its own checkpoint.

## Validation and failure handling

Before declaring the repository push-ready, create a detached temporary
worktree from the sanitized `main` commit while Milestone 4 remains stashed.
All publication tests run there, so ignored or restored local files cannot mask
an incomplete public tree. Record the first complete results in
`docs/IMPLEMENTATION_STATUS.md` and amend that evidence into the single
sanitized snapshot commit. Then discard and recreate the detached worktree from
the amended final publishable commit and rerun the complete gate below. The
second run verifies the exact commit intended for push; no tracked documentation
or source change may follow it:

1. run `git diff --check` and inspect staged/unstaged scope;
2. verify `.env`, `output/`, local caches, and model artifacts are ignored;
3. verify `apps/web/src/lib/` is not ignored;
4. assert that all three required `apps/web/src/lib/` files are tracked, while
   no M4 migration/source/test/fixture, `docker-compose.mcp.yml`, or `output/`
   artifact exists in the publishable tree;
5. scan every commit and blob in the exact `origin/main..main` push revset, plus
   the final tree filenames and content, for the known local database password,
   private-key markers, credential assignments, owner-specific home/removable-
   volume paths, ignored artifacts, and files at or above 5 MiB;
6. allow only explicit public examples such as
   `replace-with-a-local-password`, empty/commented provider keys, test-only
   opaque digest `abcdef0123456789`, and documented variable names without
   values; any other candidate requires manual review;
7. verify all local README links, cross-links and authority statements;
8. run backend compilation, the exact M3 154-test regression with coverage,
   frontend lint, TypeScript and production build, `docker compose config
   --quiet`, and the M3 Alembic downgrade/upgrade/check matrix against an
   isolated database whose name contains `test`;
9. smoke-check README setup commands/configuration from the clean snapshot with
   disposable environment variables or a temporary copy of `.env.example`,
   never the real `.env`;
10. on the first run, record exact commands and pass/fail/skip counts in
    `docs/IMPLEMENTATION_STATUS.md`; on the final-commit rerun, verify those
    recorded commands/results and append nothing unless a failure requires a
    fix and another full final-commit cycle;
11. compare the restored Milestone 4 tracked binary diff and every untracked
    file hash, including the preserved frontend-library local delta, with their
    pre-rewrite records.

Any failed secret/history or worktree-preservation check stops the process. No
push is performed by this task unless the owner explicitly asks for it after
reviewing the final state.
