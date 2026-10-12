"""Shared eTUFF archive handling for synchronous ingest and the job worker.

Allowed inputs are .txt, .zip, .tar.gz, and .tgz. The logical filename and
the file's magic bytes decide the format. A temporary path suffix does not.
"""

from __future__ import annotations

import os
import shutil
import stat
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath

from tagbase_server.utils.io_utils import TEMP_DIR

_ZIP_MAGIC = b"PK"
_GZIP_MAGIC = b"\x1f\x8b"
_DEFAULT_MAX_MEMBERS = 10_000
_DEFAULT_MAX_UNCOMPRESSED = 10 * 1024 * 1024 * 1024
_READ_CHUNK = 1024 * 1024
_INVALID_FILENAME = "invalid filename"
_NO_ETUFF_MEMBERS = "archive contained no eTUFF files"
_CORRUPT_ARCHIVE = "archive is corrupt or unreadable"


class ArchiveError(ValueError):
    """The upload is empty, the wrong type, or an unsafe archive."""


@dataclass
class PreparedIngest:
    """eTUFF members ready to parse, plus an extraction directory to delete."""

    files: list[str]
    workspace: str | None
    names: list[str] | None = None

    def submission_names(self) -> list[str]:
        """Names stored on submission rows.

        Archive members keep their path inside the archive.
        """
        if self.names is None:
            return [os.path.basename(path) for path in self.files]
        if len(self.names) != len(self.files):
            raise RuntimeError("ingest names do not match extracted files")
        return list(self.names)

    def cleanup(self) -> None:
        if self.workspace:
            shutil.rmtree(self.workspace)


def archive_limits() -> tuple[int, int]:
    members = int(os.environ.get("TAGBASE_ARCHIVE_MAX_MEMBERS", _DEFAULT_MAX_MEMBERS))
    expanded = int(
        os.environ.get(
            "TAGBASE_ARCHIVE_MAX_UNCOMPRESSED",
            str(_DEFAULT_MAX_UNCOMPRESSED),
        )
    )
    return members, expanded


def logical_filename(name: str) -> str:
    """Reject blank names and any path, keeping a single basename."""
    if name is None:
        raise ArchiveError(_INVALID_FILENAME)
    text = str(name).strip()
    if not text or text in {".", ".."} or "/" in text or "\\" in text:
        raise ArchiveError(_INVALID_FILENAME)
    base = os.path.basename(text)
    if base != text:
        raise ArchiveError(_INVALID_FILENAME)
    return base


def classify(path: str, filename: str) -> str:
    """Return etuff, zip, or tar after the name and magic bytes agree."""
    logical = logical_filename(filename)
    lowered = logical.lower()
    if lowered.endswith((".tar.gz", ".tgz")):
        expected = "tar"
    elif lowered.endswith(".zip"):
        expected = "zip"
    elif lowered.endswith(".txt"):
        expected = "etuff"
    else:
        raise ArchiveError(
            "unsupported file type; allowed types are .txt, .zip, .tar.gz, and .tgz"
        )
    sniffed = _sniff(path)
    if expected == "etuff" and sniffed != "text":
        raise ArchiveError("file contents do not match the .txt filename")
    if expected == "zip" and sniffed != "zip":
        raise ArchiveError("file contents do not match the .zip filename")
    if expected == "tar" and sniffed != "gzip":
        raise ArchiveError("file contents do not match the archive filename")
    return expected


def preflight(path: str, filename: str) -> str:
    """Reject an empty, unsupported, or unsafe upload without extracting it."""
    kind = classify(path, filename)
    if os.path.getsize(path) == 0:
        raise ArchiveError("request body is empty")
    if kind == "zip":
        _inspect_zip(path)
    elif kind == "tar":
        _inspect_tar(path)
    return kind


def materialize(path: str, filename: str) -> PreparedIngest:
    """Validate the upload and return the eTUFF files to parse."""
    kind = preflight(path, filename)
    if kind == "etuff":
        return PreparedIngest(
            files=[path],
            workspace=None,
            names=[logical_filename(filename)],
        )
    workspace = tempfile.mkdtemp(dir=TEMP_DIR, prefix="tagbase-archive-")
    try:
        if kind == "zip":
            members = _extract_zip(path, workspace)
        else:
            members = _extract_tar(path, workspace)
    except Exception:
        shutil.rmtree(workspace, ignore_errors=True)
        raise
    if not members:
        shutil.rmtree(workspace, ignore_errors=True)
        raise ArchiveError(_NO_ETUFF_MEMBERS)
    return PreparedIngest(
        files=[member_path for member_path, _name in members],
        workspace=workspace,
        names=[name for _member_path, name in members],
    )


def _sniff(path: str) -> str:
    with open(path, "rb") as handle:
        header = handle.read(8)
    if not header:
        raise ArchiveError("request body is empty")
    if header.startswith(_ZIP_MAGIC):
        return "zip"
    if header.startswith(_GZIP_MAGIC):
        return "gzip"
    return "text"


def _member_name(name: str) -> str:
    parts = PurePosixPath(name).parts
    if (
        not name
        or name.startswith("/")
        or name.startswith("\\")
        or ".." in parts
        or "\\" in name
    ):
        raise ArchiveError(f"archive member path is not allowed: {name}")
    return str(PurePosixPath(*parts))


def _limits_exceeded(count: int, declared: int) -> None:
    max_members, max_uncompressed = archive_limits()
    if count > max_members:
        raise ArchiveError("archive has too many members")
    if declared > max_uncompressed:
        raise ArchiveError("archive uncompressed size exceeds the configured cap")


def _inspect_zip(path: str) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            declared = 0
            txts = 0
            for index, info in enumerate(infos, start=1):
                _reject_zip_member(info)
                if not info.is_dir():
                    declared += info.file_size
                    if info.filename.endswith(".txt"):
                        txts += 1
                _limits_exceeded(index, declared)
    except zipfile.BadZipFile as exc:
        raise ArchiveError(_CORRUPT_ARCHIVE) from exc
    if txts == 0:
        raise ArchiveError(_NO_ETUFF_MEMBERS)


def _reject_zip_member(info: zipfile.ZipInfo) -> None:
    if info.flag_bits & 0x1:
        raise ArchiveError("encrypted ZIP members are not allowed")
    _member_name(info.filename)
    mode = info.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise ArchiveError("symlink archive members are not allowed")


def _extract_zip(path: str, workspace: str) -> list[tuple[str, str]]:
    files: list[tuple[str, str]] = []
    written = 0
    _, max_uncompressed = archive_limits()
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            _reject_zip_member(info)
            if info.is_dir():
                continue
            relative = _member_name(info.filename)
            target = os.path.join(workspace, relative)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with archive.open(info) as source, open(target, "wb") as dest:
                while True:
                    chunk = source.read(_READ_CHUNK)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > max_uncompressed:
                        raise ArchiveError("extracted bytes exceed the configured cap")
                    dest.write(chunk)
            if relative.endswith(".txt"):
                files.append((target, relative))
    return files


def _inspect_tar(path: str) -> None:
    try:
        with tarfile.open(path, "r:gz") as archive:
            declared = 0
            txts = 0
            count = 0
            for member in archive:
                count += 1
                _reject_tar_member(member)
                if member.isfile():
                    declared += member.size
                    if member.name.endswith(".txt"):
                        txts += 1
                _limits_exceeded(count, declared)
    except (tarfile.TarError, OSError) as exc:
        raise ArchiveError(_CORRUPT_ARCHIVE) from exc
    if txts == 0:
        raise ArchiveError(_NO_ETUFF_MEMBERS)


def _reject_tar_member(member: tarfile.TarInfo) -> None:
    if member.issym() or member.islnk():
        raise ArchiveError("symlink archive members are not allowed")
    _member_name(member.name)


def _extract_tar(path: str, workspace: str) -> list[tuple[str, str]]:
    files: list[tuple[str, str]] = []
    written = 0
    _, max_uncompressed = archive_limits()
    with tarfile.open(path, "r:gz") as archive:
        for member in archive:
            _reject_tar_member(member)
            if not member.isfile():
                continue
            relative = _member_name(member.name)
            target = os.path.join(workspace, relative)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise ArchiveError(_CORRUPT_ARCHIVE)
            with source, open(target, "wb") as dest:
                while True:
                    chunk = source.read(_READ_CHUNK)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > max_uncompressed:
                        raise ArchiveError("extracted bytes exceed the configured cap")
                    dest.write(chunk)
            if relative.endswith(".txt"):
                files.append((target, relative))
    return files
