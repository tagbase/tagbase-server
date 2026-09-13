#!/bin/sh
set -eu

if [ -z "${TLS_DOMAIN:-}" ]; then
	echo "TLS_DOMAIN is required for --profile letsencrypt" >&2
	exit 1
fi
if [ -z "${ACME_EMAIL:-}" ]; then
	echo "ACME_EMAIL is required for --profile letsencrypt (operator inbox; no ACME signup)" >&2
	exit 1
fi

ACME_DIRECTORY="${ACME_DIRECTORY:-https://acme-v02.api.letsencrypt.org/directory}"
LEGO_PATH="${LEGO_PATH:-/lego}"
CERTS_DIR="${CERTS_DIR:-/etc/nginx/certs}"
WEBROOT="${WEBROOT:-/var/www/acme}"

mkdir -p "${LEGO_PATH}" "${CERTS_DIR}" "${WEBROOT}/.well-known/acme-challenge"

install_certs() {
	src_crt="${LEGO_PATH}/certificates/${TLS_DOMAIN}.crt"
	src_key="${LEGO_PATH}/certificates/${TLS_DOMAIN}.key"
	if [ ! -s "${src_crt}" ] || [ ! -s "${src_key}" ]; then
		echo "Lego did not write ${src_crt} / ${src_key}" >&2
		return 1
	fi
	cp "${src_crt}" "${CERTS_DIR}/cert.pem"
	cp "${src_key}" "${CERTS_DIR}/key.pem"
	chmod 644 "${CERTS_DIR}/cert.pem"
	chmod 600 "${CERTS_DIR}/key.pem"
}

lego_base() {
	/lego \
		--accept-tos \
		--email "${ACME_EMAIL}" \
		--domains "${TLS_DOMAIN}" \
		--server "${ACME_DIRECTORY}" \
		--path "${LEGO_PATH}" \
		--http \
		--http.webroot "${WEBROOT}"
}

echo "Requesting certificate for ${TLS_DOMAIN}"
lego_base run
install_certs

while true; do
	echo "Sleeping 12h before renew check"
	sleep 43200
	lego_base renew --days 30 || true
	install_certs || true
done
