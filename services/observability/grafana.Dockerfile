FROM grafana/grafana:13.3.0@sha256:488984b716c0862639f91a698adbe2862677a5a07bad42da5f03f3030883b205

USER root
COPY grafana/provisioning /etc/grafana/provisioning
RUN chown -R grafana:root /etc/grafana/provisioning
USER grafana
