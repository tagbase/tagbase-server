#FROM williamyeh/fswatch
FROM python:bullseye

WORKDIR /usr/src/app

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends \
    install -y curl fswatch iputils-ping \
    # Remove package lists for smaller image sizes
    && rm -rf /var/lib/apt/lists/*

COPY post.sh post.sh

ENTRYPOINT ["./post.sh"]