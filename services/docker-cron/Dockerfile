FROM python:3.15-slim-bookworm@sha256:8c77b1d8f366eda6c7a66c292134d7bfb2672c1c6273262dd1a459532cbc6a96

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

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

RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install -r requirements.txt --no-cache-dir

# Credentials are written at container start from runtime env (see entrypoint.sh).
# Do not bake POSTGRES_* from build ARGs — unset ARGs produce empty exports that
# wipe compose-provided passwords when cron sources .env.

RUN chmod 777 -R /usr/src/app

USER tagbase

ENTRYPOINT ["./entrypoint.sh"]
