# coding: utf-8

import json
from pathlib import Path

from tagbase_server.api_prefix import API_PREFIX

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
ETUFF_FIXTURE = FIXTURES_DIR / "etuff" / "minimal-etuff.txt"
ETUFF_ZIP_FIXTURE = FIXTURES_DIR / "etuff" / "minimal-etuff.zip"

__all__ = [
    "API_PREFIX",
    "ETUFF_FIXTURE",
    "ETUFF_ZIP_FIXTURE",
    "FIXTURES_DIR",
    "response_json",
]


def response_json(response):
    return json.loads(response.content)
