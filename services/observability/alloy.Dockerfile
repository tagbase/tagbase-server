FROM grafana/alloy:v1.19.2@sha256:b8ec653c44235fbe910879145dac3597d66b0aaecf60bcbbe82580767771a839

USER root
COPY config.publish.alloy /etc/alloy/config.alloy
USER alloy
