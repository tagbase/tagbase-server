#!/usr/bin/env bash
# Bring up the test observability stack, ingest a minimal eTUFF, assert
# Prometheus metrics and Tempo spans on the Docker network, plus one
# authenticated HTTPS check through the nginx gateway.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

COMPOSE=(docker compose -f docker-compose.test.yml --profile observability)
GATEWAY_URL="${GATEWAY_URL:-https://localhost}"
GATEWAY_USER="${GATEWAY_USER:-testuser}"
GATEWAY_PASS="${GATEWAY_PASS:-testpass}"
FIXTURE="${FIXTURE:-tagbase_server/tagbase_server/test/fixtures/etuff/minimal-etuff.txt}"
TIMEOUT_SECS="${TIMEOUT_SECS:-240}"

cleanup() {
  "${COMPOSE[@]}" down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

# HTTP GET via tagbase_server (same Docker network; backends have no host ports).
docker_http_get() {
  local url="$1"
  "${COMPOSE[@]}" exec -T tagbase_server \
    python -c "import urllib.request; print(urllib.request.urlopen('${url}', timeout=30).read().decode())"
}

echo "==> Starting observability test stack"
mkdir -p staging_data
export OTEL_SDK_DISABLED=false
export OTEL_EXPORTER_OTLP_ENDPOINT=http://alloy:4317
export OTEL_SERVICE_NAME=tagbase_server

"${COMPOSE[@]}" up -d --build

# Prometheus serves under --web.route-prefix=/prometheus/
PROM_BASE="http://prometheus:9090/prometheus"
# Grafana serve_from_sub_path + ROOT_URL=/grafana/
GRAFANA_BASE="http://grafana:3000/grafana"

echo "==> Waiting for Prometheus / Tempo / Grafana / tagbase_server / nginx"
deadline=$((SECONDS + TIMEOUT_SECS))
ready=0
while (( SECONDS < deadline )); do
  if docker_http_get "${PROM_BASE}/-/ready" >/dev/null 2>&1 \
    && docker_http_get "http://tempo:3200/ready" >/dev/null 2>&1 \
    && docker_http_get "${GRAFANA_BASE}/api/health" >/dev/null 2>&1 \
    && docker_http_get "http://127.0.0.1:5433/tagbase/api/v0.14.0/tags" >/dev/null 2>&1 \
    && curl -kf -s -o /dev/null -u "${GATEWAY_USER}:${GATEWAY_PASS}" \
         "${GATEWAY_URL}/tagbase/api/v0.14.0/tags"; then
    ready=1
    break
  fi
  sleep 5
done
if [[ "$ready" -ne 1 ]]; then
  echo "ERROR: stack not ready within ${TIMEOUT_SECS}s" >&2
  "${COMPOSE[@]}" ps >&2 || true
  "${COMPOSE[@]}" logs --tail=80 tagbase_server alloy prometheus tempo grafana nginx >&2 || true
  exit 1
fi

# Allow OTel metric export interval (10s) + scrape path
sleep 5

echo "==> Ingesting fixture ${FIXTURE}"
"${COMPOSE[@]}" cp "${FIXTURE}" tagbase_server:/tmp/minimal-etuff.txt
ingest_status="$("${COMPOSE[@]}" exec -T tagbase_server \
  python - <<'PY'
import urllib.error
import urllib.parse
import urllib.request

params = urllib.parse.urlencode({"file": "file:///tmp/minimal-etuff.txt", "type": "etuff"})
url = f"http://127.0.0.1:5433/tagbase/api/v0.14.0/ingest?{params}"
try:
    with urllib.request.urlopen(url, timeout=120) as resp:
        print(resp.status)
except urllib.error.HTTPError as e:
    print(e.code)
    raise SystemExit(1)
PY
)"
echo "Ingest HTTP status: ${ingest_status}"

echo "==> Waiting for tagbase_ingest_requests_total in Prometheus"
metric_ok=0
deadline=$((SECONDS + TIMEOUT_SECS))
while (( SECONDS < deadline )); do
  body="$(docker_http_get "${PROM_BASE}/api/v1/query?query=sum(tagbase_ingest_requests_total)" || true)"
  if echo "$body" | grep -Eq '"value":\[[0-9.]+,"[0-9.]+"\]'; then
    metric_ok=1
    break
  fi
  sleep 5
done
if [[ "$metric_ok" -ne 1 ]]; then
  echo "ERROR: metric tagbase_ingest_requests_total not found" >&2
  docker_http_get "${PROM_BASE}/api/v1/query?query=tagbase_ingest_requests_total" >&2 || true
  "${COMPOSE[@]}" logs --tail=80 alloy tagbase_server >&2 || true
  exit 1
fi
echo "OK: Prometheus has tagbase_ingest_requests_total"

echo "==> Searching Tempo for ingest spans"
trace_ok=0
deadline=$((SECONDS + TIMEOUT_SECS))
while (( SECONDS < deadline )); do
  # Tempo search API (TraceQL)
  body="$(docker_http_get 'http://tempo:3200/api/search?q=%7B%20resource.service.name%3D%22tagbase_server%22%20%26%26%20name%3D~%22ingest.%2A%22%20%7D&limit=20' || true)"
  if echo "$body" | grep -q '"traceID"'; then
    trace_ok=1
    break
  fi
  sleep 5
done
if [[ "$trace_ok" -ne 1 ]]; then
  echo "ERROR: no ingest.* spans found in Tempo" >&2
  docker_http_get 'http://tempo:3200/api/search?q=%7B%20resource.service.name%3D%22tagbase_server%22%20%7D&limit=20' >&2 || true
  "${COMPOSE[@]}" logs --tail=80 alloy tempo tagbase_server >&2 || true
  exit 1
fi
echo "OK: Tempo has ingest spans"

echo "==> Checking Grafana datasource proxy (Prometheus + Tempo)"
grafana_prom_ok=0
grafana_tempo_ok=0
deadline=$((SECONDS + TIMEOUT_SECS))
while (( SECONDS < deadline )); do
  prom_body="$(docker_http_get \
    "${GRAFANA_BASE}/api/datasources/proxy/uid/prometheus/api/v1/query?query=sum(tagbase_ingest_requests_total)" \
    || true)"
  if echo "$prom_body" | grep -Eq '"value":\[[0-9.]+,"[0-9.]+"\]'; then
    grafana_prom_ok=1
  fi
  tempo_body="$(docker_http_get \
    "${GRAFANA_BASE}/api/datasources/proxy/uid/tempo/api/search?q=%7B%20resource.service.name%3D%22tagbase_server%22%20%26%26%20name%3D~%22ingest.%2A%22%20%7D&limit=20" \
    || true)"
  if echo "$tempo_body" | grep -q '"traceID"'; then
    grafana_tempo_ok=1
  fi
  if [[ "$grafana_prom_ok" -eq 1 && "$grafana_tempo_ok" -eq 1 ]]; then
    break
  fi
  sleep 5
done
if [[ "$grafana_prom_ok" -ne 1 ]]; then
  echo "ERROR: Grafana Prometheus datasource proxy failed" >&2
  docker_http_get \
    "${GRAFANA_BASE}/api/datasources/proxy/uid/prometheus/api/v1/query?query=sum(tagbase_ingest_requests_total)" \
    >&2 || true
  "${COMPOSE[@]}" logs --tail=80 grafana prometheus >&2 || true
  exit 1
fi
if [[ "$grafana_tempo_ok" -ne 1 ]]; then
  echo "ERROR: Grafana Tempo datasource proxy failed" >&2
  docker_http_get \
    "${GRAFANA_BASE}/api/datasources/proxy/uid/tempo/api/search?q=%7B%20resource.service.name%3D%22tagbase_server%22%20%7D&limit=20" \
    >&2 || true
  "${COMPOSE[@]}" logs --tail=80 grafana tempo >&2 || true
  exit 1
fi
echo "OK: Grafana can query Prometheus and Tempo datasources"

echo "==> Checking nginx gateway (/grafana/)"
if ! curl -kf -s -o /dev/null -u "${GATEWAY_USER}:${GATEWAY_PASS}" \
  "${GATEWAY_URL}/grafana/"; then
  echo "ERROR: gateway https://localhost/grafana/ failed" >&2
  "${COMPOSE[@]}" logs --tail=80 nginx grafana >&2 || true
  exit 1
fi
echo "OK: nginx gateway serves /grafana/"

echo "==> Observability smoke passed"
