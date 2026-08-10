# fast-rio `__ctrl__`

SSH control plane **for this repo only** — bootstrap, clone, env, start/stop, update/reset, ACME/data backup.

This is **not** foxg-ctrl. FoxG platform VMs stay under `foxg-ctrl`; template kit ops live here.

## Quick start (Windows)

From `fast-rio/__ctrl__/`:

```bat
fast-rio-ctrl.bat
```

Interactive prompt, or one-shot:

```bat
fast-rio-ctrl.bat list
fast-rio-ctrl.bat connect
fast-rio-ctrl.bat dev run all
```

Linux/mac:

```bash
chmod +x fast-rio-ctrl.sh
./fast-rio-ctrl.sh status
```

## Layout

| Path | Role |
|------|------|
| `servers.json` | Single VM entry (`fast-rio`) |
| `safe/` | PEM, address, prod `.env` |
| `static/gpg` | Docker Ubuntu GPG (Iran bootstrap) |
| `fast-rio-ctrl.bat` / `.sh` | CLI |

## Typical first deploy

```bat
fast-rio-ctrl.bat setup
fast-rio-ctrl.bat pubkey
REM add VM pubkey to GitHub
fast-rio-ctrl.bat clone
fast-rio-ctrl.bat env
fast-rio-ctrl.bat start
```

Day-2:

```bat
fast-rio-ctrl.bat update
fast-rio-ctrl.bat status
fast-rio-ctrl.bat backup-acme
```

## Local dev (Docker Desktop / host apps)

Same stack as `__init__/start-fast-rio-dev.*`, without SSH and without that script’s `pause`:

```bat
fast-rio-ctrl.bat dev run all
fast-rio-ctrl.bat dev stop all
fast-rio-ctrl.bat dev down all
fast-rio-ctrl.bat dev purge infra
fast-rio-ctrl.bat dev reset all
```

| Action | Infra (compose.dev.yml) | Apps (host) |
|--------|-------------------------|-------------|
| `run` / `start` | `up -d` db/proxy/adminer + migrate | uvicorn :18000, rio :5173 |
| `stop` | `compose stop` — containers kept | kill host processes |
| `down` | `compose down` — volumes kept | kill host processes |
| `purge` | `compose down -v` — wipe data, stay down | kill host processes |
| `reset` | wipe then `run` | stop then run |

| Target | Notes |
|--------|-------|
| `infra` | Docker only + Alembic / initial_data |
| `apps` | host processes (needs infra already up) |
| `all` | run: infra→apps · stop/down/purge/reset: apps→infra |

Opens browser tabs for Adminer / Traefik / dashboard / API docs after a successful run.

## Seed catalog

N/A — this template has no catalog seed CLI (unlike fast-game).

## Setup

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

Iran VMs (`iran_setup: true`) keep provider DNS (Shecan is not injected — it breaks Bamdad resolution), rewrite apt to Arvan `apt_mirror`, and use Arvan Docker `registry_mirror`. `clone` routes GitHub SSH via `ssh.github.com:443`.
