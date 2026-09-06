"""set-release-version.py maps 0.x → /v0 and 1.x → /v1."""

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "set-release-version.py"
_spec = importlib.util.spec_from_file_location("set_release_version", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)


def test_api_prefix_zero_and_one():
    assert _mod.api_prefix("0.14.0") == "/tagbase/api/v0"
    assert _mod.api_prefix("0.99.0") == "/tagbase/api/v0"
    assert _mod.api_prefix("1.0.0") == "/tagbase/api/v1"
    assert _mod.api_prefix("2.3.4") == "/tagbase/api/v2"


def test_parse_version_strips_v():
    assert _mod.parse_version("v0.15.0") == "0.15.0"
    assert _mod.parse_version("0.15.0") == "0.15.0"
