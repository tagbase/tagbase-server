#!/usr/bin/env python3
"""Check that ingest produces the same data_* rows before and after a change.

    ingest-equivalence.py dump OUT.json     digest every submission's rows
    ingest-equivalence.py compare A B       exit 1 if two dumps differ
    ingest-equivalence.py positions         exit 1 if position_date_time differs
                                            from the pre-#437 correlated UPDATEs

Digests are order-independent sums of 64-bit row hashes, so they work on tables
with tens of millions of rows per submission. Rows are keyed by the submission's
file_sha256 and use variable_name rather than variable_id; submission_id,
tag_id and bin_id are sequence values that differ between runs.

psql runs inside the postgis compose service by default (--compose-file may be
repeated; --service). Use --local to run the psql on PATH with PG* variables.
"""

import argparse
import json
import os
import subprocess
import sys

TABLES = {
    "data_time_series": """
        SELECT s.file_sha256, s.filename,
               ROW(t.date_time, o.variable_name, t.variable_value,
                   t.position_date_time)::text AS r
        FROM data_time_series t
        JOIN submission s ON s.submission_id = t.submission_id
        JOIN observation_types o ON o.variable_id = t.variable_id""",
    "data_position": """
        SELECT s.file_sha256, s.filename,
               ROW(t.date_time, t.lat, t.lon, t.lat_err, t.lon_err,
                   t.argos_location_class, t.flag_as_reference)::text AS r
        FROM data_position t
        JOIN submission s ON s.submission_id = t.submission_id""",
    "data_histogram_bin_info": """
        SELECT s.file_sha256, s.filename,
               ROW(t.bin_class, t.min_value, t.max_value,
                   o.variable_name)::text AS r
        FROM data_histogram_bin_info t
        JOIN submission s ON s.submission_id = t.bin_id
        LEFT JOIN observation_types o ON o.variable_id = t.variable_id""",
    "data_histogram_bin_data": """
        SELECT s.file_sha256, s.filename,
               ROW(t.bin_class, t.date_time, t.variable_value,
                   t.position_date_time, o.variable_name)::text AS r
        FROM data_histogram_bin_data t
        JOIN submission s ON s.submission_id = t.submission_id
        JOIN observation_types o ON o.variable_id = t.variable_id""",
    "data_profile": """
        SELECT s.file_sha256, s.filename,
               ROW(o.variable_name, t.date_time, t.depth, t.variable_value,
                   t.position_date_time)::text AS r
        FROM data_profile t
        JOIN submission s ON s.submission_id = t.submission_id
        JOIN observation_types o ON o.variable_id = t.variable_id""",
}

POSITION_TABLES = ("data_time_series", "data_histogram_bin_data", "data_profile")


def digest_sql():
    parts = [f"""SELECT '{table}', file_sha256, max(filename), count(*),
               sum(('x' || left(md5(r), 16))::bit(64)::bigint::numeric)
        FROM ({query}) q GROUP BY file_sha256""" for table, query in TABLES.items()]
    return "SET TimeZone = 'UTC';\n" + "\nUNION ALL\n".join(parts) + ";"


def positions_sql():
    parts = [f"""SELECT '{table}', count(*)
        FROM {table} t
        WHERE t.position_date_time IS DISTINCT FROM (
            SELECT dp.date_time FROM data_position dp
            WHERE dp.submission_id = t.submission_id
              AND dp.date_time <= t.date_time
            ORDER BY dp.date_time DESC LIMIT 1)""" for table in POSITION_TABLES]
    return "\nUNION ALL\n".join(parts) + ";"


def collect(run_query):
    """Return {file_sha256: {"filename": ..., "tables": {table: [count, digest]}}}."""
    result = {}
    for table, file_sha256, filename, count, digest in run_query(digest_sql()):
        entry = result.setdefault(file_sha256, {"filename": filename, "tables": {}})
        entry["tables"][table] = [int(count), str(digest)]
    return result


def compare(baseline, candidate):
    """Return human-readable differences between two dumps (empty when equal)."""
    differences = []
    for key in sorted(set(baseline) | set(candidate)):
        a = baseline.get(key)
        b = candidate.get(key)
        name = (a or b)["filename"]
        if a is None or b is None:
            side = "baseline" if a is None else "candidate"
            differences.append(f"{name}: missing from {side}")
            continue
        for table in sorted(set(a["tables"]) | set(b["tables"])):
            left = a["tables"].get(table, [0, "0"])
            right = b["tables"].get(table, [0, "0"])
            if left != right:
                differences.append(
                    f"{name}: {table} rows {left[0]} -> {right[0]}, "
                    f"digest {'same' if left[1] == right[1] else 'differs'}"
                )
    return differences


def psql_runner(args):
    if args.local:
        command = ["psql"]
    else:
        command = [
            "docker",
            "compose",
            *(
                arg
                for f in args.compose_file or ["docker-compose.yml"]
                for arg in ("-f", f)
            ),
            "exec",
            "-T",
            "-e",
            f"PGPASSWORD={os.getenv('POSTGRES_PASSWORD', 'tagbase')}",
            args.service,
            "psql",
            "-h",
            "localhost",
            "-U",
            "tagbase",
            "-d",
            "tagbase",
        ]

    def run(sql):
        out = subprocess.run(
            [*command, "-v", "ON_ERROR_STOP=1", "-tA", "-F", "\t", "-c", sql],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        return [line.split("\t") for line in out.splitlines() if "\t" in line]

    return run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--compose-file", action="append")
    parser.add_argument("--service", default="postgis")
    parser.add_argument("--local", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("dump").add_argument("out")
    cmp_parser = sub.add_parser("compare")
    cmp_parser.add_argument("baseline")
    cmp_parser.add_argument("candidate")
    sub.add_parser("positions")
    args = parser.parse_args(argv)

    if args.command == "compare":
        with open(args.baseline, encoding="utf-8") as a, open(
            args.candidate, encoding="utf-8"
        ) as b:
            differences = compare(json.load(a), json.load(b))
        for line in differences:
            print(line)
        print("MATCH" if not differences else f"{len(differences)} difference(s)")
        return 1 if differences else 0

    run = psql_runner(args)
    if args.command == "dump":
        result = collect(run)
        with open(args.out, "w", encoding="utf-8") as out:
            json.dump(result, out, indent=1, sort_keys=True)
        print(f"wrote {len(result)} submission(s) to {args.out}")
        return 0

    mismatches = {table: int(count) for table, count in run(positions_sql())}
    for table, count in mismatches.items():
        print(f"{table}: {count} row(s) differ from the correlated UPDATE")
    return 1 if any(mismatches.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
