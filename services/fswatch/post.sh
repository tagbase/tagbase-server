#!/usr/bin/env sh
set -eu

PATH_TO_CHECK=${PATH_TO_CHECK:-/usr/src/app/staging_data/}
TAGBASE_INGEST_BASE=${TAGBASE_INGEST_BASE:-http://tagbase_server:5433/tagbase/api/v0.14.0}

# Last successfully ingested path+size (file so it survives the fswatch|while subshell).
DEDUPE_STATE=${DEDUPE_STATE:-/tmp/fswatch-ingest-dedupe-$$}
if ! : >"$DEDUPE_STATE" 2>/dev/null; then
  DEDUPE_STATE="/tmp/fswatch-ingest-dedupe-$$"
  : >"$DEDUPE_STATE"
fi

echo "Watching $PATH_TO_CHECK (dedupe=$DEDUPE_STATE)"

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

already_ingested() {
  path=$1
  size=$2
  [ -f "$DEDUPE_STATE" ] || return 1
  {
    read -r last_path
    read -r last_size
  } <"$DEDUPE_STATE" || return 1
  [ "$path" = "$last_path" ] && [ "$size" = "$last_size" ]
}

ingest_file() {
  line=$1
  filename=${line##*/}
  if ! should_ingest "$filename"; then
    echo "Skipping non-ingestible: $filename"
    return 0
  fi
  echo "Contents of $PATH_TO_CHECK changed; Checking: $filename"
  if ! wait_stable "$line"; then
    echo "Gave up waiting for stable file: $filename"
    return 0
  fi
  size=$(file_size "$line") || return 0
  if already_ingested "$line" "$size"; then
    echo "Already ingested at this size, skipping: $filename"
    return 0
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
    printf '%s\n%s\n' "$line" "$size" >"$DEDUPE_STATE"
    echo
    echo "Ingest OK: $filename"
  fi
}

scan_existing() {
  # Process files already present (startup / leftover from a prior blind window).
  # shellcheck disable=SC2039
  for path in "$PATH_TO_CHECK"*; do
    [ -f "$path" ] || continue
    ingest_file "$path"
  done
}

scan_existing

# Continuous watch: keep receiving events while wait_stable/curl run for one file.
# Line-buffer fswatch stdout when piped (otherwise events can sit in libc buffer).
# Outer loop only restarts fswatch if the binary exits unexpectedly.
FSWATCH_CMD="fswatch"
if command -v stdbuf >/dev/null 2>&1; then
  FSWATCH_CMD="stdbuf -oL fswatch"
fi

while true; do
  # shellcheck disable=SC2086
  $FSWATCH_CMD "$PATH_TO_CHECK" \
    --event Created --event MovedTo --event IsFile --event Updated \
    | while IFS= read -r line; do
        ingest_file "$line"
      done
  echo "fswatch exited; restarting watch on $PATH_TO_CHECK"
  sleep 1
done
