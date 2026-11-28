"""The init dump must not rewind live id sequences on a second container start."""

from pathlib import Path

_SCHEMA = (
    Path(__file__).resolve().parents[3]
    / "services"
    / "postgis"
    / "tagbase_schema_tables.sql"
)
_COMPOSE_FILES = (
    Path(__file__).resolve().parents[3] / "docker-compose.yml",
    Path(__file__).resolve().parents[3] / "docker-compose.publish.yml",
)


def test_schema_does_not_rewind_sequences_to_one():
    schema = _SCHEMA.read_text()
    assert "setval('submission_tag_id_seq', 1" not in schema
    assert "setval('observation_types_variable_id_seq', 1" not in schema


def test_db_migrate_advances_tag_and_dataset_sequences():
    for path in _COMPOSE_FILES:
        text = path.read_text()
        assert "'submission_tag_id_seq'" in text
        assert "'dataset_dataset_id_seq'" in text
        assert "COALESCE(MAX(tag_id), 1)" in text
        assert "COALESCE(MAX(dataset_id), 1)" in text
