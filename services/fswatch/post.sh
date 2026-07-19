#!/usr/bin/env sh
PATH_TO_CHECK=${PATH_TO_CHECK:-/usr/src/app/staging_data/}
TAGBASE_INGEST_BASE=${TAGBASE_INGEST_BASE:-tagbase_server:5433/tagbase/api/v0.14.0}

file_size() {
  # GNU stat (Linux containers) vs BSD stat (macOS hosts for contract tests)
  if stat -c%s "$1" >/dev/null 2>&1; then
    stat -c%s "$1"
  else
    stat -f%z "$1"
  fi
}

while true
  do
    fswatch --one-event "$PATH_TO_CHECK" --event Created --event MovedTo --event IsFile --event Updated | while read line
      do
        filename="${line##*/}"
        echo "Contents of $PATH_TO_CHECK changed; Checking: $filename"

        # waiting for file to be fully uploaded
        while true
          do
            size_bfr=$(file_size "$line")
            sleep 0.5
            size_aftr=$(file_size "$line")
            if [ "$size_bfr" -eq "$size_aftr" ];
            then
                break;
            fi
          done

        echo "Processing: $filename"
        curl -X 'POST' "${TAGBASE_INGEST_BASE}/ingest?filename=${filename}" -H 'accept: application/json' -T "$line"
      done
  done
