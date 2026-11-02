#!/usr/bin/env python3
"""Benchmark large eTUFF ingests against a warm database snapshot (#477).

    ingest-benchmark.py snapshot    ingest every smoke member except the five
                                    large BFT files into an empty database,
                                    then archive the PostGIS data directory
    ingest-benchmark.py run         restore the archive and ingest one large
                                    file (pass --files for more), then write
                                    run.tsv, timings.jsonl, settings.txt and
                                    hashes.json

TAGBASE_BENCH_DATA_DIR holds eTUFF_ICCAT-20260928T014825Z-1-00{1,2,3}.zip.
The snapshot is $TAGBASE_BENCH_DATA_DIR/snapshots/warm.tar and results go to
$TAGBASE_BENCH_DATA_DIR/results/<UTC time>-<git sha>/.

Uploads go through the nginx gateway (GATEWAY_URL, GATEWAY_USER, GATEWAY_PASS;
defaults https://localhost and tagbase/tagbase). There is no timeout: a large
file can take an hour. Ctrl-C cancels a running sp_execute_data_migration
instead of leaving it in the database.

The harness does not install SQL. A restored snapshot keeps the procedure it
was archived with. After a procedure edit, recreate the stack so init SQL
reloads and rebuild the snapshot, or apply the procedure yourself and pass
--skip-restore.

data_time_series_date_time_index and data_time_series_pos_date_time_index are
database-wide. A large submission drops them until the migration rebuilds
them, so this stack must not ingest anything else during a run.
"""

import argparse
import base64
import http.client
import json
import logging
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
ZIP_GLOB = "eTUFF_ICCAT-20260928T014825Z-1-00[123].zip"
logger = logging.getLogger("ingest-benchmark")
ROUTINES = (
    "tagbase_migration_step(text,timestamptz,bigint)",
    "sp_execute_data_migration(integer,boolean)",
)
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


class Stack:
    """The docker compose project this benchmark starts, queries, and stops.

    compose_files are passed as repeated ``-f`` flags. SQL runs as the tagbase
    user inside the postgis service.
    """

    def __init__(self, compose_files):
        """Remember the compose files. The default, when empty, is docker-compose.yml."""
        self.flags = [arg for f in compose_files for arg in ("-f", f)]
        self.compose_files = compose_files

    def compose(self, *args, capture=False, input_text=None):
        """Run docker compose from the repo root. Return stdout when capture is set."""
        return subprocess.run(
            ["docker", "compose", *self.flags, *args],
            cwd=ROOT,
            check=True,
            text=True,
            input=input_text,
            capture_output=capture,
        ).stdout

    def psql(self, sql):
        """Execute sql on the tagbase database and return its tuples-only stdout."""
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
        """Return the full container id of one compose service."""
        return self.compose("ps", "-a", "-q", service, capture=True).strip()


class Gateway:
    """HTTP client for the nginx gateway in front of tagbase_server.

    GATEWAY_URL, GATEWAY_USER, and GATEWAY_PASS override the defaults
    (https://localhost, tagbase/tagbase). The local gateway certificate is
    self-signed, so TLS is not verified.
    """

    def __init__(self):
        """Read the gateway URL and basic-auth settings from the environment."""
        url = urlsplit(os.getenv("GATEWAY_URL", "https://localhost"))
        self.https = url.scheme == "https"
        self.host = url.hostname
        self.port = url.port or (443 if self.https else 80)
        user = os.getenv("GATEWAY_USER", "tagbase")
        password = os.getenv("GATEWAY_PASS", "tagbase")
        token = base64.b64encode(f"{user}:{password}".encode()).decode()
        self.auth = f"Basic {token}"

    def _connection(self, timeout):
        """Open one connection. A 1 MiB block streams a body of about 1 GB."""
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
        """Send one request under /tagbase/api/v0. Return the status and body bytes."""
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
        """Block until a missing ingest job returns 404, which means the API is up."""
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
        """Upload one eTUFF file and poll its job until the job succeeds or fails.

        Return the job object, the seconds spent uploading, and the seconds
        from the start of the upload until the job is terminal. Polling has
        no deadline, because a large file can take an hour.
        """
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
    """Sample docker stats every five seconds and keep each container's peak memory."""

    def __init__(self, containers):
        """containers maps a compose service name to its full container id."""
        super().__init__(daemon=True)
        self.containers = containers
        self.peaks = dict.fromkeys(containers, 0.0)
        self.stopped = threading.Event()

    @staticmethod
    def _mib(usage):
        """Parse a docker stats memory field such as ``8.5GiB`` into mebibytes."""
        match = re.match(r"([\d.]+)\s*([KMGT]?i?B)", usage)
        return float(match.group(1)) * MEM_UNITS.get(match.group(2), 0) if match else 0

    def run(self):
        """Poll docker stats until stop() and record the peak for each named container."""
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
        """Stop sampling and return peak mebibytes, rounded, keyed by compose service."""
        self.stopped.set()
        self.join()
        return {name: round(peak) for name, peak in self.peaks.items()}


def zip_members(data_dir):
    """Map each .txt name in the three smoke zips to ``(archive path, ZipInfo)``."""
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
    """Write one zip member into work_dir and return that path."""
    archive, info = member
    target = work_dir / Path(info.filename).name
    with zipfile.ZipFile(archive) as zf, zf.open(info) as src, target.open("wb") as dst:
        shutil.copyfileobj(src, dst, 1 << 20)
    return target


def procedure_fingerprints(stack):
    """Return one ``signature md5`` line per installed migration routine.

    Fail when either routine is missing. The harness does not install SQL.
    Executing ``pg_get_functiondef`` would only repeat what is already loaded,
    so a working-tree edit is not applied here.
    """
    lines = []
    for signature in ROUTINES:
        try:
            digest = stack.psql(
                "SELECT md5(pg_get_functiondef(" f"'{signature}'::regprocedure));"
            ).strip()
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "").strip()
            raise SystemExit(f"{signature} is not installed: {detail}") from exc
        lines.append(f"{signature} {digest}")
    return "\n".join(lines) + "\n"


def timings_for(stack, since, filename):
    """Return the ingest.timings object for filename from logs since an ISO time.

    Lines for other files are ignored. An empty dict means the worker did not
    finish the file, which is what a failed job leaves behind.
    """
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
    """Cancel any backend that is still inside sp_execute_data_migration."""
    logger.info("cancelling any running sp_execute_data_migration")
    stack.psql(
        "SELECT pg_cancel_backend(pid) FROM pg_stat_activity "
        "WHERE query ILIKE 'CALL sp_execute_data_migration%' "
        "AND pid <> pg_backend_pid();"
    )


def ingest_files(
    stack, gateway, members, names, work_dir, on_result=None, sample_memory=False
):
    """Ingest each name in order, then delete the extracted file.

    on_result, when set, receives the member name, its zip size, the job, the
    upload seconds, the job seconds, the memory peaks, and the timings record.
    Memory is sampled only when sample_memory is set, and only for
    tagbase_server and postgis while that file's job is running. A job that
    does not succeed is recorded, then the run stops, so later files cannot
    make the results look complete.
    """
    containers = {s: stack.container(s) for s in ("tagbase_server", "postgis")}
    for name in names:
        path = extract(members[name], work_dir)
        since = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        sampler = MemorySampler(containers) if sample_memory else None
        if sampler:
            sampler.start()
        logger.info("ingesting %s (%.1f MiB)", name, path.stat().st_size / 2**20)
        try:
            job, upload_s, job_s = gateway.ingest(path)
        finally:
            peaks = sampler.stop() if sampler else {}
            path.unlink(missing_ok=True)
        logger.info("%s: %s in %s s", name, job["status"], job_s)
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
        if job["status"] != "succeeded":
            raise SystemExit(f"{name}: {job.get('error', 'no error message')}")


def archive_data_dir(stack, snapshot, restore):
    """Tar the PostGIS data directory, or replace that directory from snapshot.

    A helper container mounts the volume by name. ``--volumes-from`` does not
    work here: the postgis service also has a tmpfs mount. Return the postgis
    image name so the caller can drop the VM page cache with that image.
    """
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
    """Ask the Docker VM to drop its page cache. A failure does not stop the run."""
    completed = subprocess.run(
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
        capture_output=True,
        text=True,
    )
    logger.info(
        "drop_caches exit %s\n%s%s",
        completed.returncode,
        completed.stdout,
        completed.stderr,
    )


def cmd_snapshot(args, stack, gateway, data_dir):
    """Write snapshots/warm.tar from every smoke member except the five large files.

    --archive-only tars the database as it stands, so an interrupted build can
    be saved without ingesting again. A full build requires an empty
    submission table.
    """
    snapshot = data_dir / "snapshots" / "warm.tar"
    snapshot.parent.mkdir(exist_ok=True)
    if args.archive_only:
        stack.compose("stop")
        archive_data_dir(stack, snapshot, restore=False)
        stack.compose("up", "-d")
        logger.info("wrote %s", snapshot)
        return
    gateway.wait_ready()
    count = stack.psql("SELECT count(*) FROM submission;").strip()
    if count != "0":
        raise SystemExit(
            f"snapshot needs an empty database; submission has {count} rows"
        )
    logger.info("%s", procedure_fingerprints(stack).strip())
    members = zip_members(data_dir)
    names = sorted(n for n in members if n not in LARGE_FILES)
    logger.info("building snapshot from %s members", len(names))
    work_dir = data_dir / "tmp-bench"
    work_dir.mkdir(exist_ok=True)
    ingest_files(stack, gateway, members, names, work_dir)
    stack.psql("VACUUM ANALYZE; CHECKPOINT;")
    stack.compose("stop")
    archive_data_dir(stack, snapshot, restore=False)
    stack.compose("up", "-d")
    logger.info("wrote %s", snapshot)


def cmd_run(args, stack, gateway, data_dir):
    """Restore the warm snapshot, ingest the selected files, and write the results.

    The procedure already in the database is the one that runs. It is recorded
    by md5 in settings.txt and is not replaced from the schema file. The
    database is vacuumed and checkpointed before ingest. Ctrl-C cancels a
    migration that is still running. hashes.json is produced by
    ingest-equivalence.py.
    """
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
        logger.info("restoring warm snapshot")
        stack.compose("stop")
        image = archive_data_dir(stack, snapshot, restore=True)
        drop_caches(image)
        stack.compose("up", "-d")
    gateway.wait_ready()
    fingerprints = procedure_fingerprints(stack)
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
        f"docker_cpus {docker_mem[1]}\n{settings}{fingerprints}",
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
        """Append one TSV row and one timings JSON line, and flush both."""
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
            peaks.get("tagbase_server", ""),
            peaks.get("postgis", ""),
        ]
        tsv.write("\t".join(str(v) for v in row) + "\n")
        tsv.flush()
        jsonl.write(json.dumps({"job": job, "peaks": peaks, **timings}) + "\n")
        jsonl.flush()

    work_dir = data_dir / "tmp-bench"
    work_dir.mkdir(exist_ok=True)
    names = args.files or LARGE_FILES[:1]
    try:
        ingest_files(
            stack,
            gateway,
            zip_members(data_dir),
            names,
            work_dir,
            on_result,
            sample_memory=args.sample_memory,
        )
    except KeyboardInterrupt:
        cancel_migration(stack)
        raise
    finally:
        tsv.close()
        jsonl.close()

    logger.info("digesting data_* tables")
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
    logger.info("results in %s", out_dir)


def main(argv=None):
    """Parse arguments and run snapshot or run. TAGBASE_BENCH_DATA_DIR is required."""
    logging.Formatter.converter = time.gmtime
    logging.basicConfig(
        format="%(asctime)s %(message)s", datefmt="%H:%M:%S", level=logging.INFO
    )
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
        "--files",
        nargs="+",
        help="member names instead of the one default large file",
    )
    run.add_argument(
        "--sample-memory",
        action="store_true",
        help="sample docker stats while each job runs",
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
