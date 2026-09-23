#!/bin/sh
# Named volumes keep ownership from the first writer. Git compose runs
# grafana/alloy as root; this wrapper runs as uid 473. Chown storage then drop.
set -eu

DATA="${ALLOY_STORAGE_PATH:-/var/lib/alloy/data}"
mkdir -p "${DATA}"

if [ "$(id -u)" -eq 0 ]; then
	chown -R alloy:alloy "${DATA}"
	exec setpriv --reuid=alloy --regid=alloy --init-groups --inh-caps=-all -- \
		/bin/alloy "$@"
fi

exec /bin/alloy "$@"
