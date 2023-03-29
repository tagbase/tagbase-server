# coding: utf-8

import unittest
from unittest import mock

import psycopg2
import tagbase_server.utils.processing_utils as pu


class TestIngest(unittest.TestCase):
    PG_VERSION = "postgres:9.5"
    SAMPLE_METADATA_LINES = [
        "// global attributes:",
        "// etag device attributes:",
        ':instrument_name = "159903_2012_117464"',
        ':instrument_type = "s"',
        ':manufacturer = "Wildlife"',
        ':model = "SPOT"',
        ':owner_contact = "a@a.org"',
        ':person_owner = "foo bar"',
        ':ptt = "117464"',
    ]

    fake_submission_id = 1
    fake_submission_filename = "test_file"

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
        processed_lines = pu.process_global_attributes(
            TestIngest.SAMPLE_METADATA_LINES,
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
        processed_lines = pu.process_global_attributes(
            TestIngest.SAMPLE_METADATA_LINES,
            cur,
            TestIngest.fake_submission_id,
            metadata,
            TestIngest.fake_submission_filename,
        )
        assert len(TestIngest.SAMPLE_METADATA_LINES), processed_lines + 1


if __name__ == "__main__":
    unittest.main()
