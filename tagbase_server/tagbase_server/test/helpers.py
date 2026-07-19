# coding: utf-8

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
ETUFF_FIXTURE = FIXTURES_DIR / "etuff" / "minimal-etuff.txt"
ETUFF_ZIP_FIXTURE = FIXTURES_DIR / "etuff" / "minimal-etuff.zip"
API_PREFIX = "/tagbase/api/v0.14.0"


def response_json(response):
    return json.loads(response.content)
