#!/usr/bin/env bash
# Run Super Linter via Docker (pre-commit / local). Shares config with CI:
#   .github/super-linter.env + image tag aligned with .github/workflows/super-linter.yml
#
# CI uses VALIDATE_ALL_CODEBASE=true from the env file. This wrapper overrides to
# false so commits only lint changes vs DEFAULT_BRANCH (faster feedback).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${SUPER_LINTER_IMAGE:-ghcr.io/super-linter/super-linter:v8.7.0}"

if ! command -v docker >/dev/null 2>&1; then
	echo "super-linter pre-commit: docker is required but not on PATH" >&2
	exit 1
fi

# -e after --env-file wins for VALIDATE_ALL_CODEBASE
exec docker run --rm \
	-e RUN_LOCAL=true \
	--env-file "${ROOT}/.github/super-linter.env" \
	-e VALIDATE_ALL_CODEBASE=false \
	-v "${ROOT}:/tmp/lint" \
	"${IMAGE}"
