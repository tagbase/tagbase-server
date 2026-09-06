"""HTTP prefix is major-only, not the package version."""

from tagbase_server.api_prefix import API_PREFIX
from tagbase_server.test.helpers import API_PREFIX as HELPERS_PREFIX


def test_api_prefix_is_major_only():
    assert API_PREFIX == HELPERS_PREFIX
    assert API_PREFIX in ("/tagbase/api/v0", "/tagbase/api/v1")
    assert "v0.14" not in API_PREFIX
