# Dev TLS certificates

Self-signed PEMs for local nginx HTTPS. **Not for production.**

- `cert.pem` / `key.pem` must be **files** (not directories). If Docker created empty directories here after a missing mount, delete them and restore these PEMs, then recreate the nginx container.
