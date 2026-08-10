# safe/ — keys, addresses, prod env (local only)

| Pattern | Purpose |
|---------|---------|
| `*-privatekey.pem` | SSH private key |
| `*-address.txt` | VM IP / hostname (first line) |
| `*-env.env` | Production secrets → uploaded as `~/projects/fast-rio/.env` |

| Files | Server id |
|-------|-----------|
| `ar-fast-rio-bamdad-*` | `fast-rio` |

Copy the `*.example` stubs, drop the `.example` suffix, and fill real values.

`*.pem`, `*.env`, `*-address.txt` are gitignored.

Upload env to VM:

```bat
fast-rio-ctrl.bat env
```

That copies `safe/ar-fast-rio-bamdad-env.env` → `~/projects/fast-rio/.env`.
