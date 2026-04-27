# notebooklm-py service

A FastAPI wrapper around `notebooklm-py` exposing a small REST surface with
Swagger UI at `/docs`. Lives in this directory so the upstream library tree is
untouched and `git fetch origin` always merges cleanly.

## Quick start

```bash
# 0. From the repo root, log in once on the host (writes ~/.notebooklm/storage_state.json)
notebooklm login

# 1. Configure
cd service
cp .env.example .env
python -m service.auth >> /tmp/api_token   # generates a token; copy into .env

# 2. Build and run
docker compose up --build -d

# 3. Open Swagger UI
open http://localhost:8000/docs
```

## Auth

Every endpoint requires:

```
Authorization: Bearer <API_TOKEN from .env>
```

The container is bound to `127.0.0.1:8000` by default. Edit the port mapping in
`docker-compose.yml` to expose on the LAN.

## curl examples

```bash
TOKEN=$(grep ^API_TOKEN .env | cut -d= -f2)

# List notebooks
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/notebooks

# Create a notebook
curl -X POST -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"title": "API test"}' \
     http://localhost:8000/v1/notebooks

# Add a URL source
NB=<notebook-id>
curl -X POST -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"url": "https://en.wikipedia.org/wiki/Large_language_model", "wait": true}' \
     http://localhost:8000/v1/notebooks/$NB/sources/url

# Ask a question
curl -X POST -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"question": "Summarise the main argument."}' \
     http://localhost:8000/v1/notebooks/$NB/chat

# Generate audio (podcast)
curl -X POST -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"length": "DEFAULT"}' \
     http://localhost:8000/v1/notebooks/$NB/artifacts/audio

# List artifacts
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/notebooks/$NB/artifacts
```

## How the credentials get in

`docker-compose.yml` mounts your host `~/.notebooklm/` (override with
`NOTEBOOKLM_HOST_DIR`) into `/data` read-only. The library reads
`/data/storage_state.json`. To refresh credentials:

```bash
notebooklm login           # on the host
docker compose restart     # picks up the new file on next request
```

## Endpoint surface (MVP)

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Liveness |
| GET | `/v1/notebooks` | List notebooks |
| POST | `/v1/notebooks` | Create |
| GET | `/v1/notebooks/{id}` | Get one |
| PATCH | `/v1/notebooks/{id}` | Rename |
| DELETE | `/v1/notebooks/{id}` | Delete |
| GET | `/v1/notebooks/{id}/sources` | List sources |
| POST | `/v1/notebooks/{id}/sources/url` | Add URL/YouTube |
| POST | `/v1/notebooks/{id}/sources/text` | Add text |
| DELETE | `/v1/notebooks/{id}/sources/{src}` | Delete source |
| POST | `/v1/notebooks/{id}/chat` | Ask question (with citations) |
| GET | `/v1/notebooks/{id}/artifacts` | List artifacts |
| POST | `/v1/notebooks/{id}/artifacts/audio` | Generate podcast audio |

Other artifact types (video, quiz, flashcards, infographic, slide deck, mind map,
report, study guide, data table) live in the underlying library — add routes in
`service/routes/artifacts.py` mirroring `generate_audio` when you need them.

## Image

The Docker image is based on **`nixos/nix:2.24.9`**. The Python runtime and all
third-party libraries (fastapi, uvicorn, httpx, click, rich, pydantic) are
realised declaratively from nixpkgs via [`python-env.nix`](python-env.nix) —
there is no `pip install` inside the image.

`notebooklm-py` itself is **not** in nixpkgs, so it is mounted via `PYTHONPATH`
(`/app/src`) rather than installed. The library reads its version via
`importlib.metadata` and falls back to `0.0.0.dev0` when not found, which is
expected here.

### Adding a Python dependency

Two places to update (kept in sync manually):

1. **`python-env.nix`** — the only one that affects the Docker image.
2. **`requirements.txt`** — only used by the local-dev path below.

## Development without Docker

```bash
uv venv .venv && source .venv/bin/activate
uv pip install -e ..[all]
uv pip install -r requirements.txt
export API_TOKEN=$(python -m service.auth)
uvicorn service.main:app --reload
```

Or, if you have Nix on the host, drop straight into the same env the image uses:

```bash
nix-shell -p "(import ./python-env.nix {})" --run "uvicorn service.main:app --reload"
```

## Upstream sync

This is the **forkrul** vendor copy. Upstream (`origin = teng-lin/notebooklm-py`)
is **fetch-only** — push is hard-disabled. Pull latest with:

```bash
../scripts/sync-from-origin.sh
```
