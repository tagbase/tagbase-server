FROM nginx:latest

ARG NGINX_PASS
ARG NGINX_USER

RUN apt-get update && \
    apt-get dist-upgrade -y && \
    apt-get install --no-install-recommends -y apache2-utils && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN htpasswd -bc /etc/nginx/.htpasswd ${NGINX_USER} ${NGINX_PASS}