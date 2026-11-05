FROM grafana/alloy:v1.21.3@sha256:8ab871206bd2d8f89277f53abffee5f452a293980788d52f85fa183a87a505a4

# Named-volume WAL is often root-owned (git compose runs upstream Alloy as
# root). Stay root for COPY + entrypoint chown, then drop to uid 473.
# checkov:skip=CKV_DOCKER_8: entrypoint must be root to chown the named-volume WAL, then setpriv-drop to alloy (473)
# hadolint ignore=DL3002
USER root
COPY config.publish.alloy /etc/alloy/config.alloy
COPY --chmod=0755 alloy-entrypoint.sh /usr/local/bin/alloy-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/alloy-entrypoint.sh"]

