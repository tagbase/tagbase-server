#!/usr/bin/env sh
PATH_TO_CHECK=/usr/src/app/staging_data/
while true
  do
    #fswatch --one-event $PATH_TO_CHECK --event Created --event MovedTo --event IsFile --event Updated | while read line
    #fswatch --one-event $PATH_TO_CHECK | while read line
    fswatch --batch-marker=EOF --event-flags --numeric --event Updated --event IsFile $PATH_TO_CHECK | while read file event; do
      echo $file $event
      if [ $file = "EOF" ]; then 
        #do
          #filename="${file##*/}"
        echo "Contents of $PATH_TO_CHECK changed; Processing: $file"
          # curl -X 'POST' tagbase_server:5433/tagbase/api/v0.9.0/ingest?filename="$filename" -H 'accept: application/json' -T $line
        #done
      fi
    done
  done
