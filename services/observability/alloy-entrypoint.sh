#!/bin/sh
# Named volumes keep ownership from the first writer. Git compose runs
# grafana/alloy as root; this wrapper runs as uid 473. Chown storage then drop.
set -eu

DATA="${ALLOY_STORAGE_PATH:-/var/lib/alloy/data}"
mkdir -p "${DATA}"

# config.cloud.alloy always declares pyroscope.write. An empty endpoint makes
# Alloy refuse to start, so discard profiles unless Grafana Cloud Profiles is set.
if [ -z "${PYROSCOPE_ENDPOINT:-}" ]; then
	export PYROSCOPE_ENDPOINT="http://127.0.0.1:9"
	export PYROSCOPE_USERNAME="${PYROSCOPE_USERNAME:-unused}"
	export PYROSCOPE_PASSWORD="${PYROSCOPE_PASSWORD:-unused}"
fi

if [ "$(id -u)" -eq 0 ]; then
	chown -R alloy:alloy "${DATA}"
	exec setpriv --reuid=alloy --regid=alloy --init-groups --inh-caps=-all -- \
		/bin/alloy "$@"
fi

exec /bin/alloy "$@"
