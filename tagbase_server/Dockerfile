FROM python:3.14-slim-bookworm

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

CMD ["-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:5433", "tagbase_server.__main__:app"]
