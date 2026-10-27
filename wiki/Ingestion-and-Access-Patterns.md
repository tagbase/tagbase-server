# Introduction

In developing tagbase-server we have uncovered/realized some small but important gotchas related to, in particular, data ingestion. They are documented below and will make valuable reading for _data producers_ who wish to ingest data into tagbase-server.

## API errors

Failed ingest and other HTTP errors use RFC7807 `application/problem+json` (`type`, `title`, `status`, `detail`, optional `instance`, plus `trace_id` for log correlation). The public API path is `/tagbase/api/v0`. Spectral/IBM rules that expect an `ErrorContainer` or `application/json` error bodies are disabled in [`.spectral.yaml`](https://github.com/tagbase/tagbase-server/blob/main/.spectral.yaml).

## Tooling

Before we discuss best practices related to data ingestion, let's first have a look at tooling.

- [rsync](https://linux.die.net/man/1/rsync): a fast and extraordinarily versatile file copying tool. Further to [ISSUE-189](https://github.com/tagbase/tagbase-server/issues/189) we can now use rsync to copy data to a `staging` location and automate ingestion into TagbaseDB via tagbase-server's REST API.
- [curl](https://curl.se/): an extremely popular and pervasive command line tool and library for transferring data with URLs. Available on most linux operating systems by default.
- tagbase-server UI: available as part of the [tagbase-server docker composition](https://github.com/tagbase/tagbase-server/wiki/Installation#using-the-uis). The OpenAPI specification is **self-documenting** and the UI also provides examples of how to interact with the REST API via `curl` and via a browser URL bar.

## Future work on tooling

A huge benefit of leveraging the OpenAPI specification is the larger ecosystem of tooling. In particular the [openapi-generator project](https://openapi-generator.tech/docs/generators) facilitates the generation of a wide variety of _clients_ in many different languages. If you would like to see a new client say for in Python, Java, Rust or some other supported programming language, [simply open a ticket](https://github.com/tagbase/tagbase-server/issues) and we can generate one for you and publish it in your packaging ecosystem.

## Ingestion Recommendations

The following emerging best practices can be used to drive throughput in the ingestion process

## Use compressed binary containers when submitting etuff data to tagbase-server

Synchronous `POST /ingest` and `GET /ingest` still process the file inside the request and return HTTP 200 with a trace id. A synchronous POST body is limited to 100 MiB. `GET /ingest` is also limited by the 60-second request window, so a large remote file should be submitted with `POST /ingest/jobs` instead.

`POST /ingest/jobs` accepts `.txt`, `.zip`, `.tar.gz`, and `.tgz` up to 2 GiB. The body is streamed to disk and the call returns HTTP 202 with a job id. Poll `GET /ingest/jobs/{job_id}` until `status` is `succeeded` or `failed`. The upload form and the fswatch service both use this job API.

Archives are opened with the Python `zipfile` and `tarfile` libraries. Other archive types are rejected. Extraction refuses path traversal, symlink members, and encrypted ZIP members, and it stops when a configurable member count (default 10,000) or uncompressed size (default 10 GiB) is exceeded.

## Submit multiple files at once

A synchronous request still walks the eTUFF members with [parmap](https://pypi.org/project/parmap/). The job worker runs one upload at a time. Parallelism beyond that single process is tracked as a follow-on issue.

## Ingest timings

Each successful ingest logs one `ingest.timings {json}` line from the ingest worker. It holds the Python phases in seconds (`read`, `build_rows`, `dataframe`, `csv_buffer`, `copy`, `procedure`) and `procedure_steps`: the duration in milliseconds and row count of every step of `sp_execute_data_migration`. The same steps are `migration.step` events on the `ingest.persist` span.

```bash
docker compose logs tagbase_server | grep 'ingest.timings'
```

## Benchmark large-file ingest

[`scripts/ingest-benchmark.py`](https://github.com/tagbase/tagbase-server/blob/main/scripts/ingest-benchmark.py) measures the large ICCAT files tracked in [#476](https://github.com/tagbase/tagbase-server/issues/476). `TAGBASE_BENCH_DATA_DIR` must hold `eTUFF_ICCAT-20260928T014825Z-1-001.zip`, `-002.zip` and `-003.zip`. Run the stack with the benchmark overlay, which keeps the database in a named volume and leaves fswatch stopped:

```bash
export TAGBASE_BENCH_DATA_DIR=/path/to/smoke-zips
COMPOSE="--compose-file docker-compose.yml --compose-file docker-compose.bench.yml"
docker compose -f docker-compose.yml -f docker-compose.bench.yml up -d --build

# Once, on an empty database: ingest the 39 smaller members (about 1 to 2 hours)
# and archive the PostGIS data directory to snapshots/warm.tar.
scripts/ingest-benchmark.py $COMPOSE snapshot

# Each benchmark: restore the archive, apply the procedure from
# services/postgis/tagbase_schema_tables.sql, ingest the five large BFT files.
scripts/ingest-benchmark.py $COMPOSE run --label=-my-change
```

Results go to `$TAGBASE_BENCH_DATA_DIR/results/<time>-<git sha><label>/`: `run.tsv` (per-file phases, procedure steps in seconds, peak memory of `tagbase_server` and `postgis`), `timings.jsonl`, `settings.txt` and `hashes.json`. A run has no timeout. Ctrl-C cancels a running `sp_execute_data_migration`.

[`scripts/ingest-equivalence.py`](https://github.com/tagbase/tagbase-server/blob/main/scripts/ingest-equivalence.py) checks that a change leaves the data unchanged:

```bash
scripts/ingest-equivalence.py compare baseline/hashes.json candidate/hashes.json
scripts/ingest-equivalence.py $COMPOSE positions
```

`compare` exits non-zero and names the file and table that differ. `positions` recomputes every `position_date_time` with the correlated subquery used before PR 437 and reports the rows that disagree.

## Use rsync

[ISSUE-189](https://github.com/tagbase/tagbase-server/issues/189) offers the ability to use `rsync` to copy data to a `staging` location. The data is then automatically ingested into TagbaseDB via tagbase-server's REST API

```text
rsync -e "ssh -i ~/.ssh/etags_tagbase.txt" -a ./staging_data/* tagbase@XXX.XXX.XXX.XXX:/home/tagbase/tagbase-server/staging_data/
```

## Example POST

```text
curl -X 'POST' \
  'https://XXX.XXX.XXX.XXX/tagbase/api/v0.7.0/ingest?notes=New%20notes&type=etuff&version=1&filename=159903_2012_117464_eTUFF.txt' \
  -H 'accept: application/json' \
  -H 'Content-Type: text/plain' \
  -u ...:... --insecure -T 159903_2012_117464_eTUFF.txt
```

N.B. Ensure that you have the correct IP/DNS and username/password.
