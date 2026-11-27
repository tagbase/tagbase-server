#!/bin/sh
# Named volumes keep ownership from the first writer. The published image runs
# this wrapper as root, chowns storage, then drops to uid 473. Git compose sets
# ALLOY_KEEP_ROOT=true because docker.sock discovery needs root.
set -eu

DATA="${ALLOY_STORAGE_PATH:-/var/lib/alloy/data}"
mkdir -p "${DATA}"

# config.cloud.alloy always declares pyroscope.write. An empty endpoint makes
# Alloy refuse to start, so discard profiles unless Grafana Cloud Profiles is set.
if [ -z "${PYROSCOPE_ENDPOINT:-}" ]; then
	export PYROSCOPE_ENDPOINT="http://127.0.0.1:9"
	export PYROSCOPE_USERNAME="${PYROSCOPE_USERNAME:-unused}"
	export PYROSCOPE_PASSWORD="${PYROSCOPE_PASSWORD:-unused}"
elif [ -z "${PYROSCOPE_USERNAME:-}" ] || [ -z "${PYROSCOPE_PASSWORD:-}" ]; then
	echo "PYROSCOPE_ENDPOINT is set but PYROSCOPE_USERNAME or PYROSCOPE_PASSWORD is empty" >&2
	exit 1
fi

if [ "$(id -u)" -eq 0 ] && [ "${ALLOY_KEEP_ROOT:-false}" != "true" ]; then
	chown -R alloy:alloy "${DATA}"
	exec setpriv --reuid=alloy --regid=alloy --init-groups --inh-caps=-all -- \
		/bin/alloy "$@"
fi

exec /bin/alloy "$@"
