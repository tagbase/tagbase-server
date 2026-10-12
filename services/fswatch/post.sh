#!/usr/bin/env bash
set -euo pipefail

PATH_TO_CHECK=${PATH_TO_CHECK:-/usr/src/app/staging_data/}
TAGBASE_INGEST_BASE=${TAGBASE_INGEST_BASE:-http://tagbase_server:5433/tagbase/api/v0}
CURL_MAX_TIME=${CURL_MAX_TIME:-60}
RECONCILE_SECONDS=${RECONCILE_SECONDS:-5}

if [ -n "${DEDUPE_STATE:-}" ]; then
	STATE_DIR=$(dirname "$DEDUPE_STATE")
	DONE_FILE=$DEDUPE_STATE
else
	STATE_DIR=${FSWATCH_STATE_DIR:-/var/lib/tagbase-fswatch}
	DONE_FILE=$STATE_DIR/done.tsv
fi
mkdir -p "$STATE_DIR"
PENDING_FILE=$STATE_DIR/pending.tsv
touch "$PENDING_FILE" "$DONE_FILE"

echo "Watching $PATH_TO_CHECK (state=$STATE_DIR)"

if stat -c%s / >/dev/null 2>&1; then
	file_size() {
		[ -f "$1" ] || return 1
		stat -c%s "$1"
	}
else
	file_size() {
		[ -f "$1" ] || return 1
		stat -f%z "$1"
	}
fi

urlencode() {
	python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=""))' "$1"
}

should_ingest() {
	name=$1
	case "$name" in
	.* | *.crdownload | *.part | *.tmp | *.download)
		return 1
		;;
	Unconfirmed\ *)
		return 1
		;;
	esac
	case "$name" in
	*.txt | *.zip | *.tar.gz | *.tgz)
		return 0
		;;
	*)
		return 1
		;;
	esac
}

wait_stable() {
	path=$1
	i=0
	while [ "$i" -lt 60 ]; do
		[ -f "$path" ] || return 1
		a=$(file_size "$path") || return 1
		sleep 0.5
		[ -f "$path" ] || return 1
		b=$(file_size "$path") || return 1
		if [ "$a" -eq "$b" ]; then
			return 0
		fi
		i=$((i + 1))
	done
	return 1
}

already_done() {
	path=$1
	size=$2
	awk -F '\t' -v path="$path" -v size="$size" '$1 == path && $2 == size { found = 1 } END { exit !found }' "$DONE_FILE"
}

already_pending() {
	path=$1
	awk -F '\t' -v path="$path" '$1 == path { found = 1 } END { exit !found }' "$PENDING_FILE"
}

record_pending() {
	path=$1
	size=$2
	job_id=$3
	awk -F '\t' -v path="$path" '$1 != path { print }' "$PENDING_FILE" >"$STATE_DIR/.pending.next"
	printf '%s\t%s\t%s\n' "$path" "$size" "$job_id" >>"$STATE_DIR/.pending.next"
	mv "$STATE_DIR/.pending.next" "$PENDING_FILE"
}

drop_pending() {
	path=$1
	awk -F '\t' -v path="$path" '$1 != path { print }' "$PENDING_FILE" >"$STATE_DIR/.pending.next"
	mv "$STATE_DIR/.pending.next" "$PENDING_FILE"
}

record_done() {
	path=$1
	size=$2
	drop_pending "$path"
	awk -F '\t' -v path="$path" '$1 != path { print }' "$DONE_FILE" >"$STATE_DIR/.done.next"
	printf '%s\t%s\n' "$path" "$size" >>"$STATE_DIR/.done.next"
	mv "$STATE_DIR/.done.next" "$DONE_FILE"
}

json_field() {
	python3 -c 'import json,sys; print(json.load(sys.stdin).get(sys.argv[1], "") or "")' "$1"
}

submit_file() {
	line=$1
	filename=${line##*/}
	if ! should_ingest "$filename"; then
		echo "Skipping non-ingestible: $filename"
		return 0
	fi
	if ! wait_stable "$line"; then
		echo "Gave up waiting for stable file: $filename"
		return 0
	fi
	size=$(file_size "$line") || return 0
	if already_pending "$line" || already_done "$line" "$size"; then
		echo "Already tracked, skipping: $filename"
		return 0
	fi
	echo "Submitting: $filename"
	enc=$(urlencode "$filename")
	ctype=application/octet-stream
	case "$filename" in
	*.txt) ctype=text/plain ;;
	esac
	body_file=$(mktemp "$STATE_DIR/.body.XXXXXX")
	code=$(curl -sS --max-time "$CURL_MAX_TIME" -o "$body_file" -w '%{http_code}' -X POST \
		-H "accept: application/json" \
		-H "Content-Type: ${ctype}" \
		-T "$line" \
		"${TAGBASE_INGEST_BASE}/ingest/jobs?filename=${enc}&type=etuff" || true)
	if [ "$code" != "202" ]; then
		echo "Ingest accept failed for $filename (HTTP ${code})"
		rm -f "$body_file"
		return 0
	fi
	job_id=$(json_field id <"$body_file" || true)
	rm -f "$body_file"
	if [ -z "$job_id" ]; then
		echo "Ingest accept for $filename did not return a job id"
		return 0
	fi
	record_pending "$line" "$size" "$job_id"
	echo "Queued $filename as $job_id"
}

reconcile_pending() {
	[ -s "$PENDING_FILE" ] || return 0
	snapshot=$(mktemp "$STATE_DIR/.pending.XXXXXX")
	cp "$PENDING_FILE" "$snapshot"
	while IFS=$'\t' read -r path size job_id; do
		[ -n "${job_id:-}" ] || continue
		body_file=$(mktemp "$STATE_DIR/.status.XXXXXX")
		code=$(curl -sS --max-time "$CURL_MAX_TIME" -o "$body_file" -w '%{http_code}' \
			-H "accept: application/json" \
			"${TAGBASE_INGEST_BASE}/ingest/jobs/${job_id}" || true)
		if [ "$code" != "200" ]; then
			echo "Job status request failed for $job_id (HTTP ${code}); keeping pending"
			rm -f "$body_file"
			continue
		fi
		status=$(json_field status <"$body_file" || true)
		if [ "$status" = "succeeded" ]; then
			record_done "$path" "$size"
			echo "Ingest OK: ${path##*/}"
		elif [ "$status" = "failed" ]; then
			echo "Job $job_id failed: $(cat "$body_file")"
			drop_pending "$path"
		fi
		rm -f "$body_file"
	done <"$snapshot"
	rm -f "$snapshot"
}

scan_existing() {
	for path in "$PATH_TO_CHECK"*; do
		[ -f "$path" ] || continue
		submit_file "$path"
	done
}

scan_existing

FSWATCH_CMD=(fswatch)
if command -v stdbuf >/dev/null 2>&1; then
	FSWATCH_CMD=(stdbuf -oL fswatch)
fi

FIFO=$(mktemp -u "$STATE_DIR/.events.XXXXXX")
mkfifo "$FIFO"
"${FSWATCH_CMD[@]}" "$PATH_TO_CHECK" \
	--event Created --event MovedTo --event IsFile --event Updated >"$FIFO" &
watch_pid=$!
cleanup() {
	kill "$watch_pid" >/dev/null 2>&1 || true
	rm -f "$FIFO"
}
trap cleanup EXIT

exec 3<>"$FIFO"
while true; do
	reconcile_pending
	if IFS= read -r -t "$RECONCILE_SECONDS" -u 3 line; then
		submit_file "$line"
		while IFS= read -r -t 0 -u 3 line; do
			submit_file "$line"
		done
	fi
done
