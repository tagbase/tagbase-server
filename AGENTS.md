# Agent notes

## Agent skills

### Issue tracker

GitHub Issues on `tagbase/tagbase-server` via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default mattpocock triage vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout (`CONTEXT.md` + `docs/adr/` at repository root). See `docs/agents/domain.md`.

### Ingest

Operator patterns (API, rsync, `staging_data/` drop-folder): [Ingestion and Access Patterns](https://github.com/tagbase/tagbase-server/wiki/Ingestion-and-Access-Patterns). Errors use RFC7807 `application/problem+json` (ADR-0003).

### Observability

OpenTelemetry + Alloy + LGTM runbook: `docs/observability.md`. Browser UIs are only via the nginx gateway (`https://localhost/...`); see ADR-0002. Windows + Docker Desktop: `docs/windows.md`.

### Commits

[Conventional Commits](https://www.conventionalcommits.org/). CI lints the PR title **and** every commit (`@commitlint/config-conventional`). Use `feat` / `fix` / `BREAKING CHANGE` for version bumps; `chore`, `docs`, `ci`, and similar are patch when a release runs. Do not commit unless the user asks. See [wiki/Release-Management.md](wiki/Release-Management.md).

### Super Linter

Changed files must pass Super Linter before you treat the work as done. Failed Super Linter on CI is a wasted round-trip. Use [`scripts/run-super-linter-pre-commit.sh`](scripts/run-super-linter-pre-commit.sh) (same image and [`.github/super-linter.env`](.github/super-linter.env) as [`.github/workflows/super-linter.yml`](.github/workflows/super-linter.yml)). Set `SUPER_LINTER_REQUIRE_DOCKER=1` so a missing Docker daemon is a hard fail, not a skip. Fix Ruff, Prettier, and the other validators in the log; do not “fix” by disabling a linter unless the user asks.
