FROM python:3.14-slim-bookworm

WORKDIR /usr/src/app

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends \
    install -y curl fswatch iputils-ping \
    # Remove package lists for smaller image sizes
    && rm -rf /var/lib/apt/lists/* \
    && useradd -ms /bin/bash tagbase

# Copy owned by root and grant the runtime user read+execute only, so the
# non-root user running the container cannot modify the script it executes.
COPY post.sh post.sh

RUN chmod 0555 post.sh

USER tagbase

ENTRYPOINT ["./post.sh"]
