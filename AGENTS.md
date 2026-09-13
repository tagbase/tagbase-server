# Agent notes

Operator documentation is the [GitHub wiki](https://github.com/tagbase/tagbase-server/wiki). Do not add a `docs/` tree or ADRs. Compose files, OpenAPI, and application code win if a wiki page is stale.

## Agent skills

### Issue tracker

GitHub Issues on `tagbase/tagbase-server` via the `gh` CLI.

- **Create**: `gh issue create --repository tagbase/tagbase-server --title "..." --body "..."` (heredoc for multi-line bodies).
- **Read**: `gh issue view <number> --repository tagbase/tagbase-server --comments`
- **List**: `gh issue list --repository tagbase/tagbase-server --state open` with `--label` / `--json` as needed
- **Comment**: `gh issue comment <number> --body "..."`
- **Labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

`gh` infers the repo from `git remote` inside a clone. **PRs as a request surface: no.** GitHub shares one number space across issues and PRs — try `gh pr view 42` then `gh issue view 42`.

When a skill says “publish to the issue tracker”, create a GitHub issue. When it says “fetch the relevant ticket”, run `gh issue view <number> --comments`.

Wayfinder: map issue labelled `wayfinder:map`; children as sub-issues (or task-list + `Part of #<map>`); native issue dependencies when available; claim with `gh issue edit <n> --add-assignee @me`.

### Triage labels

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

### Domain docs

Read `CONTEXT.md` for domain language. Operator how-to lives on the wiki, not in-repo markdown trees. Do not create `docs/` or `docs/adr/`.

### Ingest

[Ingestion and Access Patterns](https://github.com/tagbase/tagbase-server/wiki/Ingestion-and-Access-Patterns). Errors use RFC7807 `application/problem+json`.

### Observability

LGTM/Alloy is part of the default stack. Browser UIs only via nginx (`https://localhost/...`): [Installation](https://github.com/tagbase/tagbase-server/wiki/Installation), [Security](https://github.com/tagbase/tagbase-server/wiki/Security). Windows: Docker Desktop Linux containers + WSL2 (clone on the Linux filesystem, not `/mnt/c`).

### Branches

Do not implement on `main` (or `master`). Before the first file change, create or switch to a local topic branch (`git checkout -b …` / `git switch -c …`). If the working tree is already dirty on `main`, stop and tell the user rather than committing there. The human adds and commits locally unless they explicitly ask the agent to commit.

### Commits

When the work is ready, **recommend one Conventional Commit** (subject + short body) and stop. Do not `git add` or `git commit` unless the user asks. Default is **one commit for the whole change**; split only if they ask.

[Conventional Commits](https://www.conventionalcommits.org/). CI lints the PR title **and** every commit (`@commitlint/config-conventional`). Use `feat` / `fix` for version bumps. `chore`, `docs`, `ci`, and similar are patch when a release runs.

Do **not** use a `BREAKING CHANGE` footer or `feat!:` / `fix!:` on `0.x` unless the user explicitly wants **1.0.0**. That rewrite changes the public API prefix from `/tagbase/api/v0` to `/tagbase/api/v1`. Operator-facing breaks (ports, env) go in the commit **body**, not the footer.

See [Release Management](https://github.com/tagbase/tagbase-server/wiki/Release-Management). Do not “fix” a failed semantic-release by granting the default `GITHUB_TOKEN` write: `main` is PR-protected and `github-actions[bot]` cannot push to it. Releases need repo secret `RELEASE_TOKEN` (classic PAT).

### Super Linter

Changed files must pass Super Linter before you treat the work as done. Failed Super Linter on CI is a wasted round-trip. Use [`scripts/run-super-linter-pre-commit.sh`](scripts/run-super-linter-pre-commit.sh) (same image and [`.github/super-linter.env`](.github/super-linter.env) as [`.github/workflows/super-linter.yml`](.github/workflows/super-linter.yml)). Set `SUPER_LINTER_REQUIRE_DOCKER=1` so a missing Docker daemon is a hard fail, not a skip. Fix Ruff, Prettier, and the other validators in the log; do not “fix” by disabling a linter unless the user asks.
