FROM goacme/lego:v5.4.1@sha256:ac04a7aaac0270ca2c32f1e79b157087d763e78c4473551c6e093070614536e2

COPY entrypoint.sh /entrypoint.sh

RUN chmod 0555 /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
