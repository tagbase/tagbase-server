#!/usr/bin/env python3
"""Check that ingest produces the same data_* rows before and after a change.

    ingest-equivalence.py dump OUT.json     digest every submission's rows
    ingest-equivalence.py compare A B       exit 1 if two dumps differ
    ingest-equivalence.py positions         exit 1 if position_date_time differs
                                            from the pre-#437 correlated UPDATEs

To compare ingestion implementations:

1. Start with an empty database.
2. Ingest the same input files using the baseline implementation.
3. Run `dump baseline.json`.
4. Restore an empty database.
5. Ingest the same input files using the candidate implementation.
6. Run `dump candidate.json`.
7. Run `compare baseline.json candidate.json`.

The database must be reset between runs because duplicate submissions are not
supported.

Digests are order-independent sums of 64-bit row hashes, so they work on tables
with tens of millions of rows per submission. Rows are keyed by the submission's
file_sha256 and use variable_name rather than variable_id; submission_id,
tag_id and bin_id are sequence values that differ between runs. A dump is one
object per submission, not per row.

compare prints ``git diff --no-index`` of the two dump files and exits with
git's status: 0 when they match, 1 when they differ.

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
    """SQL for one row per table and submission: name, sha256, filename, count, digest.

    The session time zone is UTC so timestamp text does not follow the
    server's zone. The digest sums 64-bit md5 prefixes, which stays inside
    numeric and does not build one string over millions of rows.
    """
    parts = [f"""SELECT '{table}', file_sha256, max(filename), count(*),
               sum(('x' || left(md5(r), 16))::bit(64)::bigint::numeric)
        FROM ({query}) q GROUP BY file_sha256""" for table, query in TABLES.items()]
    return "SET TimeZone = 'UTC';\n" + "\nUNION ALL\n".join(parts) + ";"


def positions_sql():
    """SQL that counts rows whose position_date_time differs from the old lookup.

    The lookup is the pre-#437 correlated subquery: the latest data_position
    at or before the row's date_time, in the same submission.
    """
    parts = [f"""SELECT '{table}', count(*)
        FROM {table} t
        WHERE t.position_date_time IS DISTINCT FROM (
            SELECT dp.date_time FROM data_position dp
            WHERE dp.submission_id = t.submission_id
              AND dp.date_time <= t.date_time
            ORDER BY dp.date_time DESC LIMIT 1)""" for table in POSITION_TABLES]
    return "\nUNION ALL\n".join(parts) + ";"


def collect(run_query):
    """Turn digest_sql() into ``{file_sha256: {"filename", "tables"}}``.

    tables maps a table name to ``[row count, digest]``. run_query executes
    SQL and returns rows of strings.
    """
    result = {}
    for table, file_sha256, filename, count, digest in run_query(digest_sql()):
        entry = result.setdefault(file_sha256, {"filename": filename, "tables": {}})
        entry["tables"][table] = [int(count), str(digest)]
    return result


def compare(baseline, candidate):
    """Print a unified diff of two dump files and return git's exit status.

    baseline and candidate are paths. The dumps are one JSON object per
    submission, written with sorted keys, so the diff is stable. Status 0
    means they match and 1 means they differ. Any other status is git's own
    failure.
    """
    completed = subprocess.run(
        ["git", "diff", "--no-index", "--no-ext-diff", "--", baseline, candidate],
        check=False,
    )
    return completed.returncode


def psql_runner(args):
    """Return a function that runs SQL via compose exec, or via local psql with --local."""
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
        """Execute sql and return tab-separated data rows, skipping lines without a tab."""
        out = subprocess.run(
            [*command, "-v", "ON_ERROR_STOP=1", "-tA", "-F", "\t", "-c", sql],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        return [line.split("\t") for line in out.splitlines() if "\t" in line]

    return run


def main(argv=None):
    """dump writes JSON, compare prints a git diff, positions checks #437."""
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
        return compare(args.baseline, args.candidate)

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
