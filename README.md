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

* [Python](https://www.python.org/downloads/) (preferrably >= 3.5)
* [Docker](https://www.docker.com/get-docker)
* [Docker Compose](https://docs.docker.com/compose/install/)

### Deployment

To orchestrate and deploy the Tagbase services execute the following from this root directory:

```bash
$ docker-compose build
$ docker-compose up
```

Navigate to [http://localhost:5433/v1/tagbase/ui/](http://localhost:5433/v1/tagbase/ui/) 
to see the tagbase-server UI running. 
**It will really help for you to read the documentation provided.**
Using the eTUFF API, you can execute the following commands to initiate a primitive test
ingestion of some sample eTUFF-sailfish-117259.txt present on the server.

using curl...
```
curl -X GET --header 'Accept: application/json' 'http://localhost:5433/v1/tagbase/ingest/etuff?dmas_granule_id=1234&file=file%3A%2F%2F%2Fusr%2Fsrc%2Fapp%2Fdata%2FeTUFF-sailfish-117259.txt'
```
...or using a Request URL
```
http://localhost:5433/v1/tagbase/ingest/etuff?dmas_granule_id=1234&file=file%3A%2F%2F%2Fusr%2Fsrc%2Fapp%2Fdata%2FeTUFF-sailfish-117259.txt
```

**N.B.** The REST server is capable of ingesting data from many sources e.g. file, ftp, http and https.

## Running Manually

See https://wiki.earthdata.nasa.gov/display/OIIP/Manual+Installation+of+tagbase-server

## Development, Support and Community
Please reach out to the OIIP project team at <oiip@jpl.nasa.gov>