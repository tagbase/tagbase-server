FROM python:3.15-slim-bookworm@sha256:8c77b1d8f366eda6c7a66c292134d7bfb2672c1c6273262dd1a459532cbc6a96

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
