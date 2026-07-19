#!/usr/bin/env bash
# Run the test suite and fail if coverage on lines changed vs the base
# branch is below 80% (mirrors the SonarCloud "Coverage on New Code" gate).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_DIR="${ROOT}/tagbase_server"
cd "${SERVER_DIR}"

COMPARE_BRANCH="${DIFF_COVER_COMPARE_BRANCH:-}"
if [[ -z "${COMPARE_BRANCH}" ]]; then
  if git -C "${ROOT}" rev-parse --verify --quiet origin/main >/dev/null; then
    COMPARE_BRANCH="origin/main"
  elif git -C "${ROOT}" rev-parse --verify --quiet main >/dev/null; then
    COMPARE_BRANCH="main"
  else
    echo "error: cannot find origin/main or main to compare against" >&2
    exit 1
  fi
fi

# Prefer an existing tox env; otherwise create one for the current Python.
TOX_ENV=""
for candidate in py314 py313 py312 py311 py310 py; do
  if [[ -x "${SERVER_DIR}/.tox/${candidate}/bin/python" ]]; then
    TOX_ENV="${candidate}"
    break
  fi
done

if [[ -z "${TOX_ENV}" ]]; then
  if ! command -v tox >/dev/null 2>&1; then
    python3 -m pip install --user --quiet 'tox>=4'
  fi
  tox -e py --notest
  TOX_ENV="$(basename "$(ls -d "${SERVER_DIR}"/.tox/py* | head -1)")"
fi

ENV_BIN="${SERVER_DIR}/.tox/${TOX_ENV}/bin"
"${ENV_BIN}/python" -m pip install --quiet 'diff-cover==10.3.0'

COVERAGE_XML="${SERVER_DIR}/tagbase_server/coverage.xml"
rm -f "${COVERAGE_XML}"

"${ENV_BIN}/pytest" \
  --cov-config=.coveragerc \
  --cov=tagbase_server \
  --cov-branch \
  --cov-report="xml:${COVERAGE_XML}" \
  --cov-report=term-missing:skip-covered \
  -q

# Coverage XML filenames are package-relative (e.g. models/tag200.py).
# Rewrite them to repo-root paths so diff-cover can match git diff output.
python3 - "${COVERAGE_XML}" <<'PY'
import pathlib
import sys
import xml.etree.ElementTree as ET

coverage_xml = pathlib.Path(sys.argv[1])
prefix = "tagbase_server/tagbase_server/"
tree = ET.parse(coverage_xml)
root = tree.getroot()
for cls in root.iter("class"):
    filename = cls.attrib.get("filename", "")
    if not filename or filename.startswith(prefix):
        continue
    if filename.startswith("tagbase_server/"):
        cls.set("filename", f"tagbase_server/{filename}")
    else:
        cls.set("filename", f"{prefix}{filename}")
tree.write(coverage_xml)
PY

cd "${ROOT}"
echo "Comparing coverage for changes against ${COMPARE_BRANCH}..."
"${ENV_BIN}/diff-cover" "${COVERAGE_XML}" \
  --compare-branch="${COMPARE_BRANCH}" \
  --fail-under=80 \
  --include='tagbase_server/tagbase_server/**' \
  --exclude='tagbase_server/tagbase_server/test/**'
