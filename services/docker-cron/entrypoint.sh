#!/bin/sh

echo "Starting cron..."
cron
echo "Cron started"

# Run forever
tail -f /dev/null