"""Public HTTP prefix: major-only (`/tagbase/api/v0` until 1.0.0, then `/v1`, …).

Package version lives in pyproject / OpenAPI info.version, not in this path.
Updated by ``scripts/set-release-version.py`` during semantic-release.
"""

API_PREFIX = "/tagbase/api/v0"
