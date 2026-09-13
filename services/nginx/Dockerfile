FROM nginx:1.29-bookworm@sha256:8adbdcb969e2676478ee2c7ad333956f0c8e0e4c5a7463f4611d7a2e7a7ff5dc

RUN apt-get update && \
    apt-get dist-upgrade -y && \
    apt-get install --no-install-recommends -y apache2-utils curl inotify-tools openssl && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY config/nginx.conf /etc/nginx/nginx.conf
COPY proxy/ /usr/share/nginx/html/
COPY entrypoint.sh /entrypoint.sh

RUN chmod 0555 /entrypoint.sh

EXPOSE 80 443

ENTRYPOINT ["/entrypoint.sh"]
