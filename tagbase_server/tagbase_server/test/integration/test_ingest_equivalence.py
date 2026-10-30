# coding: utf-8

import importlib.util
from pathlib import Path

import pytest

import tagbase_server.utils.processing_utils as pu
from tagbase_server.test.helpers import ETUFF_FIXTURE

pytestmark = pytest.mark.integration

SCRIPT = Path(__file__).resolve().parents[4] / "scripts" / "ingest-equivalence.py"


@pytest.fixture
def equivalence():
    if not SCRIPT.exists():
        pytest.skip("scripts/ingest-equivalence.py is not in this checkout")
    spec = importlib.util.spec_from_file_location("ingest_equivalence", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _runner(conn):
    def run(sql):
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

    return run


def _ingest_fixture(conn):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE submission CASCADE")
        cur.execute("TRUNCATE dataset CASCADE")
    assert pu.process_etuff_file(str(ETUFF_FIXTURE), version="1") is None


def test_reingest_matches_and_changes_are_detected(clean_db, equivalence):
    run = _runner(clean_db)
    _ingest_fixture(clean_db)
    first = equivalence.collect(run)
    (entry,) = first.values()
    assert entry["filename"] == "minimal-etuff.txt"
    assert entry["tables"]["data_time_series"][0] == 1
    assert entry["tables"]["data_position"][0] == 1

    _ingest_fixture(clean_db)
    assert equivalence.compare(first, equivalence.collect(run)) == []

    with clean_db.cursor() as cur:
        cur.execute("UPDATE data_position SET lat = '0.0'")
    differences = equivalence.compare(first, equivalence.collect(run))
    assert differences == [
        "minimal-etuff.txt: data_position rows 1 -> 1, digest differs"
    ]


def test_position_dates_match_correlated_update(clean_db, equivalence):
    _ingest_fixture(clean_db)
    mismatches = dict(_runner(clean_db)(equivalence.positions_sql()))
    assert mismatches == {
        "data_time_series": 0,
        "data_histogram_bin_data": 0,
        "data_profile": 0,
    }
