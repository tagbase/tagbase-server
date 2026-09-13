FROM grafana/loki:3.7.7@sha256:d70e4659623f3e109af669cae76fe2a5dd5be54e2298fe8aed380d982fbc2500

USER root
COPY loki/loki-config.yml /etc/loki/loki-config.yml
USER 10001
