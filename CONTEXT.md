# tagbase-server

HTTP API and ingestion pipeline for archival tag datasets (eTUFF) into PostgreSQL.

## Language

**eTUFF**:
A text (or archive-of-text) tag data file format carrying global attributes, metadata, and observations for an archival tag deployment.
_Avoid_: etuff file (when referring to the format itself), raw tag dump

**Ingest**:
The operation that accepts an eTUFF source (network URL or uploaded body), persists it, and loads its contents into the database.
_Avoid_: upload-only, import (when meaning the full pipeline)

**Ingest file type**:
The OpenAPI `type` parameter naming the payload format for an ingest; today only `etuff` is supported, and that is the default when omitted.
_Avoid_: MIME type, content-type (for this parameter)

**Submission**:
A recorded attempt to ingest a specific eTUFF source for a tag/dataset, including hashes used for duplicate detection.
_Avoid_: upload job, ingest request (when referring to the persisted row)

**Ingest job**:
One accepted upload (a single file or an archive) queued in `ingest_job` and run by the ingest worker. A job produces one Submission per eTUFF member it loads.
_Avoid_: upload job, task

**Member**:
One eTUFF file inside an ingest job. A single-file job has one member; an archive has one per eTUFF file it contains.
_Avoid_: entry, part

**Job log line**:
A worker log line tagged with `job_id=<uuid>`, shown on demand in a Grafana panel for that job. It is telemetry, not a domain observation. The job API does not read it; job status comes from the `ingest_job` row.
_Avoid_: event, observation

## Ops telemetry (not domain observations)

These terms describe runtime observability. They must not be confused with eTUFF **observations** (tag measurement rows).

**Telemetry**:
Metrics, logs, traces, and profiles emitted about service behavior (latency, errors, ingest pipeline).
_Avoid_: observations (when meaning ops signals)

**Profile**:
Wall-clock stack samples and sampled heap allocations from the `tagbase_server` ingest worker and API workers. Only collected with the profiling image and `TAGBASE_PYROSCOPE_ENABLED=true`.
_Avoid_: observation, CPU profile (samples are wall-clock)

**Pyroscope**:
Grafana Pyroscope — the profile store. Alloy forwards profiles to the local container (`https://localhost/pyroscope/`) or to Grafana Cloud Profiles when `PYROSCOPE_*` is set.

**Ingest phase**:
The `phase` label on profile samples inside one file ingest: `read`, `resolve`, `metadata`, `build_rows`, `dataframe`, `csv_buffer`, `copy`, `procedure`. Used to filter flame graphs; it is not a job status.
_Avoid_: stage, step (when meaning job status)

**OTLP**:
OpenTelemetry Protocol — the wire format used to export telemetry from `tagbase_server` to Alloy.

**Alloy**:
Grafana Alloy — the collector that receives OTLP and Docker logs and forwards them to LGTM or Grafana Cloud.

**LGTM**:
Self-hosted Loki + Grafana + Tempo + Prometheus stack used for local observability.
