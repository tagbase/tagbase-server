FROM grafana/alloy:v1.19.2@sha256:b8ec653c44235fbe910879145dac3597d66b0aaecf60bcbbe82580767771a839

# Named-volume WAL is often root-owned (git compose runs upstream Alloy as
# root). Stay root for COPY + entrypoint chown, then drop to uid 473.
# hadolint ignore=DL3002
USER root
COPY config.publish.alloy /etc/alloy/config.alloy
COPY --chmod=0755 alloy-entrypoint.sh /usr/local/bin/alloy-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/alloy-entrypoint.sh"]

