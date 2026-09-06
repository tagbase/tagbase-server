#!/usr/bin/env bash
# Exit 0 and print skip=true when a scheduled run is within 14 days of the last v* tag.
# workflow_dispatch always continues. No tags → continue.
set -euo pipefail

EVENT_NAME="${1:-}"
if [[ "${EVENT_NAME}" != "schedule" ]]; then
	echo "skip=false"
	exit 0
fi

latest="$(git tag --list 'v[0-9]*' --sort=-v:refname | head -n 1 || true)"
if [[ -z "${latest}" ]]; then
	echo "skip=false"
	exit 0
fi

tag_epoch="$(git log -1 --format=%ct "${latest}")"
now_epoch="$(date +%s)"
age_days="$(((now_epoch - tag_epoch) / 86400))"
if ((age_days < 14)); then
	echo "Last tag ${latest} is ${age_days} day(s) old (< 14); skipping scheduled release." >&2
	echo "skip=true"
	exit 0
fi
echo "skip=false"
