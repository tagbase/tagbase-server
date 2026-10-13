FROM goacme/lego:v5.5.2@sha256:1944e8c36055beec47c7de6f15202b41128be75eea0ffa257f0c14d93c5155fd

COPY entrypoint.sh /entrypoint.sh

RUN chmod 0555 /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
