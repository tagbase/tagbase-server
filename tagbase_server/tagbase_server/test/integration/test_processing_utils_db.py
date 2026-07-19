# coding: utf-8

import pytest

import tagbase_server.utils.processing_utils as pu
from tagbase_server.test.helpers import ETUFF_FIXTURE
from tagbase_server.utils.io_utils import compute_file_sha256, make_hash_sha256

pytestmark = pytest.mark.integration


def test_get_dataset_properties_reads_etuff_fixture():
    (
        instrument_name,
        serial_number,
        ptt,
        platform,
        referencetrack_included,
        content,
        metadata_content,
        number_global_attributes_lines,
    ) = pu.get_dataset_properties(str(ETUFF_FIXTURE))
    assert instrument_name == "test_instrument_117464"
    assert serial_number == "SN117464"
    assert ptt == "117464"
    assert platform == "Istiophorus platypterus"
    assert referencetrack_included == 0
    assert len(content) == 3
    assert any(line.startswith(":ptt") for line in metadata_content)
    assert number_global_attributes_lines >= 0


def test_detect_duplicate_file_roundtrip(clean_db):
    file_hash = compute_file_sha256(str(ETUFF_FIXTURE))
    with clean_db.cursor() as cur:
        assert pu.detect_duplicate_file(cur, file_hash) is False
        dataset_id = pu.get_dataset_id(
            cur,
            "test_instrument_117464",
            "SN117464",
            "117464",
            "Istiophorus platypterus",
        )
        tag_id = pu.get_tag_id(cur, dataset_id)
        pu.insert_new_submission(
            cur,
            tag_id,
            "minimal-etuff.txt",
            "notes",
            "1",
            file_hash,
            dataset_id,
            make_hash_sha256(["md"]),
            make_hash_sha256(["data"]),
        )
        assert pu.detect_duplicate_file(cur, file_hash) is True


def test_dataset_tag_submission_ids(clean_db):
    with clean_db.cursor() as cur:
        dataset_id = pu.get_dataset_id(cur, "inst-a", "sn-a", "ptt-a", "plat-a")
        tag_id = pu.get_tag_id(cur, dataset_id)
        assert dataset_id is not None
        assert tag_id is not None
        assert pu.get_submission_id(cur, tag_id, dataset_id, "missing-hash") is None
        pu.insert_new_submission(
            cur,
            tag_id,
            "file.txt",
            None,
            None,
            "file-hash",
            dataset_id,
            "md-hash",
            "data-hash",
        )
        submission_id = pu.get_current_submission_id(cur)
        assert (
            pu.get_submission_id(cur, tag_id, dataset_id, "data-hash") == submission_id
        )


def test_process_global_attributes_and_metadata_insert(clean_db):
    lines = [
        ':instrument_name = "test_instrument_117464"',
        ':ptt = "117464"',
        ':unknown_attr = "x"',
    ]
    with clean_db.cursor() as cur:
        dataset_id = pu.get_dataset_id(cur, "inst-b", "sn-b", "ptt-b", "plat-b")
        tag_id = pu.get_tag_id(cur, dataset_id)
        pu.insert_new_submission(
            cur,
            tag_id,
            "file.txt",
            None,
            "1",
            "fh",
            dataset_id,
            "mh",
            "dh",
        )
        submission_id = pu.get_current_submission_id(cur)
        metadata = pu.process_global_attributes_metadata(
            lines, cur, submission_id, "file.txt", 0
        )
        assert len(metadata) == 2
        pu.insert_metadata(cur, metadata, tag_id)
        cur.execute(
            "SELECT attribute_value FROM metadata WHERE submission_id = %s ORDER BY attribute_id",
            (submission_id,),
        )
        values = [row[0] for row in cur.fetchall()]
        assert "test_instrument_117464" in values
        assert "117464" in values


def test_is_only_metadata_change_and_update(clean_db):
    with clean_db.cursor() as cur:
        dataset_id = pu.get_dataset_id(cur, "inst-c", "sn-c", "ptt-c", "plat-c")
        tag_id = pu.get_tag_id(cur, dataset_id)
        pu.insert_new_submission(
            cur,
            tag_id,
            "file.txt",
            None,
            "1",
            "fh",
            dataset_id,
            "old-md",
            "same-data",
        )
        submission_id = pu.get_current_submission_id(cur)
        assert pu.is_only_metadata_change(cur, "new-md", "same-data") is True
        assert pu.is_only_metadata_change(cur, "old-md", "other-data") is False

        metadata = [(str(submission_id), "1", '"new-value"')]
        # attribute_id 1 must exist from seed
        cur.execute(
            "INSERT INTO metadata (submission_id, attribute_id, attribute_value, tag_id) "
            "VALUES (%s, %s, %s, %s)",
            (submission_id, 1, "old-value", tag_id),
        )
        pu.update_submission_metadata(
            cur, tag_id, metadata, submission_id, dataset_id, "new-md"
        )
        cur.execute(
            "SELECT md_sha256 FROM submission WHERE submission_id = %s",
            (submission_id,),
        )
        assert cur.fetchone()[0] == "new-md"


def test_process_etuff_file_ingests_and_skips_duplicate(clean_db):
    first = pu.process_etuff_file(str(ETUFF_FIXTURE), version="1", notes="pu test")
    assert first is None
    assert pu.process_etuff_file(str(ETUFF_FIXTURE), version="1", notes="pu test") == 1
    with clean_db.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM submission")
        assert cur.fetchone()[0] == 1
