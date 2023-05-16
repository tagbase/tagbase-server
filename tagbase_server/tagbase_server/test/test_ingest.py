# coding: utf-8

import builtins
import unittest
from unittest import mock

import psycopg2
import tagbase_server.utils.processing_utils as pu


class TestIngest(unittest.TestCase):
    SAMPLE_METADATA_LINES = [
        b"// global attributes:",
        b"// etag device attributes:",
        b':instrument_name = "159903_2012_117464"',
        b':instrument_type = "s"',
        b':manufacturer = "Wildlife"',
        b':model = "SPOT"',
        b':owner_contact = "a@a.org"',
        b':person_owner = "foo bar"',
        b':ptt = "117464"',
    ]

    fake_submission_id = 1
    fake_submission_filename = "test_file"

    @mock.patch.object(
        builtins,
        "open",
        new_callable=mock.mock_open,
        read_data=SAMPLE_METADATA_LINES[0],
    )
    def test_not_finding_any_global_attributes(self, mock_open):
        with mock_open(TestIngest.fake_submission_filename, "r") as f:
            global_attributes, processed_lines = pu._get_global_attributes(f)
            self.assertEquals(len(global_attributes), 0)
            self.assertEquals(processed_lines, 0)

    @mock.patch.object(
        builtins,
        "open",
        new_callable=mock.mock_open,
        read_data=SAMPLE_METADATA_LINES[2],
    )
    def test_finding_a_global_attributes(self, mock_open):
        with mock_open(TestIngest.fake_submission_filename, "r") as f:
            global_attributes, processed_lines = pu._get_global_attributes(f)
            self.assertEquals(len(global_attributes), 1)
            self.assertEquals(
                global_attributes[0], ':instrument_name = "159903_2012_117464"'
            )

    @mock.patch("psycopg2.connect")
    def test_processing_file_metadata_with_existing_attributes(self, mock_connect):
        metadata_attribs_in_db = [[1, "instrument_name"], [2, "model"]]
        # result of psycopg2.connect(**connection_stuff)
        mock_con = mock_connect.return_value
        # result of con.cursor(cursor_factory=DictCursor)
        mock_cur = mock_con.cursor.return_value
        # return this when calling cur.fetchall()
        mock_cur.fetchall.return_value = metadata_attribs_in_db

        conn = psycopg2.connect(
            dbname="test",
            user="test",
            host="localhost",
            port="32780",
            password="test",
        )
        cur = conn.cursor()

        metadata = []
        encoded_metadata_lines = [
            line.decode("utf-8") for line in TestIngest.SAMPLE_METADATA_LINES
        ]
        processed_lines = pu.process_all_lines_for_global_attributes(
            encoded_metadata_lines,
            cur,
            TestIngest.fake_submission_id,
            metadata,
            TestIngest.fake_submission_filename,
        )
        assert len(TestIngest.SAMPLE_METADATA_LINES), processed_lines + 1
        assert len(metadata_attribs_in_db), len(metadata)
        assert metadata[0][2], "159903_2012_117464"
        assert metadata[1][2], "SPOT"

    @mock.patch("psycopg2.connect")
    def test_processing_duplicate_file(self, mock_connect):
        computes_hash_sha256 = "some-hash-sha256"
        mock_con = mock_connect.return_value
        mock_cur = mock_con.cursor.return_value
        # duplicate stored in the db
        mock_cur.fetchone.return_value = computes_hash_sha256

        has_duplicate = pu.detect_duplicate(mock_cur, computes_hash_sha256)
        assert has_duplicate, True
        has_no_duplicate = pu.detect_duplicate(mock_cur, "non-existing-hash")
        assert has_no_duplicate, False

    @mock.patch("psycopg2.connect")
    def test_processing_file_metadata_without_attributes(self, mock_connect):
        metadata_attribs_in_db = []
        # result of psycopg2.connect(**connection_stuff)
        mock_con = mock_connect.return_value
        # result of con.cursor(cursor_factory=DictCursor)
        mock_cur = mock_con.cursor.return_value
        # return this when calling cur.fetchall()
        mock_cur.fetchall.return_value = metadata_attribs_in_db

        conn = psycopg2.connect(
            dbname="test",
            user="test",
            host="localhost",
            port="32780",
            password="test",
        )
        cur = conn.cursor()

        metadata = []
        encoded_metadata_lines = [
            line.decode("utf-8") for line in TestIngest.SAMPLE_METADATA_LINES
        ]
        processed_lines = pu.process_all_lines_for_global_attributes(
            encoded_metadata_lines,
            cur,
            TestIngest.fake_submission_id,
            metadata,
            TestIngest.fake_submission_filename,
        )
        assert len(TestIngest.SAMPLE_METADATA_LINES), processed_lines + 1


if __name__ == "__main__":
    unittest.main()
