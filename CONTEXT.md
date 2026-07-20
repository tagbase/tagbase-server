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

## Ops telemetry (not domain observations)

These terms describe runtime observability. They must not be confused with eTUFF **observations** (tag measurement rows).

**Telemetry**:
Metrics, logs, and traces emitted about service behavior (latency, errors, ingest pipeline).
_Avoid_: observations (when meaning ops signals)

**OTLP**:
OpenTelemetry Protocol — the wire format used to export telemetry from `tagbase_server` to Alloy.

**Alloy**:
Grafana Alloy — the collector that receives OTLP and Docker logs and forwards them to LGTM or Grafana Cloud.

**LGTM**:
Self-hosted Loki + Grafana + Tempo + Prometheus stack used for local observability.
