FROM python:3.15-slim-bookworm@sha256:96599df822d0e1c6bb700014a05c7f3c8cabc6e0f7ff3c4f9f69cee033b4b5d9

RUN mkdir -p /usr/src/app
RUN mkdir -p /usr/src/app/logs
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN apt-get update && \
 apt-get -y upgrade && \
 apt-get -y --no-install-recommends install bash gcc musl-dev tzdata && \
 rm -rf /var/lib/apt/lists/* && \
 python3 -m pip install -r requirements.txt --no-cache-dir

RUN ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime

COPY . /usr/src/app

EXPOSE 5433

RUN chmod 0555 /usr/src/app/docker-entrypoint.sh

ENTRYPOINT ["/usr/src/app/docker-entrypoint.sh"]
