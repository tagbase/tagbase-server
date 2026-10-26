FROM python:3.15-slim-bookworm@sha256:575f8bc12ec26542e0678bc6b60e385218248019d433157ec327264a78c3a853

WORKDIR /usr/src/app

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends \
    install -y curl fswatch iputils-ping \
    # Remove package lists for smaller image sizes
    && rm -rf /var/lib/apt/lists/* \
    && useradd -ms /bin/bash tagbase \
    && mkdir -p /var/lib/tagbase-fswatch \
    && chown tagbase:tagbase /var/lib/tagbase-fswatch

# Copy owned by root and grant the runtime user read+execute only, so the
# non-root user running the container cannot modify the script it executes.
COPY post.sh post.sh

RUN chmod 0555 post.sh

USER tagbase

ENTRYPOINT ["./post.sh"]
