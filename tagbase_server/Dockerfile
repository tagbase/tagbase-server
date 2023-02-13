FROM python:slim-bullseye

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN apt update && \
 apt -y upgrade && \
 apt -y install bash curl gcc musl-dev tzdata && \
 python3 -m pip install --upgrade pip && \
 python3 -m pip install -r requirements.txt --no-cache-dir

RUN ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime

COPY . /usr/src/app

EXPOSE 5433
EXPOSE 5555

ENTRYPOINT ["gunicorn"]

CMD ["tagbase_server.__main__:app", "--preload"]
