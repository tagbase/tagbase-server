# Introduction

This page provides details the tagbase-server [system architecture](https://www.mitre.org/publications/systems-engineering-guide/se-lifecycle-building-blocks/system-architecture). This serves the following purposes

- assists in understanding how the deployment may have changed (gotten more complex) over time
- provides guidance on how tagbase-server is physically deployed into target environments e.g. Docker Swarm, Kubernetes, AWS EKS, etc.

## Architecture diagrams for the docker composition

The diagram below represents the system architecture as of `v0.8.0`.

![tagbase-server system architecture](https://raw.githubusercontent.com/tagbase/tagbase.github.io/master/images/docker-compose.png)

N.B. This diagram was generated using [docker-compose-diagram](https://github.com/skonik/docker-compose-diagram).

```bash
brew install graphviz
pip3 install docker-compose-diagram
compose-diagram --file docker-compose.yml --direction=TB --nodesep=1.5
```

The file is then written to `docker-compose.png`.

## Runtime dependency on Loki

`tagbase_server` reads from Loki at request time. `GET /tagbase/api/v0/ingest/jobs/{job_id}` queries Loki (`LOKI_URL`, default `http://loki:3100`) for that job's log lines. The ingest worker's lines reach Loki over OTLP through Alloy (`otelcol.exporter.loki`), in both the git and the published stack, and Loki labels them `service_name=tagbase_server` from `OTEL_SERVICE_NAME`. If Loki is down, the job API still answers, with `log_available: false`, and ingest is not affected.
