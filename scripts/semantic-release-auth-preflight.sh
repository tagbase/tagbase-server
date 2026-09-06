#!/usr/bin/env bash
# Refuse an empty RELEASE_TOKEN or one that authenticates as github-actions[bot].
# git push --dry-run does not trigger GH006 on protected main; this check does.
set -euo pipefail

if [[ -z "${RELEASE_TOKEN:-}" ]]; then
	echo "RELEASE_TOKEN is empty. Create a classic PAT (repo scope) as lewismc and:" >&2
	echo "  gh secret set RELEASE_TOKEN --repo tagbase/tagbase-server" >&2
	exit 1
fi

login="$(GH_TOKEN="${RELEASE_TOKEN}" gh api user --jq .login)"
if [[ -z "${login}" || "${login}" == "github-actions[bot]" ]]; then
	echo "RELEASE_TOKEN authenticates as '${login:-<empty>}'; need a human admin PAT, not GITHUB_TOKEN." >&2
	exit 1
fi
echo "semantic-release will push as ${login}"
