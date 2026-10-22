FROM grafana/loki:3.7.9@sha256:0db216b630ae1f348a1584c67f3cead8b4c1fc839169a39501db664744158e28

USER root
COPY loki/loki-config.yml /etc/loki/loki-config.yml
USER 10001
