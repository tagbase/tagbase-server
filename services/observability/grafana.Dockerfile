FROM grafana/grafana:13.2.3@sha256:b28bae15e219c998fb0e0424ed724930cc61b1f61fb404d47c862f9a23f9e572

USER root
COPY grafana/provisioning /etc/grafana/provisioning
RUN chown -R grafana:root /etc/grafana/provisioning
USER grafana
