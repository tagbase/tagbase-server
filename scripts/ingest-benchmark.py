#!/usr/bin/env python3
"""Benchmark large eTUFF ingests against a warm database snapshot (#477).

    ingest-benchmark.py snapshot    ingest every smoke member except the five
                                    large BFT files into an empty database,
                                    then archive the PostGIS data directory
    ingest-benchmark.py run         restore the archive, ingest the five large
                                    files in order, write run.tsv, timings.jsonl,
                                    settings.txt and hashes.json

TAGBASE_BENCH_DATA_DIR holds eTUFF_ICCAT-20260928T014825Z-1-00{1,2,3}.zip.
The snapshot is $TAGBASE_BENCH_DATA_DIR/snapshots/warm.tar and results go to
$TAGBASE_BENCH_DATA_DIR/results/<UTC time>-<git sha>/.

Uploads go through the nginx gateway (GATEWAY_URL, GATEWAY_USER, GATEWAY_PASS;
defaults https://localhost and tagbase/tagbase). There is no timeout: a large
file can take an hour. Ctrl-C cancels a running sp_execute_data_migration
instead of leaving it in the database.
"""

import argparse
import base64
import http.client
import json
import os
import re
import shutil
import signal
import ssl
import subprocess
import sys
import threading
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit

ROOT = Path(__file__).resolve().parents[1]
API = "/tagbase/api/v0"
PGDATA = "/var/lib/postgresql"
SCHEMA_SQL = ROOT / "services" / "postgis" / "tagbase_schema_tables.sql"
ZIP_GLOB = "eTUFF_ICCAT-20260928T014825Z-1-00[123].zip"
LARGE_FILES = [
    "2024BFT07891A_264262_23P2947.txt",
    "2024BFT07903A_265548_24P0087.txt",
    "2024BFT07902A_265536_24P0021.txt",
    "2024BFT07799A_264255_23P2610.txt",
    "2024BFT07801A_264258_23P2820.txt",
]
PHASES = ["read", "build_rows", "dataframe", "csv_buffer", "copy", "procedure"]
STEPS = [
    "defer_index",
    "time_series",
    "position_lon",
    "position_lat",
    "position_lon_err",
    "position_lat_err",
    "hist_bin_min",
    "hist_bin_max",
    "hist_bin_data",
    "profile_depth",
    "profile_temp_min",
    "profile_temp_max",
    "position_match_build",
    "position_update_time_series",
    "position_update_hist_bin_data",
    "position_update_profile",
    "index_rebuild",
]
PG_SETTINGS = [
    "shared_buffers",
    "work_mem",
    "maintenance_work_mem",
    "max_wal_size",
    "checkpoint_timeout",
    "effective_cache_size",
]
MEM_UNITS = {"B": 1 / 2**20, "KiB": 1 / 2**10, "MiB": 1, "GiB": 2**10, "TiB": 2**20}


def log(message):
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{stamp}] {message}", flush=True)


class Stack:
    def __init__(self, compose_files):
        self.flags = [arg for f in compose_files for arg in ("-f", f)]
        self.compose_files = compose_files

    def compose(self, *args, capture=False, input_text=None):
        return subprocess.run(
            ["docker", "compose", *self.flags, *args],
            cwd=ROOT,
            check=True,
            text=True,
            input=input_text,
            capture_output=capture,
        ).stdout

    def psql(self, sql):
        password = os.getenv("POSTGRES_PASSWORD", "tagbase")
        return self.compose(
            "exec",
            "-T",
            "-e",
            f"PGPASSWORD={password}",
            "postgis",
            "psql",
            "-h",
            "localhost",
            "-U",
            "tagbase",
            "-d",
            "tagbase",
            "-v",
            "ON_ERROR_STOP=1",
            "-tA",
            "-f",
            "-",
            capture=True,
            input_text=sql,
        )

    def container(self, service):
        return self.compose("ps", "-a", "-q", service, capture=True).strip()


class Gateway:
    def __init__(self):
        url = urlsplit(os.getenv("GATEWAY_URL", "https://localhost"))
        self.https = url.scheme == "https"
        self.host = url.hostname
        self.port = url.port or (443 if self.https else 80)
        user = os.getenv("GATEWAY_USER", "tagbase")
        password = os.getenv("GATEWAY_PASS", "tagbase")
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        self.auth = f"Basic {token}"

    def _connection(self, timeout):
        if self.https:
            return http.client.HTTPSConnection(
                self.host,
                self.port,
                timeout=timeout,
                context=ssl._create_unverified_context(),
                blocksize=1 << 20,
            )
        return http.client.HTTPConnection(
            self.host, self.port, timeout=timeout, blocksize=1 << 20
        )

    def request(self, method, path, body=None, headers=None, timeout=60):
        conn = self._connection(timeout)
        try:
            conn.request(
                method,
                API + path,
                body=body,
                headers={"Authorization": self.auth, **(headers or {})},
            )
            response = conn.getresponse()
            return response.status, response.read()
        finally:
            conn.close()

    def wait_ready(self, timeout=600):
        deadline = time.monotonic() + timeout
        probe = "/ingest/jobs/00000000-0000-0000-0000-000000000000"
        while time.monotonic() < deadline:
            try:
                status, _ = self.request("GET", probe, timeout=10)
                if status == 404:
                    return
            except OSError:
                pass
            time.sleep(5)
        raise RuntimeError("tagbase_server did not become ready behind the gateway")

    def ingest(self, path):
        query = urlencode({"filename": path.name, "version": "1", "type": "etuff"})
        started = time.perf_counter()
        with path.open("rb") as body:
            status, payload = self.request(
                "POST",
                f"/ingest/jobs?{query}",
                body=body,
                headers={
                    "Content-Type": "text/plain",
                    "Content-Length": str(path.stat().st_size),
                },
                timeout=1800,
            )
        upload_s = round(time.perf_counter() - started, 2)
        if status != 202:
            raise RuntimeError(f"upload of {path.name} returned {status}: {payload!r}")
        job_id = json.loads(payload)["id"]
        while True:
            time.sleep(10)
            status, payload = self.request("GET", f"/ingest/jobs/{job_id}")
            job = json.loads(payload)
            if job["status"] in ("succeeded", "failed"):
                return job, upload_s, round(time.perf_counter() - started, 2)


class MemorySampler(threading.Thread):
    def __init__(self, containers):
        super().__init__(daemon=True)
        self.containers = containers
        self.peaks = dict.fromkeys(containers, 0.0)
        self.stopped = threading.Event()

    @staticmethod
    def _mib(usage):
        match = re.match(r"([\d.]+)\s*([KMGT]?i?B)", usage)
        return float(match.group(1)) * MEM_UNITS.get(match.group(2), 0) if match else 0

    def run(self):
        ids = list(self.containers.values())
        while not self.stopped.is_set():
            out = subprocess.run(
                [
                    "docker",
                    "stats",
                    "--no-stream",
                    "--format",
                    "{{.ID}}\t{{.MemUsage}}",
                    *ids,
                ],
                capture_output=True,
                text=True,
            ).stdout
            for line in out.splitlines():
                cid, _, usage = line.partition("\t")
                for name, full_id in self.containers.items():
                    if full_id.startswith(cid):
                        self.peaks[name] = max(self.peaks[name], self._mib(usage))
            self.stopped.wait(5)

    def stop(self):
        self.stopped.set()
        self.join()
        return {name: round(peak) for name, peak in self.peaks.items()}


def zip_members(data_dir):
    zips = sorted(data_dir.glob(ZIP_GLOB))
    if len(zips) != 3:
        raise SystemExit(f"expected three {ZIP_GLOB} files in {data_dir}")
    members = {}
    for archive in zips:
        with zipfile.ZipFile(archive) as zf:
            for info in zf.infolist():
                if not info.is_dir() and info.filename.endswith(".txt"):
                    members[Path(info.filename).name] = (archive, info)
    return members


def extract(member, work_dir):
    archive, info = member
    target = work_dir / Path(info.filename).name
    with zipfile.ZipFile(archive) as zf, zf.open(info) as src, target.open("wb") as dst:
        shutil.copyfileobj(src, dst, 1 << 20)
    return target


def procedure_sql():
    text = SCHEMA_SQL.read_text(encoding="utf-8").replace("\r\n", "\n")
    start = text.index("CREATE OR REPLACE FUNCTION tagbase_migration_step")
    proc = text.index("PROCEDURE sp_execute_data_migration", start)
    return text[start : text.index("$BODY$;", proc) + len("$BODY$;")] + "\n"


def timings_for(stack, since, filename):
    logs = stack.compose(
        "logs", "--no-color", "--since", since, "tagbase_server", capture=True
    )
    found = {}
    for line in logs.splitlines():
        _, sep, payload = line.partition("ingest.timings ")
        if sep:
            try:
                record = json.loads(payload)
            except ValueError:
                continue
            if record.get("file") == filename:
                found = record
    return found


def cancel_migration(stack):
    log("cancelling any running sp_execute_data_migration")
    stack.psql(
        "SELECT pg_cancel_backend(pid) FROM pg_stat_activity "
        "WHERE query ILIKE 'CALL sp_execute_data_migration%' "
        "AND pid <> pg_backend_pid();"
    )


def ingest_files(stack, gateway, members, names, work_dir, on_result=None):
    containers = {s: stack.container(s) for s in ("tagbase_server", "postgis")}
    for name in names:
        path = extract(members[name], work_dir)
        since = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        sampler = MemorySampler(containers)
        sampler.start()
        log(f"ingesting {name} ({path.stat().st_size / 2**20:.1f} MiB)")
        try:
            job, upload_s, job_s = gateway.ingest(path)
        finally:
            peaks = sampler.stop()
            path.unlink(missing_ok=True)
        log(f"{name}: {job['status']} in {job_s} s")
        if job["status"] != "succeeded":
            log(f"{name}: {job.get('error', 'no error message')}")
        if on_result:
            on_result(
                name,
                members[name][1].file_size,
                job,
                upload_s,
                job_s,
                peaks,
                timings_for(stack, since, name),
            )


def archive_data_dir(stack, snapshot, restore):
    cid = stack.container("postgis")
    inspected = json.loads(
        subprocess.run(
            ["docker", "inspect", cid], check=True, capture_output=True, text=True
        ).stdout
    )[0]
    image = inspected["Config"]["Image"]
    (mount,) = [m for m in inspected["Mounts"] if m["Destination"] == PGDATA]
    source = mount["Name"] if mount["Type"] == "volume" else mount["Source"]
    if restore:
        script = f"find {PGDATA} -mindepth 1 -delete && tar -xpf /snap/{snapshot.name} -C {PGDATA}"
    else:
        script = f"tar -cf /snap/{snapshot.name} -C {PGDATA} ."
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--user",
            "0",
            "--entrypoint",
            "sh",
            "-v",
            f"{source}:{PGDATA}",
            "-v",
            f"{snapshot.parent}:/snap",
            image,
            "-c",
            script,
        ],
        check=True,
    )
    return image


def drop_caches(image):
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--privileged",
            "--user",
            "0",
            "--entrypoint",
            "sh",
            image,
            "-c",
            "sync; echo 3 > /proc/sys/vm/drop_caches",
        ],
        check=False,
    )


def cmd_snapshot(args, stack, gateway, data_dir):
    snapshot = data_dir / "snapshots" / "warm.tar"
    snapshot.parent.mkdir(exist_ok=True)
    if args.archive_only:
        stack.compose("stop")
        archive_data_dir(stack, snapshot, restore=False)
        stack.compose("up", "-d")
        log(f"wrote {snapshot}")
        return
    gateway.wait_ready()
    count = stack.psql("SELECT count(*) FROM submission;").strip()
    if count != "0":
        raise SystemExit(
            f"snapshot needs an empty database; submission has {count} rows"
        )
    stack.psql(procedure_sql())
    members = zip_members(data_dir)
    names = sorted(n for n in members if n not in LARGE_FILES)
    log(f"building snapshot from {len(names)} members")
    work_dir = data_dir / "tmp-bench"
    work_dir.mkdir(exist_ok=True)
    ingest_files(stack, gateway, members, names, work_dir)
    stack.psql("VACUUM ANALYZE; CHECKPOINT;")
    stack.compose("stop")
    archive_data_dir(stack, snapshot, restore=False)
    stack.compose("up", "-d")
    log(f"wrote {snapshot}")


def cmd_run(args, stack, gateway, data_dir):
    snapshot = data_dir / "snapshots" / "warm.tar"
    sha = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    ).stdout.strip()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out or data_dir / "results" / f"{stamp}-{sha}{args.label}")
    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_restore:
        if not snapshot.exists():
            raise SystemExit(f"{snapshot} is missing; run the snapshot command first")
        log("restoring warm snapshot")
        stack.compose("stop")
        image = archive_data_dir(stack, snapshot, restore=True)
        drop_caches(image)
        stack.compose("up", "-d")
    gateway.wait_ready()
    stack.psql(procedure_sql())
    stack.psql("VACUUM ANALYZE; CHECKPOINT;")

    settings = stack.psql(
        "SELECT name || ' = ' || setting || coalesce(unit, '') FROM pg_settings "
        f"WHERE name IN ({', '.join(repr(s) for s in PG_SETTINGS)}) ORDER BY name;"
    )
    docker_mem = subprocess.run(
        ["docker", "info", "--format", "{{.MemTotal}} {{.NCPU}}"],
        capture_output=True,
        text=True,
    ).stdout.split()
    (out_dir / "settings.txt").write_text(
        f"git {sha}\ndocker_mem_gib {int(docker_mem[0]) / 2**30:.2f}\n"
        f"docker_cpus {docker_mem[1]}\n{settings}",
        encoding="utf-8",
    )

    columns = [
        "file",
        "mib",
        "rows",
        "status",
        "upload_s",
        "job_s",
        *PHASES,
        *STEPS,
        "peak_api_mib",
        "peak_postgis_mib",
    ]
    tsv = (out_dir / "run.tsv").open("w", encoding="utf-8")
    tsv.write("\t".join(columns) + "\n")
    jsonl = (out_dir / "timings.jsonl").open("w", encoding="utf-8")

    def on_result(name, size, job, upload_s, job_s, peaks, timings):
        steps = {s["step"]: s.get("ms") for s in timings.get("procedure_steps", [])}
        row = [
            name,
            f"{size / 2**20:.1f}",
            timings.get("rows", ""),
            job["status"],
            upload_s,
            job_s,
            *(timings.get(p, "") for p in PHASES),
            *("" if steps.get(s) is None else round(steps[s] / 1000, 1) for s in STEPS),
            peaks["tagbase_server"],
            peaks["postgis"],
        ]
        tsv.write("\t".join(str(v) for v in row) + "\n")
        tsv.flush()
        jsonl.write(json.dumps({"job": job, "peaks": peaks, **timings}) + "\n")
        jsonl.flush()

    work_dir = data_dir / "tmp-bench"
    work_dir.mkdir(exist_ok=True)
    names = args.files or LARGE_FILES
    try:
        ingest_files(stack, gateway, zip_members(data_dir), names, work_dir, on_result)
    except KeyboardInterrupt:
        cancel_migration(stack)
        raise
    finally:
        tsv.close()
        jsonl.close()

    log("digesting data_* tables")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "ingest-equivalence.py"),
            *(arg for f in stack.compose_files for arg in ("--compose-file", f)),
            "dump",
            str(out_dir / "hashes.json"),
        ],
        cwd=ROOT,
        check=True,
    )
    log(f"results in {out_dir}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--compose-file",
        action="append",
        help="compose file(s) for the stack (default docker-compose.yml)",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    snapshot = sub.add_parser("snapshot")
    snapshot.add_argument(
        "--archive-only",
        action="store_true",
        help="archive the current database without ingesting",
    )
    run = sub.add_parser("run")
    run.add_argument("--out", help="results directory")
    run.add_argument("--label", default="", help="suffix for the results directory")
    run.add_argument(
        "--files", nargs="+", help="member names instead of the five large files"
    )
    run.add_argument(
        "--skip-restore", action="store_true", help="use the current database"
    )
    args = parser.parse_args(argv)

    data_dir = os.getenv("TAGBASE_BENCH_DATA_DIR")
    if not data_dir:
        raise SystemExit(
            "set TAGBASE_BENCH_DATA_DIR to the directory holding the smoke zips"
        )
    signal.signal(signal.SIGTERM, signal.default_int_handler)
    stack = Stack(args.compose_file or ["docker-compose.yml"])
    commands = {"snapshot": cmd_snapshot, "run": cmd_run}
    commands[args.command](args, stack, Gateway(), Path(data_dir).expanduser())
    return 0


if __name__ == "__main__":
    sys.exit(main())
