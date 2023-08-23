# coding: utf-8

import unittest
from unittest import mock

import psycopg2
import tagbase_server.utils.processing_utils as pu
import tagbase_server.utils.io_utils as io_utils


class TestIngest(unittest.TestCase):
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

    @mock.patch("builtins.open", create=True)
    def test_get_dataset_properties(self, mock_open):
        expected_property = (
            b':ptt = "117464"'
            b'\n:instrument_type = "s"'
            b"\n2012-03-16 18:31:39,2,22.2,longitude,degree"
            b"\n2012-03-16 18:31:39,3,-34.142,latitude,degree"
        )
        mock_open.side_effect = [
            mock.mock_open(read_data=expected_property).return_value
        ]
        (
            instrument_name,
            serial_number,
            ptt,
            platform,
            referenced_track_included,
            content,
            metadata_content,
            number_global_attributes_lines,
        ) = pu.get_dataset_properties("test_file")

        assert ptt, 117464
        assert instrument_name, "s"
        assert metadata_content
        assert expected_property, metadata_content[0]
        assert len(content), 2
        assert len(metadata_content), 2
        # TODO we use zero based indexing
        assert number_global_attributes_lines, 1
        assert (
            number_global_attributes_lines != 4
        ), "# of global attributes needs to be different to # of file lines"

    def test_compute_file_sha256(self):
        file_name = "/tmp/tmp_file.txt"
        with open(file_name, "w") as file_handler:
            file_handler.write("foo")
        file_sha256 = "b5bb9d8014a0f9b1d61e21e796d78dccdf1352f23cd32812f4850b878ae4944c"
        computed_file_sha256 = io_utils.compute_file_sha256(file_name)
        assert computed_file_sha256, file_sha256

    def test_make_python_object_sha256(self):
        some_dict = {"key": "value"}
        obj_sha256 = io_utils.make_hash_sha256(some_dict)
        expected_sha256 = "w+2rjvbC2Hy3LM9Azda0pif/ebnFey5joqfSwIpqwLM="
        assert obj_sha256, expected_sha256

    @mock.patch("psycopg2.connect")
    def test_get_dataset_id(self, mock_connect):
        # result of psycopg2.connect(**connection_stuff)
        mock_con = mock_connect.return_value
        # result of con.cursor(cursor_factory=DictCursor)
        mock_cur = mock_con.cursor.return_value
        # return this when calling cur.fetchall()
        mock_cur.fetchone.return_value = ["1"]

        conn = psycopg2.connect(
            dbname="test",
            user="test",
            host="localhost",
            port="32780",
            password="test",
        )
        cur = conn.cursor()
        tag_id = pu.get_tag_id(cur, 1)
        assert tag_id, "1"

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
        line_counter = 0

        metadata = pu.process_global_attributes_metadata(
            TestIngest.SAMPLE_METADATA_LINES,
            cur,
            TestIngest.fake_submission_id,
            TestIngest.fake_submission_filename,
            line_counter,
        )

        assert len(TestIngest.SAMPLE_METADATA_LINES), line_counter + 1
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

        has_duplicate = pu.detect_duplicate_file(mock_cur, computes_hash_sha256)
        assert has_duplicate, True
        has_no_duplicate = pu.detect_duplicate_file(mock_cur, "non-existing-hash")
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
        line_counter = 0

        pu.process_global_attributes_metadata(
            TestIngest.SAMPLE_METADATA_LINES,
            cur,
            TestIngest.fake_submission_id,
            TestIngest.fake_submission_filename,
            line_counter,
        )
        assert len(TestIngest.SAMPLE_METADATA_LINES), line_counter + 1


if __name__ == "__main__":
    unittest.main()
