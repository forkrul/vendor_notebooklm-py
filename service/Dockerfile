# syntax=docker/dockerfile:1.6
#
# NixOS-based image. The Python runtime and all third-party packages are
# realised declaratively from nixpkgs via `service/python-env.nix`. The
# notebooklm-py library is not yet in nixpkgs, so we expose it via PYTHONPATH
# rather than pip-installing it (avoids mixing pip and nix in one tree).
#
# Auth: a Playwright `storage_state.json` is mounted at runtime under /data —
# never bake credentials into the image.

FROM nixos/nix:2.24.9

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NIX_CONFIG="experimental-features = nix-command flakes" \
    NOTEBOOKLM_HOME=/data \
    NOTEBOOKLM_STORAGE_PATH=/data/storage_state.json

# Refresh the nixpkgs channel (the base pins one, but it's old) and install
# minimal runtime utilities. curl is used by the healthcheck; cacert gives
# nixpkgs a TLS trust store.
RUN nix-channel --update \
 && nix-env -iA nixpkgs.curl nixpkgs.cacert nixpkgs.shadow

# Build the Python environment declaratively. Cached as long as python-env.nix
# is unchanged — this is the heavy layer.
COPY service/python-env.nix /tmp/python-env.nix
RUN nix-build /tmp/python-env.nix -o /python-env \
 && nix-collect-garbage -d >/dev/null 2>&1 || true

ENV PATH=/python-env/bin:/root/.nix-profile/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    PYTHONPATH=/app/src \
    SSL_CERT_FILE=/root/.nix-profile/etc/ssl/certs/ca-bundle.crt

WORKDIR /app

# Library and service code go in last — edits here don't bust the nix layers.
COPY src /app/src
COPY service /app/service
COPY pyproject.toml README.md /app/

# Non-root runtime user. /nix/store is world-readable so this is safe.
RUN adduser -D -u 10001 nlm \
 && mkdir -p /data \
 && chown -R nlm:nlm /data /app
USER nlm

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "service.main:app", "--host", "0.0.0.0", "--port", "8000"]
