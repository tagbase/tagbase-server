# Nginx TLS (runtime)

Certificates are **not** stored in git. The nginx entrypoint writes a self-signed
`cert.pem` / `key.pem` into the `nginx-certs` named volume when those files are
missing.

- Restarting the stack reuses the volume.
- `docker compose down -v` deletes the volume and the next start mints a new
  pair (browsers will warn again).
- Trusted certificates: `docker compose --profile letsencrypt` with `TLS_DOMAIN`
  and `ACME_EMAIL` (operator inbox; no Let's Encrypt signup). HTTP-01 uses port
  80 and the `acme-www` volume.

Do not commit PEMs. If Docker ever created empty `cert.pem`/`key.pem`
directories from an old bind mount, delete them.
