FROM grafana/alloy:v1.21.1@sha256:4039c971193053a84e53dd9ed3e7d4561c069256b024631cd3498a353ed7ece8

# Named-volume WAL is often root-owned (git compose runs upstream Alloy as
# root). Stay root for COPY + entrypoint chown, then drop to uid 473.
# checkov:skip=CKV_DOCKER_8: entrypoint must be root to chown the named-volume WAL, then setpriv-drop to alloy (473)
# hadolint ignore=DL3002
USER root
COPY config.publish.alloy /etc/alloy/config.alloy
COPY --chmod=0755 alloy-entrypoint.sh /usr/local/bin/alloy-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/alloy-entrypoint.sh"]

