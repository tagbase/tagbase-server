FROM postgres:10.4-alpine

RUN mkdir -p /usr/src/app
RUN mkdir -p /usr/local/postgres && \
   chown -R postgres /usr/local/postgres

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN apk --update add gcc linux-headers musl-dev python3 python3-dev

RUN pg_config --version

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

USER postgres

RUN pg_ctl initdb -D /usr/local/postgres 
RUN pg_ctl -D /usr/local/postgres -w start && \
    psql -f sqldb/tagbase-schema.sql && \
    psql -f sqldb/metadata_types.sql

#RUN psql -f sqldb/tagbase-schema.sql

#RUN psql -f sqldb/metadata_types.sql

#COPY . /usr/src/app

EXPOSE 5433

ENTRYPOINT ["python3"]

CMD ["-m", "swagger_server"]
