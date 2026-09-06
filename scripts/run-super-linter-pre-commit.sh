#!/usr/bin/env bash
# Run Super Linter via Docker (pre-commit / local). Shares config with CI:
#   .github/super-linter.env + image tag aligned with .github/workflows/super-linter.yml
#
# CI uses VALIDATE_ALL_CODEBASE=true from the env file (full workspace).
# This wrapper lints only staged paths passed by pre-commit, and disables
# Checkov, JSCPD, and Trivy (they ignore include filters and scan everything).
# Super Linter builds its file list from git *commit* data, not the index, so
# brand-new files are skipped if we mount the working tree. Lint a throwaway
# snapshot that has those paths committed instead.
# If Docker is missing or the daemon is down, skip (CI still lints) unless
# SUPER_LINTER_REQUIRE_DOCKER=1.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${SUPER_LINTER_IMAGE:-ghcr.io/super-linter/super-linter:v8.7.0}"
# Official Super Linter images are linux/amd64 only (same pin as docker-compose).
PLATFORM="${SUPER_LINTER_PLATFORM:-linux/amd64}"
ENV_FILE="${ROOT}/.github/super-linter.env"
REQUIRE_DOCKER="${SUPER_LINTER_REQUIRE_DOCKER:-0}"

normalize_path() {
	local f="$1"
	f="${f#"${ROOT}/"}"
	f="${f#./}"
	printf '%s' "${f}"
}

EXCLUDE_REGEX="$(
	grep -E '^FILTER_REGEX_EXCLUDE=' "${ENV_FILE}" | sed 's/^FILTER_REGEX_EXCLUDE=//'
)"

is_excluded() {
	local f="$1"
	if [[ -z "${EXCLUDE_REGEX}" ]]; then
		return 1
	fi
	[[ "${f}" =~ ${EXCLUDE_REGEX} ]]
}

escape_regex() {
	# Escape ERE metacharacters in a repo-relative path.
	printf '%s' "$1" | sed -e 's/[].[^$*+?(){}|\\]/\\&/g'
}

lintable=()
for arg in "$@"; do
	rel="$(normalize_path "${arg}")"
	if [[ -z "${rel}" ]]; then
		continue
	fi
	if is_excluded "${rel}"; then
		continue
	fi
	lintable+=("${rel}")
done

if [[ ${#lintable[@]} -eq 0 ]]; then
	echo "super-linter pre-commit: no lintable staged files, skipping"
	exit 0
fi

docker_unavailable() {
	local reason="$1"
	if [[ "${REQUIRE_DOCKER}" == "1" ]]; then
		echo "super-linter pre-commit: ${reason}" >&2
		exit 1
	fi
	echo "super-linter pre-commit: ${reason}; skipping (CI still lints)" >&2
	exit 0
}

if ! command -v docker >/dev/null 2>&1; then
	docker_unavailable "docker not on PATH"
fi
if ! docker info >/dev/null 2>&1; then
	docker_unavailable "docker daemon not running"
fi
if ! command -v git >/dev/null 2>&1; then
	echo "super-linter pre-commit: git not on PATH" >&2
	exit 1
fi

# BASH_EXEC cannot fail inside the container on a macOS bind mount: the linter
# runs as root, where test -x passes even on mode 644. Check the committed mode
# here instead so a non-executable shell script fails locally, not on CI.
exec_bit_errors=0
for rel in "${lintable[@]}"; do
	src="${ROOT}/${rel}"
	[[ -f "${src}" ]] || continue
	if [[ "${rel}" != *.sh ]] && ! head -c 2 "${src}" | grep -q '^#!'; then
		continue
	fi
	if [[ "${rel}" == *.sh ]] || head -n 1 "${src}" | grep -qE '^#!.*\b(ba)?sh$'; then
		if [[ ! -x "${src}" ]]; then
			echo "super-linter pre-commit: ${rel} is not executable (BASH_EXEC fails on CI)" >&2
			echo "  fix: chmod +x ${rel} && git update-index --chmod=+x ${rel}" >&2
			exec_bit_errors=1
		fi
	fi
done
if [[ "${exec_bit_errors}" == "1" ]]; then
	exit 1
fi

include_parts=()
for rel in "${lintable[@]}"; do
	include_parts+=("$(escape_regex "${rel}")")
done
include_joined="$(
	IFS='|'
	printf '%s' "${include_parts[*]}"
)"
# Anchor to the workspace root so e.g. README.md does not also match
# tagbase_server/README.md.
FILTER_REGEX_INCLUDE="^(/tmp/lint/)?(${include_joined})$"

snap="$(mktemp -d "${TMPDIR:-/tmp}/super-linter-snap.XXXXXX")"
cleanup() {
	rm -rf "${snap}"
}
trap cleanup EXIT

# Index first (pre-commit's staged tree), then overlay requested working-tree
# files so untracked paths and hand-invoked unstaged edits are present.
git -C "${ROOT}" checkout-index --all --prefix="${snap}/"
for rel in "${lintable[@]}"; do
	src="${ROOT}/${rel}"
	if [[ -f "${src}" ]]; then
		mkdir -p "${snap}/$(dirname "${rel}")"
		cp -p "${src}" "${snap}/${rel}"
	fi
done

GIT_TERMINAL_PROMPT=0 git -C "${snap}" \
	-c init.defaultBranch=main \
	init -q
GIT_TERMINAL_PROMPT=0 git -C "${snap}" add -A
GIT_TERMINAL_PROMPT=0 git -C "${snap}" \
	-c user.email=super-linter@local \
	-c user.name=super-linter \
	-c commit.gpgsign=false \
	commit -qm "super-linter snapshot"

# -e after --env-file wins. Do not exec: the EXIT trap must remove the snapshot.
docker run --rm \
	--platform "${PLATFORM}" \
	-e RUN_LOCAL=true \
	--env-file "${ENV_FILE}" \
	-e VALIDATE_ALL_CODEBASE=true \
	-e FILTER_REGEX_INCLUDE="${FILTER_REGEX_INCLUDE}" \
	-e VALIDATE_CHECKOV=false \
	-e VALIDATE_JSCPD=false \
	-e VALIDATE_TRIVY=false \
	-v "${snap}:/tmp/lint" \
	"${IMAGE}"
