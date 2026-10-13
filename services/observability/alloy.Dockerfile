FROM grafana/alloy:v1.20.1@sha256:2aa2099af76c0098d4af7a4d6e48f86cb66dc1a000222ad927a1c67c6542d13f

# Named-volume WAL is often root-owned (git compose runs upstream Alloy as
# root). Stay root for COPY + entrypoint chown, then drop to uid 473.
# checkov:skip=CKV_DOCKER_8: entrypoint must be root to chown the named-volume WAL, then setpriv-drop to alloy (473)
# hadolint ignore=DL3002
USER root
COPY config.publish.alloy /etc/alloy/config.alloy
COPY --chmod=0755 alloy-entrypoint.sh /usr/local/bin/alloy-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/alloy-entrypoint.sh"]

