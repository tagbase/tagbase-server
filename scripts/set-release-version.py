#!/usr/bin/env python3
"""Set package version and major-only HTTP API prefix for a semantic-release.

Usage: python3 scripts/set-release-version.py 0.15.0
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PREFIX_RE = re.compile(r"/tagbase/api/v\d+(?:\.\d+)*")
INFO_VERSION_RE = re.compile(r"(?m)^  version: v\d+\.\d+\.\d+$")
API_PREFIX_ASSIGN_RE = re.compile(r'(?m)^API_PREFIX = "/tagbase/api/v\d+"$')

PACKAGE_FILES = (
    (
        ROOT / "tagbase_server" / "pyproject.toml",
        re.compile(r'(?m)^version = "v[^"]+"$'),
    ),
    (ROOT / "tagbase_server" / "setup.py", re.compile(r'VERSION = "v[^"]+"')),
    (
        ROOT / "tagbase_server" / "tagbase_server" / "telemetry.py",
        re.compile(r'SERVICE_VERSION = "v[^"]+"'),
    ),
)

OPENAPI_FILES = (
    ROOT / "openapi.yaml",
    ROOT / "tagbase_server" / "tagbase_server" / "openapi" / "openapi.yaml",
)

PREFIX_FILES = (
    ROOT / "tagbase_server" / "tagbase_server" / "api_prefix.py",
    ROOT / "openapi.yaml",
    ROOT / "tagbase_server" / "tagbase_server" / "openapi" / "openapi.yaml",
    ROOT / "services" / "nginx" / "config" / "nginx.conf",
    ROOT / "services" / "nginx" / "config" / "nginx.test.conf",
    ROOT / "services" / "nginx" / "proxy" / "index.html",
    ROOT / "services" / "nginx" / "proxy" / "upload.html",
    ROOT / "docker-compose.test.yml",
    ROOT / ".github" / "workflows" / "build.yml",
    ROOT / "tagbase_server" / "README.md",
    ROOT / "services" / "fswatch" / "post.sh",
    ROOT / "scripts" / "observability-smoke.sh",
)


def parse_version(raw: str) -> str:
    ver = raw.strip()
    if ver.startswith("v"):
        ver = ver[1:]
    if not re.fullmatch(r"\d+\.\d+\.\d+", ver):
        raise SystemExit(f"version must be MAJOR.MINOR.PATCH, got: {raw!r}")
    return ver


def api_prefix(ver: str) -> str:
    major = int(ver.split(".", 1)[0])
    return f"/tagbase/api/v{major if major >= 1 else 0}"


def sub_one(path: Path, pattern: re.Pattern[str], repl: str) -> None:
    text = path.read_text(encoding="utf-8")
    new, n = pattern.subn(repl, text, count=1)
    if n != 1:
        raise SystemExit(f"{path}: expected 1 match for {pattern.pattern!r}, got {n}")
    path.write_text(new, encoding="utf-8")


def sub_all(path: Path, pattern: re.Pattern[str], repl: str) -> None:
    text = path.read_text(encoding="utf-8")
    new, n = pattern.subn(repl, text)
    if n < 1:
        raise SystemExit(f"{path}: expected at least 1 match for {pattern.pattern!r}")
    path.write_text(new, encoding="utf-8")


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        raise SystemExit("usage: python3 scripts/set-release-version.py <version>")
    ver = parse_version(argv[1])
    tagged = f"v{ver}"
    prefix = api_prefix(ver)

    for path, pattern in PACKAGE_FILES:
        if path.name == "pyproject.toml":
            sub_one(path, pattern, f'version = "{tagged}"')
        elif path.name == "setup.py":
            sub_one(path, pattern, f'VERSION = "{tagged}"')
        else:
            sub_one(path, pattern, f'SERVICE_VERSION = "{tagged}"')

    for path in OPENAPI_FILES:
        sub_one(path, INFO_VERSION_RE, f"  version: {tagged}")

    for path in PREFIX_FILES:
        if path.name == "api_prefix.py":
            sub_one(path, API_PREFIX_ASSIGN_RE, f'API_PREFIX = "{prefix}"')
        else:
            sub_all(path, PREFIX_RE, prefix)


if __name__ == "__main__":
    main(sys.argv)
