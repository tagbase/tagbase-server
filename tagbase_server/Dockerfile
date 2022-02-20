FROM python:3-alpine

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN apk update && \
 apk upgrade && \
 apk add bash postgresql-libs && \
 apk add --update tzdata && \
 apk add --virtual .build-deps gcc musl-dev postgresql-dev && \
 python3 -m pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps

RUN ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime
#&& \ dpkg-reconfigure -f noninteractive tzdata

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

EXPOSE 5433

ENTRYPOINT ["python3"]

CMD ["-m", "tagbase_server"]
