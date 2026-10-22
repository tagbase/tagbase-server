FROM grafana/tempo:3.1.1@sha256:64e2fbd56d9c2b3412a4b430a58ea59e91a670b1e75f920a0c702213ad145044

USER root
COPY tempo/tempo-config.yml /etc/tempo/tempo-config.yml
USER 10001
