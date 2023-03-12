#!/usr/bin/env sh
PATH_TO_CHECK=/usr/src/app/staging_data
while true
  do
    fswatch --one-event $PATH_TO_CHECK --event Created --event MovedTo --event IsFile | while read line
      do
      	filename="${line##*/}"
        echo "Contents of $PATH_TO_CHECK changed; Processing: $line"
        curl -X 'POST' tagbase_server:5433/tagbase/api/v0.8.0/ingest?filename="$filename" -H 'accept: application/json' -T $line
      done
  done
