#!/bin/sh
# Gunicorn accepts uploads. One ingest process beside it runs the queue.
set -eu

python -m tagbase_server.ingest_worker &
worker_pid=$!

gunicorn -c gunicorn.conf.py tagbase_server.__main__:app &
gunicorn_pid=$!

stop() {
	kill "$worker_pid" "$gunicorn_pid" 2>/dev/null || true
}
trap stop INT TERM

status=0
while true; do
	if ! kill -0 "$gunicorn_pid" 2>/dev/null; then
		wait "$gunicorn_pid" || status=$?
		break
	fi
	if ! kill -0 "$worker_pid" 2>/dev/null; then
		wait "$worker_pid" || status=$?
		break
	fi
	sleep 1
done
stop
wait "$worker_pid" 2>/dev/null || true
wait "$gunicorn_pid" 2>/dev/null || true
exit "$status"
