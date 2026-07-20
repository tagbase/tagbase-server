# Agent notes

## Agent skills

### Issue tracker

GitHub Issues on `tagbase/tagbase-server` via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default mattpocock triage vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout (`CONTEXT.md` + `docs/adr/` at repo root). See `docs/agents/domain.md`.

### Ingest

Operator patterns (API, rsync, `staging_data/` drop-folder): [Ingestion and Access Patterns](https://github.com/tagbase/tagbase-server/wiki/Ingestion-and-Access-Patterns). Errors use RFC7807 `application/problem+json` (ADR-0003).

### Observability

OpenTelemetry + Alloy + LGTM runbook: `docs/observability.md`. Browser UIs are only via the nginx gateway (`https://localhost/...`); see ADR-0002. Windows + Docker Desktop: `docs/windows.md`.
