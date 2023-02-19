#!/usr/bin/env sh
while true
  do
    fswatch --one-event /usr/src/app/staging_data | while read line
      do
      	filename="${line##*/}"
        echo "Contents of /usr/src/app/staging_data changed; Processing: $line"
        curl -X 'POST' tagbase_server:5433/tagbase/api/v0.7.0/ingest?filename="$filename" -H 'accept: application/json' -T $line
      done
  done
