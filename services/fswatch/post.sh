#!/usr/bin/env sh
set -eu

PATH_TO_CHECK=${PATH_TO_CHECK:-/usr/src/app/staging_data/}
TAGBASE_INGEST_BASE=${TAGBASE_INGEST_BASE:-http://tagbase_server:5433/tagbase/api/v0.14.0}

# Detect GNU vs BSD stat once (not per-file — missing files must not flip dialects).
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
  # Prefer python3 (available in fswatch image); fall back to raw name.
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=""))' "$1"
  else
    printf '%s' "$1"
  fi
}

should_ingest() {
  name=$1
  case "$name" in
    .*|*.crdownload|*.part|*.tmp|*.download)
      return 1
      ;;
    Unconfirmed\ *)
      return 1
      ;;
  esac
  case "$name" in
    *.txt|*.zip|*.tar.gz|*.tgz)
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

while true; do
  fswatch --one-event "$PATH_TO_CHECK" \
    --event Created --event MovedTo --event IsFile --event Updated \
    | while IFS= read -r line; do
        filename=${line##*/}
        if ! should_ingest "$filename"; then
          echo "Skipping non-ingestible: $filename"
          continue
        fi
        echo "Contents of $PATH_TO_CHECK changed; Checking: $filename"
        if ! wait_stable "$line"; then
          echo "Gave up waiting for stable file: $filename"
          continue
        fi
        echo "Processing: $filename"
        enc=$(urlencode "$filename")
        ctype=application/octet-stream
        case "$filename" in
          *.txt) ctype=text/plain ;;
        esac
        if ! curl -sS -f -X POST \
          -H "accept: application/json" \
          -H "Content-Type: ${ctype}" \
          -T "$line" \
          "${TAGBASE_INGEST_BASE}/ingest?filename=${enc}&type=etuff"; then
          echo "Ingest failed for $filename (see tagbase_server logs)"
        else
          echo
          echo "Ingest OK: $filename"
        fi
      done
done
