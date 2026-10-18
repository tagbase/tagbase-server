# coding: utf-8

import io
import os
import stat
import tarfile
import zipfile

import pytest

from tagbase_server.archives import (
    ArchiveError,
    archive_limits,
    materialize,
    preflight,
)


def _zip(path, members):
    with zipfile.ZipFile(path, "w") as archive:
        for info, payload in members:
            archive.writestr(info, payload)


def test_archive_limits_default_to_ten_thousand_and_ten_gib():
    members, expanded = archive_limits()
    assert members == 10_000
    assert expanded == 10 * 1024 * 1024 * 1024


def test_plain_text_materialize_returns_the_file(tmp_path):
    path = tmp_path / "tag.txt"
    path.write_text("etuff", encoding="utf-8")
    prepared = materialize(str(path), "tag.txt")
    assert prepared.files == [str(path)]
    assert prepared.submission_names() == ["tag.txt"]
    assert prepared.workspace is None


def test_staged_text_keeps_the_logical_name(tmp_path):
    path = tmp_path / "5fb7423d15d9452dbfdc81d9a1c2c995-tagbase-upload-cjz5__3y"
    path.write_text("etuff", encoding="utf-8")
    prepared = materialize(str(path), "2024BFT07799A.txt")
    assert prepared.files == [str(path)]
    assert prepared.submission_names() == ["2024BFT07799A.txt"]


def test_zip_extracts_txt_and_cleanup_removes_workspace(tmp_path):
    archive = tmp_path / "bundle.zip"
    _zip(archive, [(zipfile.ZipInfo("inner.txt"), b"etuff")])
    prepared = materialize(str(archive), "bundle.zip")
    try:
        assert len(prepared.files) == 1
        assert prepared.files[0].endswith("inner.txt")
        assert prepared.submission_names() == ["inner.txt"]
        assert os.path.isdir(prepared.workspace)
    finally:
        workspace = prepared.workspace
        prepared.cleanup()
    assert not os.path.exists(workspace)


def test_zip_member_name_keeps_its_directory(tmp_path):
    archive = tmp_path / "bundle.zip"
    _zip(archive, [(zipfile.ZipInfo("cruise/inner.txt"), b"etuff")])
    prepared = materialize(str(archive), "bundle.zip")
    try:
        assert prepared.submission_names() == ["cruise/inner.txt"]
    finally:
        prepared.cleanup()


def test_tar_gz_and_tgz_extract_txt(tmp_path):
    for name in ("bundle.tar.gz", "bundle.tgz"):
        archive = tmp_path / name
        with tarfile.open(archive, "w:gz") as tar:
            payload = b"etuff"
            info = tarfile.TarInfo("inner.txt")
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))
        prepared = materialize(str(archive), name)
        try:
            assert prepared.files[0].endswith("inner.txt")
            assert prepared.submission_names() == ["inner.txt"]
        finally:
            prepared.cleanup()


def test_rejects_path_traversal_symlink_and_encrypted_zip(tmp_path):
    traversal = tmp_path / "traversal.zip"
    info = zipfile.ZipInfo("../evil.txt")
    _zip(traversal, [(info, b"x")])
    with pytest.raises(ArchiveError, match="path"):
        preflight(str(traversal), "traversal.zip")

    link = tmp_path / "link.zip"
    info = zipfile.ZipInfo("link.txt")
    info.external_attr = stat.S_IFLNK << 16
    _zip(link, [(info, b"target")])
    with pytest.raises(ArchiveError, match="symlink"):
        preflight(str(link), "link.zip")

    encrypted = tmp_path / "secret.zip"
    _zip(encrypted, [(zipfile.ZipInfo("secret.txt"), b"x")])
    raw = bytearray(encrypted.read_bytes())
    raw[6] |= 0x1
    central = raw.find(b"PK\x01\x02")
    raw[central + 8] |= 0x1
    encrypted.write_bytes(raw)
    with pytest.raises(ArchiveError, match="encrypted"):
        preflight(str(encrypted), "secret.zip")


def test_rejects_tar_traversal_and_symlink(tmp_path):
    traversal = tmp_path / "traversal.tar.gz"
    with tarfile.open(traversal, "w:gz") as tar:
        info = tarfile.TarInfo("../evil.txt")
        info.size = 1
        tar.addfile(info, io.BytesIO(b"x"))
    with pytest.raises(ArchiveError, match="path"):
        preflight(str(traversal), "traversal.tar.gz")

    link = tmp_path / "link.tgz"
    with tarfile.open(link, "w:gz") as tar:
        info = tarfile.TarInfo("link.txt")
        info.type = tarfile.SYMTYPE
        info.linkname = "inner.txt"
        tar.addfile(info)
    with pytest.raises(ArchiveError, match="symlink"):
        preflight(str(link), "link.tgz")


def test_member_and_expanded_size_caps(tmp_path, monkeypatch):
    monkeypatch.setenv("TAGBASE_ARCHIVE_MAX_MEMBERS", "1")
    archive = tmp_path / "many.zip"
    _zip(
        archive,
        [
            (zipfile.ZipInfo("a.txt"), b"a"),
            (zipfile.ZipInfo("b.txt"), b"b"),
        ],
    )
    with pytest.raises(ArchiveError, match="too many members"):
        preflight(str(archive), "many.zip")

    monkeypatch.setenv("TAGBASE_ARCHIVE_MAX_MEMBERS", "10")
    monkeypatch.setenv("TAGBASE_ARCHIVE_MAX_UNCOMPRESSED", "4")
    large = tmp_path / "large.zip"
    _zip(large, [(zipfile.ZipInfo("big.txt"), b"12345")])
    with pytest.raises(ArchiveError, match="uncompressed"):
        preflight(str(large), "large.zip")


def test_rejects_corrupt_empty_and_mismatched_types(tmp_path):
    corrupt = tmp_path / "bad.zip"
    corrupt.write_bytes(b"not-a-zip")
    with pytest.raises(ArchiveError):
        preflight(str(corrupt), "bad.zip")

    empty = tmp_path / "empty.txt"
    empty.write_bytes(b"")
    with pytest.raises(ArchiveError, match="empty"):
        preflight(str(empty), "empty.txt")

    disguised = tmp_path / "notes.txt"
    disguised.write_bytes(b"PK\x03\x04nope")
    with pytest.raises(ArchiveError, match="do not match"):
        preflight(str(disguised), "notes.txt")

    with pytest.raises(ArchiveError, match="unsupported"):
        preflight(str(disguised), "notes.csv")
