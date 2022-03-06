# Tagbase server

[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=tagbase_tagbase-server&metric=bugs)](https://sonarcloud.io/summary/new_code?id=tagbase_tagbase-server)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=tagbase_tagbase-server&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=tagbase_tagbase-server)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=tagbase_tagbase-server&metric=coverage)](https://sonarcloud.io/summary/new_code?id=tagbase_tagbase-server)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=tagbase_tagbase-server&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=tagbase_tagbase-server)
![tagbase-server CI](https://github.com/tagbase/tagbase-server/actions/workflows/build.yaml/badge.svg)
[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=tagbase_tagbase-server&metric=ncloc)](https://sonarcloud.io/summary/new_code?id=tagbase_tagbase-server)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=tagbase_tagbase-server&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=tagbase_tagbase-server)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=tagbase_tagbase-server&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=tagbase_tagbase-server)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=tagbase_tagbase-server&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=tagbase_tagbase-server)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=tagbase_tagbase-server&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=tagbase_tagbase-server)
[![Technical Debt](https://sonarcloud.io/api/project_badges/measure?project=tagbase_tagbase-server&metric=sqale_index)](https://sonarcloud.io/summary/new_code?id=tagbase_tagbase-server)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=tagbase_tagbase-server&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=tagbase_tagbase-server)

## Overview

[tagbase-server](https://github.com/tagbase/tagbase-server) is a data management web service for working with eTUFF [1](https://doi.org/10.6084/m9.figshare.10032848.v4) [2](https://doi.org/10.6084/m9.figshare.10159820.v1.0.0)) and [nc-eTAG](https://github.com/oceandatainterop/nc-eTAG/) files.

tagbase-server facilitates ingestion operations via REST courtesy of the [OpenAPI v3.0.3](https://spec.openapis.org/oas/v3.0.3.html).

## Running with Docker

### Introduction
[Docker](https://www.docker.com/why-docker) enables rapid simplified deployment of Tagbase by removing
all services setup and configuration e.g. PostgreSQL, tagbase-server, etc.
This is achieved via [Docker Compose](https://docs.docker.com/compose/overview/); a tool for defining and
running multi-container Docker applications.

See below for prerequisite installation requirements.

### Prerequisites

* [Git](https://git-scm.com/downloads)
* [Docker](https://www.docker.com/products/docker-desktop)

Either [download tabase-server](https://github.com/tagbase/tagbase-server/raw/master/tagbase-server-master.zip) OR clone the source code with Git

Once you've acquired the tagbase-server source code on your workstation, you need to navigate to the source root directory e.g.

```bash
$ cd tagbase-server
```

### Deployment

**N.B.** Due to the size of the input datasets we ingest into tagbase-server, it is essential that the container running the service has sufficient available memory (4GB should do the trick).

See this for Mac:

https://docs.docker.com/docker-for-mac/#memory


***MEMORY By default, Docker for Mac is set to use 2 GB runtime memory, allocated from the total available memory on your Mac. You can increase the RAM on the app to get faster performance by setting this number higher (for example to 3) or lower (to 1) if you want Docker for Mac to use less memory.***

For Windows:

https://docs.docker.com/docker-for-windows/#advanced

***Memory - Change the amount of memory the Docker for Windows Linux VM uses***

Once sufficient memory is available, to orchestrate and deploy the Tagbase services execute the following from this root directory:

```bash
$ docker-compose build
$ docker-compose up
```

After a short while, you will now have a running docker composition comprising tagbase-sever (main branch), [PostgreSQL 14.X](https://www.postgresql.org) and [pgAdmin4](https://www.pgadmin.org).

See below for accessing the Web Applications.

To stop the docker-compose deployment, simply open a new terminal, navigate to the tagbase-server root directory and execute
```
$ docker-compose stop
```
You will see the services graciously shutdown.

### Tagbase Server

**N.B.** The URI's below may alternate between ***localhost*** and ***0.0.0.0*** depending on whether your workstation is Windows (localhost) or Linux/Mac (0.0.0.0)

Navigate to [http://localhost:5433/v0.3.0/ui/](http://0.0.0.0:5433/v0.3.0/ui/)
to see the tagbase-server UI running.
**It will really help for you to read the API documentation provided in the Web Application.**
Using the `/ingest/etuff` API, you can execute the following commands to initiate a primitive test
ingestion of some sample eTUFF-sailfish-117259.txt data present on the server.

using curl...

```bash
curl -X GET --header 'Accept: application/json' 'http://0.0.0.0:5433/v0.3.0/ingest/etuff?granule_id=1234&file=file%3A%2F%2F%2Fusr%2Fsrc%2Fapp%2Fdata%2FeTUFF-sailfish-117259.txt'
```

...or using a Request URL

```bash
http://0.0.0.0:5433/v0.3.0/ingest/etuff?granule_id=1234&file=file%3A%2F%2F%2Fusr%2Fsrc%2Fapp%2Fdata%2FeTUFF-sailfish-117259.txt
```

**N.B.** The REST server is capable of ingesting data over `file`, `ftp`, `http` and `https` protocols.

### pgAdmin

Navigate to [http://0.0.0.0:5434/browser/](http://0.0.0.0:5434/browser/) and enter

**username** ***tagbase***
**password** ***tagbase***

You can now:

* Add New Server
* General Tab --> name: tagbase
* Connection Tab --> Host name/address: postgres
* Connection Tab --> Port: 5432
* Connection Tab --> Maintenance database: postgres
* Connection Tab --> Username: tagbase

On the left hand side navigation panel, you will now see the persistent connection to the tagbase database.

#### Generating Meterialized views

Upon successful ingestion of files into Tagbase, you are required to generate materialized views in order to
access the 'application ready' tagbase data.

**N.B.** Previously, it was necessary to execute a data migration command which essentially
populated initial staging data around the DB. This is now managed by a trigger such that
all we need to worry about it generating materialized views.

[PostgreSQL Materialized Views](https://www.postgresql.org/docs/current/static/rules-materializedviews.html)
extend the concept of database views; virtual tables which represent data of the underlying tables,
to the next level that allows views to store data physically, and we call those views materialized views.
A materialized view caches the result of a complex expensive query and then allows you to refresh this result periodically.

You can generate the Tagbase materialized views by opening [tagbase-materialized-views.sql](https://github.com/tagbase/tagbase-server/blob/main/services/postgres/sqldb/tagbase-materialized-views.sql)

... and executing the contents as a query within the pgAdmin4 Query Tool.

Similar to the ingestion and migration routines, generation of the materialized views may take a while so be patient. Once it has completed however, you can browse the materialized views.

**N.B.** It should be noted that materialized views can only be generated once... this process should not be executed every time a file is ingested!

## Running Manually

See https://wiki.earthdata.nasa.gov/display/OIIP/Manual+Installation+of+tagbase-server

## Development, Support and Community
Please create a [issue](https://github.com/tagbase/tagbase-server/issues).
