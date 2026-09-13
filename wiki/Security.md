# Security (operators)

How tagbase-server is exposed on the network, how TLS and passwords work, and what you must set. Install steps: [Installation](https://github.com/tagbase/tagbase-server/wiki/Installation). This page is the security model for that stack.

Nginx is the **only browser entry**. Grafana, Alloy, Prometheus, Loki, Tempo, the API, and pgAdmin are reached through it.

## Gateway (nginx)

All user-facing HTTP(S) goes through nginx. Grafana, Alloy, Prometheus, Loki, Tempo, the API, and pgAdmin are on the Docker network. In the **GHCR / Compose OCI** install they are not published as extra host ports.

- **HTTPS:** port **443**
- **HTTP:** port **80** — ACME challenge (see below) or **301** to HTTPS
- Port **81** is not used

The nginx image is **digest-pinned** in compose (not a floating `latest` tag).

`server_tokens` is off. Docker embedded DNS is used so observability backends resolve at request time.

## Authentication

HTTPS locations use **HTTP basic auth**. The password file is written when the container **starts**, from:

| Variable     | Default (git compose) | OCI / published compose   |
| ------------ | --------------------- | ------------------------- |
| `NGINX_USER` | `tagbase`             | `tagbase` if unset        |
| `NGINX_PASS` | `tagbase`             | **required** (no default) |

Do not bake credentials into an image build. Old `--build-arg NGINX_USER` / `NGINX_PASS` are gone.

Grafana is **anonymous Admin** _behind_ nginx. Nginx **clears** the `Authorization` header on `/grafana/` (and other observability paths) so browser basic auth is not forwarded (that used to cause a second 401 prompt).

pgAdmin has its **own** login (`PGADMIN_DEFAULT_EMAIL` / `PGADMIN_DEFAULT_PASSWORD`) **after** nginx basic auth. Treat both as secrets on any shared host.

Database password is `POSTGRES_PASSWORD` (required on the OCI install). You do not edit SQL files to change it.

## TLS

Certificates are **not** stored in git. Do **not** run `openssl` by hand and copy PEMs into `services/nginx/ssl/` — that workflow is obsolete.

### Default (non-production / no public DNS)

On first start, if `/etc/nginx/certs/cert.pem` and `key.pem` are missing, nginx’s entrypoint creates a **self-signed** pair (CN/SAN `localhost`) on the **`nginx-certs` named volume**.

- Browsers will warn. For CLI: `curl -k`
- Restarting the stack **reuses** the volume
- `docker compose down -v` **deletes** the volume; the next start mints a new pair

This is expected until you have a public hostname.

### Let’s Encrypt (optional)

When the host has a **public DNS name** pointing at this machine and port **80** is reachable from the internet:

```bash
export TLS_DOMAIN=tagbase.example.org
export ACME_EMAIL=ops@example.org   # any inbox you control; no Let's Encrypt signup
docker compose --profile letsencrypt -f oci://ghcr.io/tagbase/tagbase-stack:vX.Y.Z up -d
```

(Git clone: `docker compose --profile letsencrypt up -d` with the same env.)

- **HTTP-01** only (no DNS-01 in this version)
- Challenge files: `/.well-known/acme-challenge/` on port 80, **`auth_basic off`**
- Lego writes the issued cert into the same `nginx-certs` volume; nginx **reloads** (inotify) without using the Docker socket
- Account metadata stays in the `lego-data` volume
- Default `up` **does not** start Lego
- Experiments: set `ACME_DIRECTORY` to the [Let’s Encrypt staging API](https://letsencrypt.org/docs/staging-environment/) to avoid production rate limits

## What is open on the host

| Install                          | Host ports                                                                                         |
| -------------------------------- | -------------------------------------------------------------------------------------------------- |
| GHCR Compose OCI                 | **80**, **443**, Alloy syslog **514/udp** (for Docker log scrape). **Postgres is not** on the host |
| Git clone (`docker-compose.yml`) | **80**, **443**, and PostGIS **5432** for local DB clients                                         |

Do not publish Grafana/Alloy/OTLP on the host.

## Logs and the Docker socket

The **published** compose does **not** mount `/var/run/docker.sock`. Container stdout goes to Alloy via the Docker **syslog** logging driver (`SYSLOG_ADDRESS`, default `host.docker.internal:514` on Docker Desktop). See [Installation](https://github.com/tagbase/tagbase-server/wiki/Installation).

Git clone compose **does** mount the socket on Alloy so local Docker logs can be scraped. That widens the Alloy container’s privilege; do not copy that bind into a public OCI artifact.

## Images and secrets

GHCR images are public (once maintainers set package visibility). They must not contain your passwords or Let’s Encrypt account keys. Secrets are environment at `up` time. Do not use `docker compose publish --with-env` when publishing the stack (that would bake interpolated secrets into the artifact).

## Related

- [Installation](https://github.com/tagbase/tagbase-server/wiki/Installation)
- [Operations](https://github.com/tagbase/tagbase-server/wiki/Operations)
- [nginx TLS volume notes](https://github.com/tagbase/tagbase-server/blob/main/services/nginx/ssl/README.md)
