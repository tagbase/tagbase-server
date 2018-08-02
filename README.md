# Tagbase server

## Overview

Tagbase is a [Flask](http://flask.pocoo.org/) application which provides HTTP endpoints for ingestion of 
various files into the Tagbase SQL database.


## Running with Docker

### Introduction
[Docker](https://www.docker.com/what-docker) enables rapid simplified deployment of Tagbase by removing
all services setup and configuration e.g. PostgreSQL, tagbase-server, etc. 
This is achieved via [Docker Compose]](https://docs.docker.com/compose/overview/); a tool for defining and 
running multi-container Docker applications.

See below for prerequisite installation requirements.

### Prerequisites

* [Git](https://git-scm.com/downloads)
* [Docker](https://www.docker.com/get-docker)
* [Docker Compose](https://docs.docker.com/compose/install/)

Either [download tabase-server](https://git.earthdata.nasa.gov/rest/api/latest/projects/OIIP/repos/tagbase-server/archive?format=zip) OR clone the source code with Git

```bash
$ git clone https://${urs_username}@git.earthdata.nasa.gov/scm/oiip/tagbase-server.git
```

N.B. you should replace ```${urs_username}``` with your URS username.

Either way, once you've acquired the tagbase-server source code on your workstation, you need to navigate to the source root directory e.g.

```bash
$ cd tagbase-server
```

### Deployment

To orchestrate and deploy the Tagbase services execute the following from this root directory:

```bash
$ docker-compose build
$ docker-compose up
```

After a short while, you will now have a completely Dockerized deployment of Tagbase (master), 
[PosgreSQL 10.X](https://www.postgresql.org) and [pgAdmin](https://www.pgadmin.org).

See below for accessing the Web Applications.

### Tagbase Server

Navigate to [http://localhost:5433/v1/tagbase/ui/](http://0.0.0.0:5433/v1/tagbase/ui/) 
to see the tagbase-server UI running. 
**It will really help for you to read the API documentation provided in the Web Application.**
Using the [eTUFF API](http://0.0.0.0:5433/v1/tagbase/ui/#!/Products/ingest_etuff_get), 
you can execute the following commands to initiate a primitive test
ingestion of some sample eTUFF-sailfish-117259.txt data present on the server.

using curl...

```bash
curl -X GET --header 'Accept: application/json' 'http://localhost:5433/v1/tagbase/ingest/etuff?dmas_granule_id=1234&file=file%3A%2F%2F%2Fusr%2Fsrc%2Fapp%2Fdata%2FeTUFF-sailfish-117259.txt'
```

...or using a Request URL

```bash
http://localhost:5433/v1/tagbase/ingest/etuff?dmas_granule_id=1234&file=file%3A%2F%2F%2Fusr%2Fsrc%2Fapp%2Fdata%2FeTUFF-sailfish-117259.txt
```

**N.B.** The REST server is capable of ingesting data from many sources e.g. file, ftp, http and https.

### pgAdmin

Navigate to [http://0.0.0.0:5434/browser/](http://0.0.0.0:5434/browser/) and enter 

**username** ***oiip@jpl.nasa.gov***
**password** ***tagbase***

You can now:

* Add New Server
* General Tab --> name: tagbase
* Connection Tab --> Host name/address: postgres
* Connection Tab --> Port: 5432
* Connection Tab --> Maintenance database: postgres 
* Connection Tab --> Username: tagbase

On the left hand side navigation panel, you will now see the persistent connection to the tagbase database.

## Running Manually

See https://wiki.earthdata.nasa.gov/display/OIIP/Manual+Installation+of+tagbase-server

## Development, Support and Community
Please reach out to the OIIP project team at <oiip@jpl.nasa.gov>