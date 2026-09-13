# What is OpenAPI?

The [OpenAPI Specification](https://spec.openapis.org/oas/latest.html) (OAS) defines a standard, programming language-agnostic interface description for HTTP APIs, which allows both humans and computers to discover and understand the capabilities of a service without requiring access to source code, additional documentation, or inspection of network traffic. When properly defined via OpenAPI, a consumer can understand and interact with the remote service with a minimal amount of implementation logic. Similar to what interface descriptions have done for lower-level programming, the OpenAPI Specification removes guesswork in calling a service.

## API-First Approach to Building Products

An API-first approach means that for any given development project, your APIs are treated as “_first-class citizens_” (rather than embedded deep down inside some code).

An API-first approach involves developing APIs that are consistent and reusable. In the case of tagbase-server, this is accomplished by using the OpenAPI specification, which establishes a contract for how the API is supposed to behave.

See [Swagger's Understanding the API-First Approach to Building Products](https://swagger.io/resources/articles/adopting-an-api-first-approach/) for loads more information.

## Generating tagbase-server from openapi.yaml

A [wide variety of tooling](https://openapi-generator.tech/) exists within the OAS ecosystem, which allows us to generate clients, servers, and documentation fairly easily.

## Which framework?

In the case of tagbase-server we use the [python-flask generator](https://openapi-generator.tech/docs/generators/python-flask) to produce the _server implementation_ of the OpenAPI specification hence... tagbase-server.

[Flask](https://flask.palletsprojects.com/) is a lightweight [WSGI](https://wsgi.readthedocs.io/en/latest/what.html) web application framework which has become one of the most popular Python web application frameworks. It's simple programming design patterns, implemented through the [python-flask generator](https://openapi-generator.tech/docs/generators/python-flask) make for a clean, minimal, intuitive tagbase-server codebase.

It should be noted that several alternative web application frameworks could be used to generate the tagbase-server implementation. For example, in the future [python-fastapi](https://openapi-generator.tech/docs/generators/python-fastapi) may becomes more appealing as the OpenAPI generator tooling matures from beta --> stable.

## Why Python

Put simply, the user and consumer communities targeted by tagbase-server are familiar with Python. Python and Flask therefore presents a very small learning curve for future tagbase-server users or developers. Again however, there is really no reason why tagbase-server couldn't be written (or generated) in Scala, or Kotlin or `${insert favorite programming language}`.

## Generating tagbase-server

### CAUTION: Overwriting existing files

In particular every time you generate tagbase-server using the above commands, it will overwrite, in particular [all controllers](https://github.com/tagbase/tagbase-server/tree/main/tagbase_server/tagbase_server/controllers) which contains Python logic for a variety of user-facing operations. **It is therefore imperative**, that you carefully cherry pick your code from source code management to ensure you retain backwards compatibility.

### Prerequisites

- Install [openapi-generator](https://openapi-generator.tech/docs/installation)

### Generation

Clone if you haven't already

```bash
git clone https://github.com/tagbase/tagbase-server && cd tagbase-server
```

Then generate the python-flask server

```bash
openapi-generator generate -g python-flask -i openapi.yaml -o tagbase_server --additional-properties packageName=tagbase_server
```

The tool output will indicate any warnings or errors. Now is a good time to pay attention to them and resolve any anomalies. Once you are satisfied, you will now see the updated Flask server implementation in [tagbase-server/tagbase_server](https://github.com/tagbase/tagbase-server/tree/main/tagbase_server)

## Updating openapi.yaml

It is inevitable that future changes will be made to [openapi.yaml](https://github.com/tagbase/tagbase-server/blob/main/openapi.yaml). Here are some things to take into mind.

- Save yourself some hassle and use [https://editor.swagger.io/](https://editor.swagger.io/) to sanity check your OpenAPI changes.
- The [lint-openapi target of .github/workflows/build.yml](https://github.com/tagbase/tagbase-server/blob/main/.github/workflows/build.yml) will always catch any OpenAPI linting or validation errors. It is therefore strongly recommended that you use [IBM/openapi-validator](https://github.com/IBM/openapi-validator) to sanity check your code before you touch anything else or progress any further. You can run it as follows

```bash
lint-openapi openapi.yaml
```

- Once openapi-validator checks pass, go ahead and [regenerate the tagbase-server implementation](#generating-tagbase-server).
