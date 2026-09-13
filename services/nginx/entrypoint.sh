#!/bin/sh
set -eu

NGINX_USER="${NGINX_USER:-tagbase}"
if [ -z "${NGINX_PASS:-}" ]; then
	echo "NGINX_PASS is required" >&2
	exit 1
fi

htpasswd -bc /etc/nginx/.htpasswd "${NGINX_USER}" "${NGINX_PASS}"

mkdir -p /etc/nginx/certs /var/www/acme/.well-known/acme-challenge

if [ ! -s /etc/nginx/certs/cert.pem ] || [ ! -s /etc/nginx/certs/key.pem ]; then
	echo "Generating self-signed TLS certificate for localhost"
	openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
		-keyout /etc/nginx/certs/key.pem \
		-out /etc/nginx/certs/cert.pem \
		-subj "/CN=localhost" \
		-addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
	chmod 600 /etc/nginx/certs/key.pem
	chmod 644 /etc/nginx/certs/cert.pem
fi

# Reload when Lego (or an operator) replaces PEMs on the certs volume.
(
	while inotifywait -e close_write,moved_to,create /etc/nginx/certs >/dev/null 2>&1; do
		nginx -s reload || true
	done
) &

exec nginx -g "daemon off;"
