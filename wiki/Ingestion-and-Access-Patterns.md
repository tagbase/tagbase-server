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
