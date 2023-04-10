#!/usr/bin/env sh
PATH_TO_CHECK=/usr/src/app/staging_data/
while true
  do
    fswatch --one-event $PATH_TO_CHECK --event Created --event MovedTo --event IsFile --event Updated | while read line
      do
        filename="${line##*/}"
        echo "Contents of $PATH_TO_CHECK changed; Checking: $filename"

        # waiting for file to be fully uploaded
        while true
          do
            size_bfr=$(stat -c%s "$line")
            sleep 0.5
            size_aftr=$(stat -c%s "$line")
            if [ $size_bfr -eq $size_aftr ];
            then
                break;
            fi
          done

        echo "Processing: $filename"
        curl -X 'POST' tagbase_server:5433/tagbase/api/v0.10.0/ingest?filename="$filename" -H 'accept: application/json' -T $line
      done
  done
