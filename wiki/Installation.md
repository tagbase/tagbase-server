# Installation (operators)

This page is for people who **run** tagbase-server: ingest eTUFF, use the HTTP API and UIs, keep the stack up. You do **not** need to build from source.

Developers who change code should clone the git repository and use `docker compose up --build`. Release mechanics: [Release Management](https://github.com/tagbase/tagbase-server/wiki/Release-Management).

**Recommended:** Docker Compose **2.34+** and images from GitHub Container Registry (GHCR). Git is not required.

## What you get

The stack is reached only through **nginx** (HTTPS). Grafana, Alloy, Prometheus, Loki, Tempo, the API, and pgAdmin are not published as extra host ports in the operator install.

| What             | URL / port                                                             |
| ---------------- | ---------------------------------------------------------------------- |
| Landing          | [https://localhost/](https://localhost/)                               |
| OpenAPI UI       | [https://localhost/docs](https://localhost/docs)                       |
| REST API (0.x)   | [https://localhost/tagbase/api/v0](https://localhost/tagbase/api/v0)   |
| pgAdmin          | [https://localhost/pgadmin4/](https://localhost/pgadmin4/)             |
| Grafana          | [https://localhost/grafana/](https://localhost/grafana/)               |
| Alloy            | [https://localhost/alloy/](https://localhost/alloy/)                   |
| Prometheus       | [https://localhost/prometheus/](https://localhost/prometheus/)         |
| Loki / Tempo UIs | [https://localhost/grafana/explore](https://localhost/grafana/explore) |

HTTP **80** redirects to HTTPS **443** and serves Let’s Encrypt HTTP-01 if you enable that profile. Nothing listens on port **81**.

The **API path is major-only** (`/tagbase/api/v0` today). Old patch URLs such as `/tagbase/api/v0.14.0` 404.

Ingest patterns: [Ingestion and Access Patterns](https://github.com/tagbase/tagbase-server/wiki/Ingestion-and-Access-Patterns).

## Prerequisites

- [Docker Engine](https://docs.docker.com/engine/install/) or [Docker Desktop](https://www.docker.com/products/docker-desktop) (Linux containers)
- [Docker Compose](https://docs.docker.com/compose/install/) **v2.34 or newer** (`docker compose version`)
- **~8 GiB RAM** for the VM/engine (large eTUFF files may need more). [Docker Desktop memory](https://docs.docker.com/desktop/settings-and-maintenance/settings/#advanced)
- On Apple Silicon, PostGIS still runs as **linux/amd64** (emulation). That is expected.
- Windows: Docker Desktop **Linux containers** + **WSL2**. Clone and run from the WSL Linux filesystem (not `/mnt/c`). Scripts are LF (`.gitattributes`). Prefer WSL bash over PowerShell for `*.sh`.

Pick a **version tag** from [Releases](https://github.com/tagbase/tagbase-server/releases) (for example `v0.15.0`). Images and the Compose artifact use the same tag: `ghcr.io/tagbase/tagbase-stack:vX.Y.Z`.

If `docker compose -f oci://… pull` fails with 404/denied, the GHCR packages for that tag are not public yet (first publish is often private). Ask a maintainer to set the `tagbase/*` packages public, or use the [git clone fallback](#git-clone-fallback) until they are.

## Recommended: Compose OCI (no git clone)

Set secrets in the environment (or a `.env` file in the directory where you run Compose). **Do not use the examples below in anything reachable from a network.**

```bash
export POSTGRES_PASSWORD='choose-a-strong-password'
export NGINX_PASS='choose-a-strong-password'
export PGADMIN_DEFAULT_PASSWORD='choose-a-strong-password'
# optional
export NGINX_USER=tagbase
export PGADMIN_DEFAULT_EMAIL=admin@example.com
```

Start a release (replace the tag):

```bash
docker compose -f oci://ghcr.io/tagbase/tagbase-stack:vX.Y.Z up -d
```

Compose will list interpolation variables and remote sources; confirm if you trust `tagbase/tagbase-server`.

Wait until nginx is up, then:

```bash
curl -kf -u "${NGINX_USER:-tagbase}:${NGINX_PASS}" https://localhost/tagbase/api/v0/tags
```

Expect a browser **certificate warning**. Nginx creates a **self-signed** cert on first start and keeps it in the `nginx-certs` volume. `docker compose down` keeps the volume; `docker compose down -v` deletes data **and** the cert (a new self-signed pair is minted next time).

### Required and optional environment

| Variable                    | Required (OCI install)            | Notes                                                                                                                         |
| --------------------------- | --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `POSTGRES_PASSWORD`         | yes                               | Database and app                                                                                                              |
| `NGINX_PASS`                | yes                               | HTTP basic auth on all UIs                                                                                                    |
| `PGADMIN_DEFAULT_PASSWORD`  | yes                               | pgAdmin login (after nginx auth)                                                                                              |
| `NGINX_USER`                | no                                | Default `tagbase`                                                                                                             |
| `PGADMIN_DEFAULT_EMAIL`     | no                                | Default `admin@example.com`                                                                                                   |
| `SYSLOG_ADDRESS`            | no                                | Default `host.docker.internal:514`. Docker Desktop: leave default. Linux engine: try `127.0.0.1:514` if logs never reach Loki |
| `TLS_DOMAIN` / `ACME_EMAIL` | only with `--profile letsencrypt` | See [Trusted HTTPS](#trusted-https-lets-encrypt)                                                                              |

Postgres is **not** published on the host in this install (API and pgAdmin use the Docker network). Backups stay in the `dbbackups` volume.

### Drop-folder ingest (eTUFF on disk)

The published compose uses a **named volume** `staging-data` (empty until you copy files in or ingest over the API). Compose OCI **cannot** include host bind mounts.

To watch a directory on the operator machine, add a local override file (not published) after the first `up`, for example `compose.override.yml`:

```yaml
services:
  fswatch:
    volumes:
      - /absolute/path/to/staging_data:/usr/src/app/staging_data:ro
```

```bash
docker compose -f oci://ghcr.io/tagbase/tagbase-stack:vX.Y.Z -f compose.override.yml up -d
```

API ingest does not need that override: [Ingestion and Access Patterns](https://github.com/tagbase/tagbase-server/wiki/Ingestion-and-Access-Patterns).

### Trusted HTTPS (Let’s Encrypt)

Only when the host has a **public DNS name** pointing at this machine and port **80** is reachable from the internet. There is no Let’s Encrypt “account signup”; `ACME_EMAIL` is an inbox you control (expiry mail). Details: [Security](https://github.com/tagbase/tagbase-server/wiki/Security).

```bash
export TLS_DOMAIN=tagbase.example.org
export ACME_EMAIL=ops@example.org
docker compose --profile letsencrypt -f oci://ghcr.io/tagbase/tagbase-stack:vX.Y.Z up -d
```

Default `up` (no profile) never starts Lego. For experiments, set `ACME_DIRECTORY` to the [Let’s Encrypt staging directory](https://letsencrypt.org/docs/staging-environment/) so you do not burn production rate limits.

### Stop / remove

```bash
docker compose -f oci://ghcr.io/tagbase/tagbase-stack:vX.Y.Z stop
# remove containers; keep volumes (database, certs, logs)
docker compose -f oci://ghcr.io/tagbase/tagbase-stack:vX.Y.Z down
# destroy volumes as well (irreversible)
docker compose -f oci://ghcr.io/tagbase/tagbase-stack:vX.Y.Z down -v
```

## Using the UIs

All browser routes need **nginx basic auth** (`NGINX_USER` / `NGINX_PASS`). Grafana is anonymous **behind** that gateway; do not expose Grafana on the host.

**OpenAPI** is the ingest contract (GET/POST, `file` / `ftp` / `http` / `https`, `.txt` / archives). Start at [https://localhost/docs](https://localhost/docs).

**pgAdmin:** [https://localhost/pgadmin4/](https://localhost/pgadmin4/) — nginx auth first, then `PGADMIN_DEFAULT_EMAIL` / `PGADMIN_DEFAULT_PASSWORD`. Register a server:

- Host: **`postgis`** (Docker DNS name, not `postgres` and not `localhost`)
- Port: `5432`
- Database: `tagbase`
- Username: `tagbase`
- Password: the same `POSTGRES_PASSWORD`

**Materialized views** (once, after you have ingested tags you want in “application ready” form): run [`tagbase_materialized_views.sql`](https://github.com/tagbase/tagbase-server/blob/main/services/postgis/tagbase_materialized_views.sql) in the pgAdmin query tool. Do not re-run that script on every ingest.

Observability (Grafana, Loki, Tempo, Prometheus, Alloy) starts with the stack. Git compose sets `OTEL_SDK_DISABLED=false` and `OTEL_EXPORTER_OTLP_ENDPOINT=http://alloy:4317`. The published install ships container logs to Alloy over syslog (`SYSLOG_ADDRESS`, default `host.docker.internal:514`).

## Git clone fallback

Use this if GHCR is unavailable, or you are iterating on compose binds (`./staging_data`, `./postgis-data`).

```bash
git clone https://github.com/tagbase/tagbase-server.git
cd tagbase-server
docker compose up -d --build
```

Git compose still **builds** first-party images and bind-mounts config. It **defaults** passwords to `tagbase` if you set nothing; change them before any shared host. TLS is still generated at runtime (nothing to copy into `services/nginx/ssl/`). HTTP is port **80**, not 81.

Optional Let’s Encrypt is the same profile: `docker compose --profile letsencrypt up -d` with `TLS_DOMAIN` and `ACME_EMAIL`.

A `.env` file next to `docker-compose.yml` is optional (Compose loads it automatically). You do **not** edit SQL to change `POSTGRES_PASSWORD`.

Manual (non-Docker) install is **not supported**.

## Related

- [Security](https://github.com/tagbase/tagbase-server/wiki/Security) — nginx gateway, TLS, basic auth, and what is published on the host
- [Operations](https://github.com/tagbase/tagbase-server/wiki/Operations)
- [Systems Architecture](https://github.com/tagbase/tagbase-server/wiki/Systems-Architecture)
- [Release Management](https://github.com/tagbase/tagbase-server/wiki/Release-Management)
