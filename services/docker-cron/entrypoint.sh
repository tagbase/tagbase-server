#!/bin/sh
set -eu

POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-tagbase}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

# Runtime credentials for cron jobs (compose environment, not build ARGs).
cat > /usr/src/app/.env <<EOF
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
export POSTGRES_PORT=${POSTGRES_PORT}
EOF

echo "Seeding metadata_types and observation_types..."
i=0
until /usr/local/bin/python3 /usr/src/app/poll_metadata_and_obs_types.py; do
  i=$((i + 1))
  if [ "$i" -ge 30 ]; then
    echo "Initial seed failed after ${i} attempts; continuing with cron"
    break
  fi
  echo "Seed attempt ${i} failed; retrying in 5s..."
  sleep 5
done

echo "Starting cron..."
cron
echo "Cron started"

# Run forever
tail -f /dev/null
