FROM python:bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ARG POSTGRES_PASSWORD
ARG POSTGRES_PORT

WORKDIR /usr/src/app

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends install -y cron \
    # Remove package lists for smaller image sizes
    && rm -rf /var/lib/apt/lists/*

COPY crontab /etc/cron.d/docker-cron

RUN chmod 0644 /etc/cron.d/docker-cron

RUN useradd -ms /bin/bash tagbase

RUN crontab -u tagbase /etc/cron.d/docker-cron \
     && chmod u+s /usr/sbin/cron

COPY --chown=tagbase:tagbase . .

RUN python3 -m pip install pip --upgrade pip && \
    python3 -m pip install -r requirements.txt --no-cache-dir

RUN touch .env \
    && echo "export POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> /usr/src/app/.env \
    && echo "export POSTGRES_PORT=${POSTGRES_PORT}" >> /usr/src/app/.env

RUN chmod 777 -R /usr/src/app

USER tagbase

ENTRYPOINT ["./entrypoint.sh"]
