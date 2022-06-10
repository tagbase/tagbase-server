FROM python:slim-buster

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN apt update && \
 apt -y upgrade && \
 apt -y install bash gcc musl-dev  tzdata && \
 python3 -m pip install -r requirements.txt --no-cache-dir

RUN ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime

COPY . /usr/src/app

EXPOSE 5433

ENTRYPOINT ["python3"]

CMD ["-m", "tagbase_server"]
