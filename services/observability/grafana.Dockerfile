FROM grafana/grafana:13.2.1@sha256:f772d434e8fab0049deb2b1b30abd43342bcfca1537614aa8d36080232cf4283

USER root
COPY grafana/provisioning /etc/grafana/provisioning
RUN chown -R grafana:root /etc/grafana/provisioning
USER grafana
