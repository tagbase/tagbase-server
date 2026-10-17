FROM python:3.15-slim-bookworm@sha256:2a41267d9de9d358f77a1de356e0f16ecba8d39827855be0ce9ef4792edce402

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

ENTRYPOINT ["gunicorn"]

CMD ["-c", "gunicorn.conf.py", "tagbase_server.__main__:app"]
