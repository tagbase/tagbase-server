# coding: utf-8

import logging
import os
from pathlib import Path
from unittest import mock

import psycopg2
import pytest
from connexion import FlaskApp
from connexion.options import SwaggerUIOptions

from tagbase_server import encoder

OPENAPI_DIR = Path(__file__).resolve().parents[1] / "openapi"
_FIXTURES = Path(__file__).resolve().parent / "fixtures"
ETUFF_FIXTURE = _FIXTURES / "etuff" / "minimal-etuff.txt"
ETUFF_ZIP_FIXTURE = _FIXTURES / "etuff" / "minimal-etuff.zip"

METADATA_TYPE_SEED = [
    (1, "device", "instrument_name", "Instrument name", "req"),
    (2, "device", "serial_number", "Serial number", "req"),
    (3, "device", "instrument_type", "Instrument type", "opt"),
    (4, "device", "manufacturer", "Manufacturer", "opt"),
    (5, "device", "model", "Model", "opt"),
    (6, "device", "owner_contact", "Owner contact", "opt"),
    (7, "device", "person_owner", "Person owner", "opt"),
    (8, "device", "ptt", "PTT", "req"),
    (9, "device", "platform", "Platform", "req"),
    (10, "device", "referencetrack_included", "Reference track", "opt"),
]


def create_test_app():
    """Build a Connexion FlaskApp for tests."""
    logging.getLogger("connexion.operation").setLevel("ERROR")
    swagger_ui_options = SwaggerUIOptions(swagger_ui=False)
    app = FlaskApp(
        __name__,
        specification_dir=str(OPENAPI_DIR),
        swagger_ui_options=swagger_ui_options,
        jsonifier=encoder.create_jsonifier(),
    )
    app.add_api("openapi.yaml", pythonic_params=True, strict_validation=True)
    return app


def _pg_connect_kwargs():
    return {
        "dbname": "tagbase",
        "user": "tagbase",
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "password": os.getenv("POSTGRES_PASSWORD", "tagbase"),
    }


def postgres_available():
    try:
        conn = psycopg2.connect(**_pg_connect_kwargs())
        conn.close()
        return True
    except Exception:
        return False


@pytest.fixture
def app():
    return create_test_app()


@pytest.fixture
def client(app):
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def etuff_bytes():
    return ETUFF_FIXTURE.read_bytes()


@pytest.fixture
def etuff_path():
    return ETUFF_FIXTURE


@pytest.fixture
def etuff_zip_bytes():
    return ETUFF_ZIP_FIXTURE.read_bytes()


@pytest.fixture(autouse=True)
def mute_slack(monkeypatch):
    monkeypatch.setenv("SLACK_BOT_TOKEN", "")
    monkeypatch.setattr(
        "tagbase_server.utils.slack_utils.post_msg",
        mock.Mock(return_value=None),
    )
    monkeypatch.setattr(
        "tagbase_server.utils.processing_utils.post_msg",
        mock.Mock(return_value=None),
    )


@pytest.fixture(scope="session")
def postgres_env():
    """Point the app at the test database (host default localhost for CI/local)."""
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    os.environ.setdefault("POSTGRES_PORT", "5432")
    os.environ.setdefault("POSTGRES_PASSWORD", "tagbase")
    os.environ.setdefault("PGADMIN_DEFAULT_EMAIL", "test@example.com")
    return _pg_connect_kwargs()


@pytest.fixture
def db_conn(postgres_env):
    if not postgres_available():
        pytest.skip("Postgres not available for integration tests")
    conn = psycopg2.connect(**postgres_env)
    conn.autocommit = True
    yield conn
    conn.close()


@pytest.fixture
def clean_db(db_conn):
    """Reset mutable ingest tables; keep metadata_types / observation_types seeds."""
    with db_conn.cursor() as cur:
        cur.execute("TRUNCATE submission CASCADE")
        cur.execute("TRUNCATE dataset CASCADE")
        for attribute_id, category, name, description, necessity in METADATA_TYPE_SEED:
            cur.execute(
                """
                INSERT INTO metadata_types
                    (attribute_id, category, attribute_name, description, necessity)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (attribute_id, category, name, description, necessity),
            )
    yield db_conn
