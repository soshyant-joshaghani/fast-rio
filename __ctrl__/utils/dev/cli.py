"""fast-rio-ctrl dev — run/stop local Docker Desktop / host app stacks."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from lib.config import ROOT

# __ctrl__ lives under fast-rio/; the compose + apps root is the parent.
PROJECT = ROOT.parent

RUN_ORDER = ("infra", "apps")
STOP_ORDER = ("apps", "infra")
TARGETS = ("infra", "apps", "all")

COMPOSE_PROJECT_NAME = "fast-rio-dev"
COMPOSE_FILE = "compose.dev.yml"
INFRA_SERVICES = ("db", "proxy", "adminer")

# (window_title, port) — host processes spawned in new consoles on Windows
APP_PORTS = (
    ("fast-rio-backend", 18000),
    ("fast-rio-frontend", 5173),
)

STACK_OPEN_URLS: dict[str, tuple[str, ...]] = {
    "infra": (
        "http://adminer.localhost/",
        "http://localhost:18090/",
    ),
    "apps": (
        "http://dashboard.localhost/",
        "http://api.localhost/docs",
        "http://api.localhost/sdoc",
    ),
}


def _require_cmd(name: str) -> str | None:
    path = shutil.which(name)
    if not path:
        print(f"error: '{name}' not found on PATH", file=sys.stderr)
        return None
    return path


def _host_python_argv() -> list[str] | None:
    """Resolve a usable host Python (avoid Windows Store stub)."""
    if shutil.which("py"):
        return ["py", "-3"]
    for name in ("python3", "python"):
        path = shutil.which(name)
        if not path:
            continue
        normalized = path.replace("/", "\\").lower()
        if "windowsapps" in normalized:
            continue
        probe = subprocess.run(
            [path, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"],
            capture_output=True,
            check=False,
        )
        if probe.returncode == 0:
            return [path]
    print(
        "error: Python 3.10+ not found (try enabling the 'py' launcher)",
        file=sys.stderr,
    )
    return None


def _resolve_targets(target: str, *, order: tuple[str, ...]) -> tuple[str, ...]:
    if target == "all":
        return order
    return (target,)


def _ensure_env() -> None:
    env = PROJECT / ".env"
    example = PROJECT / ".env.example"
    if env.is_file():
        return
    if example.is_file():
        shutil.copy(example, env)
        print(f"created {env} from .env.example")
    else:
        print(f"warn: no .env or .env.example in {PROJECT}", file=sys.stderr)


def _open_stack_urls(targets: tuple[str, ...]) -> None:
    urls: list[str] = []
    for t in targets:
        for url in STACK_OPEN_URLS.get(t, ()):
            if url not in urls:
                urls.append(url)
    for url in urls:
        print(f"opening {url}")
        try:
            webbrowser.open(url)
        except Exception as exc:
            print(f"warn: could not open {url}: {exc}", file=sys.stderr)


def _compose(*args: str, check: bool = True) -> int:
    if not _require_cmd("docker"):
        return 1
    cmd = ["docker", "compose", "-f", COMPOSE_FILE, *args]
    print(f"[fast-rio] {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=PROJECT, capture_output=False)
    if check and proc.returncode != 0:
        # Re-run with capture for a clearer port-conflict hint.
        probe = subprocess.run(
            cmd,
            cwd=PROJECT,
            capture_output=True,
            text=True,
            check=False,
        )
        combined = f"{probe.stdout or ''}\n{probe.stderr or ''}"
        if "port is already allocated" in combined.lower() or "address already in use" in combined.lower():
            print(
                "\nerror: Docker could not bind a host port (often :80 / :443).\n"
                "  Another Traefik/proxy is likely running (e.g. fast-game-dev-proxy).\n"
                "  Free it, then retry:\n"
                "    docker ps --format \"{{.Names}}\\t{{.Ports}}\"\n"
                "    docker stop <conflicting-proxy-container>\n"
                "  Apps still work directly at http://localhost:5173 and http://localhost:18000/docs\n"
                "  via:  fast-rio-ctrl.bat dev run apps\n",
                file=sys.stderr,
            )
        return proc.returncode
    return proc.returncode


def _wait_postgres(service: str, *, timeout_s: float = 120.0) -> int:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        proc = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                COMPOSE_FILE,
                "exec",
                "-T",
                service,
                "pg_isready",
                "-U",
                "postgres",
            ],
            cwd=PROJECT,
            capture_output=True,
            check=False,
        )
        if proc.returncode == 0:
            return 0
        time.sleep(2)
    print(f"error: {service} not ready within {timeout_s:.0f}s", file=sys.stderr)
    return 1


def _venv_python() -> Path | None:
    if sys.platform == "win32":
        py = PROJECT / ".venv" / "Scripts" / "python.exe"
    else:
        py = PROJECT / ".venv" / "bin" / "python"
    return py if py.is_file() else None


def _setup_local() -> int:
    """Mirror __init__/setup-local: ensure venv + requirements (no npm)."""
    _ensure_env()

    venv = PROJECT / ".venv"
    py = _venv_python()
    created = False
    if py is None:
        host_py = _host_python_argv()
        if not host_py:
            return 1
        print("[fast-rio] Creating Python venv at .venv ...")
        proc = subprocess.run([*host_py, "-m", "venv", str(venv)], cwd=PROJECT)
        if proc.returncode != 0:
            return proc.returncode
        created = True
        py = _venv_python()

    if not py:
        print("error: .venv python not found after create", file=sys.stderr)
        return 1

    # Always ensure deps when marker missing or venv was just created.
    marker = PROJECT / ".venv" / ".fast-rio-deps-ok"
    need_install = created or not marker.is_file()
    if need_install:
        print("[fast-rio] Installing Python requirements...")
        proc = subprocess.run(
            [str(py), "-m", "pip", "install", "-U", "pip"],
            cwd=PROJECT,
        )
        if proc.returncode != 0:
            return proc.returncode
        proc = subprocess.run(
            [str(py), "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=PROJECT,
        )
        if proc.returncode != 0:
            return proc.returncode
        try:
            marker.write_text("ok\n", encoding="utf-8")
        except OSError:
            pass

    print("Local environment ready.")
    return 0


def _run_migrations() -> int:
    py = _venv_python()
    if not py:
        print("error: missing project .venv — run setup first", file=sys.stderr)
        return 1
    backend = PROJECT / "backend"
    env = {**os.environ, "PYTHONPATH": str(backend)}
    if sys.platform == "win32":
        alembic = PROJECT / ".venv" / "Scripts" / "alembic.exe"
    else:
        alembic = PROJECT / ".venv" / "bin" / "alembic"
    alembic_cmd = str(alembic) if alembic.is_file() else None

    steps: list[list[str]] = [
        [str(py), "app/backend_pre_start.py"],
    ]
    if alembic_cmd:
        steps.append([alembic_cmd, "-c", "alembic.ini", "upgrade", "head"])
    else:
        steps.append(
            [str(py), "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"]
        )
    steps.append([str(py), "app/initial_data.py"])

    print("[fast-rio] Running migrations + seed (local prestart)...")
    for cmd in steps:
        print(f"  {' '.join(cmd)}")
        proc = subprocess.run(cmd, cwd=backend, env=env)
        if proc.returncode != 0:
            return proc.returncode
    return 0


def _port_listening(port: int) -> bool:
    if sys.platform == "win32":
        return bool(_pids_on_port_windows(port))
    return bool(_pids_on_port_unix(port))


def _wait_ports(ports: tuple[int, ...], *, timeout_s: float = 90.0) -> list[int]:
    deadline = time.time() + timeout_s
    pending = set(ports)
    while pending and time.time() < deadline:
        ready = {p for p in pending if _port_listening(p)}
        pending -= ready
        if pending:
            time.sleep(0.5)
    return sorted(pending)


def _pids_on_port_windows(port: int) -> set[int]:
    proc = subprocess.run(
        ["netstat", "-ano", "-p", "tcp"],
        capture_output=True,
        text=True,
        check=False,
    )
    pids: set[int] = set()
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) < 5 or parts[0].upper() != "TCP":
            continue
        if parts[3].upper() != "LISTENING":
            continue
        local = parts[1]
        if not (local.endswith(f":{port}") or local.endswith(f"]:{port}")):
            continue
        try:
            pid = int(parts[4])
        except ValueError:
            continue
        if pid > 0:
            pids.add(pid)
    return pids


def _pids_on_port_unix(port: int) -> set[int]:
    pids: set[int] = set()
    if shutil.which("lsof"):
        proc = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in (proc.stdout or "").splitlines():
            line = line.strip()
            if line.isdigit():
                pids.add(int(line))
        return pids
    if shutil.which("fuser"):
        proc = subprocess.run(
            ["fuser", f"{port}/tcp"],
            capture_output=True,
            text=True,
            check=False,
        )
        for token in (proc.stdout or "").replace("\n", " ").split():
            digits = "".join(c for c in token if c.isdigit())
            if digits:
                pids.add(int(digits))
    return pids


def _kill_pid(pid: int) -> None:
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            check=False,
        )
    else:
        try:
            os.kill(pid, 15)
        except ProcessLookupError:
            return
        except PermissionError:
            subprocess.run(["kill", "-9", str(pid)], check=False)


def _start_infra() -> int:
    code = _setup_local()
    if code != 0:
        return code

    code = _compose("up", "-d", "db", "adminer")
    if code != 0:
        return code
    # Recreate proxy so Traefik re-reads bind-mounted dynamic.dev.yml.
    # Docker Desktop on Windows does not deliver fsnotify for host mounts.
    code = _compose("up", "-d", "--force-recreate", "--no-deps", "proxy")
    if code != 0:
        return code

    print("[fast-rio] Waiting for Postgres...")
    if _wait_postgres("db") != 0:
        return 1

    code = _run_migrations()
    if code != 0:
        return code

    print("Infra ready: Adminer / Traefik up; DB migrated.")
    return 0


def _backend_env() -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONPATH": str(PROJECT / "backend"),
    }


def _frontend_env() -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONPATH": str(PROJECT / "frontend"),
        "PUBLIC_API_BASE_URL": "http://localhost:18000/api/v1",
    }


def _quote_cmd_arg(arg: str) -> str:
    """Quote a token for cmd.exe if it contains whitespace/special chars."""
    if not arg or any(c in arg for c in ' \t"&|<>()^%'):
        return '"' + arg.replace('"', '""') + '"'
    return arg


def _start_named_console(
    title: str,
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> None:
    """Open a titled console like start-fast-rio-dev.bat (`start "title" cmd /k …`).

    Uses shell=True so cmd.exe parses the line; argv is joined with cmd-safe quoting
    (avoids Python list2cmdline turning quotes into \\\").
    """
    inner = " ".join(_quote_cmd_arg(a) for a in args)
    cmdline = f'start "{title}" /D {_quote_cmd_arg(str(cwd))} cmd /k {inner}'
    subprocess.Popen(cmdline, shell=True, env=env)


def _spawn_apps_windows() -> int:
    py = _venv_python()
    if not py:
        print("error: missing project .venv", file=sys.stderr)
        return 1

    backend = PROJECT / "backend"
    frontend = PROJECT / "frontend"
    env_be = _backend_env()
    env_fe = _frontend_env()
    py_s = str(py)

    specs: list[tuple[str, list[str], Path, dict[str, str], int | None]] = [
        (
            "fast-rio-backend",
            [
                py_s,
                "-m",
                "uvicorn",
                "app.main:app",
                "--reload",
                "--host",
                "0.0.0.0",
                "--port",
                "18000",
            ],
            backend,
            env_be,
            18000,
        ),
        (
            "fast-rio-frontend",
            [py_s, "-m", "rio", "run", "--port", "5173", "--public"],
            frontend,
            env_fe,
            5173,
        ),
    ]

    wait_ports: list[int] = []
    for title, args, cwd, env, port in specs:
        if port is not None and _port_listening(port):
            print(f"  {title}: already listening on :{port}")
            continue
        print(f"  {title}: starting (new console)...")
        _start_named_console(title, args, cwd=cwd, env=env)
        if port is not None:
            wait_ports.append(port)

    if wait_ports:
        print("  waiting for app ports :18000, :5173...")
        missing = _wait_ports(tuple(wait_ports), timeout_s=90.0)
        if missing:
            print(
                f"error: apps did not listen on port(s) {missing} within 90s. "
                "Check the new console windows for errors.",
                file=sys.stderr,
            )
            return 1
    return 0


def _spawn_apps_unix() -> int:
    py = _venv_python()
    if not py:
        print("error: missing project .venv", file=sys.stderr)
        return 1

    backend = PROJECT / "backend"
    frontend = PROJECT / "frontend"
    env_be = _backend_env()
    env_fe = _frontend_env()
    specs: list[tuple[str, list[str], Path, dict[str, str], int | None]] = [
        (
            "fast-rio-backend",
            [
                str(py),
                "-m",
                "uvicorn",
                "app.main:app",
                "--reload",
                "--host",
                "0.0.0.0",
                "--port",
                "18000",
            ],
            backend,
            env_be,
            18000,
        ),
        (
            "fast-rio-frontend",
            [str(py), "-m", "rio", "run", "--port", "5173", "--public"],
            frontend,
            env_fe,
            5173,
        ),
    ]

    wait_ports: list[int] = []
    for title, cmd, cwd, env, port in specs:
        if port is not None and _port_listening(port):
            print(f"  {title}: already listening on :{port}")
            continue
        print(f"  {title}: starting...")
        subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        if port is not None:
            wait_ports.append(port)

    if wait_ports:
        print("  waiting for app ports :18000, :5173...")
        missing = _wait_ports(tuple(wait_ports), timeout_s=90.0)
        if missing:
            print(
                f"error: apps did not listen on port(s) {missing} within 90s.",
                file=sys.stderr,
            )
            return 1
    return 0


def _start_apps() -> int:
    code = _setup_local()
    if code != 0:
        return code

    print("[fast-rio] Starting backend (uvicorn) and frontend (rio)...")
    if sys.platform == "win32":
        code = _spawn_apps_windows()
    else:
        code = _spawn_apps_unix()
    if code != 0:
        return code

    print()
    print("Dev stack ready (hot reload on save):")
    print("  Dashboard:   http://dashboard.localhost")
    print("  API docs:    http://api.localhost/docs")
    print("  Scalar:      http://api.localhost/sdoc")
    print("  Adminer:     http://adminer.localhost")
    print("  Traefik:     http://localhost:18090")
    print()
    print("Direct: http://localhost:5173  http://localhost:18000/docs")
    print("Stop with: fast-rio-ctrl.bat dev stop all")
    return 0


def _stop_apps() -> int:
    print("[fast-rio] Stopping host apps (backend / frontend)...")
    killed: set[int] = set()
    for _title, port in APP_PORTS:
        if port is None:
            continue
        if sys.platform == "win32":
            pids = _pids_on_port_windows(port)
        else:
            pids = _pids_on_port_unix(port)
        for pid in pids:
            if pid in killed:
                continue
            print(f"  kill pid {pid} (port {port})")
            _kill_pid(pid)
            killed.add(pid)

    if sys.platform == "win32":
        for title, _port in APP_PORTS:
            subprocess.run(
                ["taskkill", "/F", "/FI", f"WINDOWTITLE eq {title}*"],
                capture_output=True,
                check=False,
            )

    if not killed:
        print("  (no listeners found on app ports; closed matching consoles if any)")
    else:
        print("Host apps stopped.")
    return 0


def _compose_stop() -> int:
    code = _compose("stop")
    if code != 0:
        return code
    print("Infra stopped (containers kept).")
    return 0


def _compose_down(*, volumes: bool = False) -> int:
    cmd = ["down", "--remove-orphans"]
    if volumes:
        cmd.append("-v")
        print("[fast-rio] compose down -v  (WIPES VOLUMES)")
    code = _compose(*cmd)
    if code != 0:
        return code
    if volumes:
        _cleanup_leftover_volumes()
        print("Infra removed; named volumes wiped.")
    else:
        print("Infra removed (volumes kept).")
    return 0


def _list_volume_names() -> list[str]:
    proc = subprocess.run(
        ["docker", "volume", "ls", "-q"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    return [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]


def _cleanup_leftover_volumes() -> None:
    prefix_us = f"{COMPOSE_PROJECT_NAME}_"
    for name in _list_volume_names():
        if name.startswith(prefix_us):
            print(f"  removing leftover volume {name}")
            subprocess.run(
                ["docker", "volume", "rm", "-f", name],
                capture_output=True,
                check=False,
            )
    print("  pruning dangling anonymous volumes...")
    proc = subprocess.run(
        ["docker", "volume", "prune", "-f"],
        capture_output=True,
        text=True,
        check=False,
    )
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    if out:
        for line in out.splitlines():
            print(f"  {line}")


def _run_one(target: str) -> int:
    if target == "infra":
        return _start_infra()
    if target == "apps":
        return _start_apps()
    print(f"error: unknown target {target!r}", file=sys.stderr)
    return 1


def _stop_one(target: str) -> int:
    if target == "infra":
        return _compose_stop()
    if target == "apps":
        return _stop_apps()
    print(f"error: unknown target {target!r}", file=sys.stderr)
    return 1


def _down_one(target: str) -> int:
    if target == "infra":
        return _compose_down(volumes=False)
    if target == "apps":
        return _stop_apps()
    print(f"error: unknown target {target!r}", file=sys.stderr)
    return 1


def _wipe_one(target: str) -> int:
    if target == "infra":
        return _compose_down(volumes=True)
    if target == "apps":
        return _stop_apps()
    print(f"error: unknown target {target!r}", file=sys.stderr)
    return 1


def cmd_dev_run(args: argparse.Namespace) -> int:
    targets = _resolve_targets(args.target, order=RUN_ORDER)
    for t in targets:
        code = _run_one(t)
        if code != 0:
            return code
    _open_stack_urls(targets)
    return 0


def cmd_dev_stop(args: argparse.Namespace) -> int:
    for t in _resolve_targets(args.target, order=STOP_ORDER):
        code = _stop_one(t)
        if code != 0:
            return code
    return 0


def cmd_dev_down(args: argparse.Namespace) -> int:
    for t in _resolve_targets(args.target, order=STOP_ORDER):
        code = _down_one(t)
        if code != 0:
            return code
    return 0


def cmd_dev_reset(args: argparse.Namespace) -> int:
    target = args.target
    print(
        f"WARNING: dev reset {target} removes compose named volumes "
        "(Postgres data for infra)."
    )
    for t in _resolve_targets(target, order=STOP_ORDER):
        code = _wipe_one(t)
        if code != 0:
            return code
    run_targets = _resolve_targets(target, order=RUN_ORDER)
    for t in run_targets:
        code = _run_one(t)
        if code != 0:
            return code
    _open_stack_urls(run_targets)
    return 0


def cmd_dev_purge(args: argparse.Namespace) -> int:
    target = args.target
    print(
        f"WARNING: dev purge {target} removes compose named volumes "
        "(Postgres data for infra). Stack will stay down."
    )
    for t in _resolve_targets(target, order=STOP_ORDER):
        code = _wipe_one(t)
        if code != 0:
            return code
    return 0


def _dev_help(args: argparse.Namespace) -> int:
    _ = args
    print(
        "usage: fast-rio-ctrl.bat dev {run|start,stop,down,purge,reset} {infra,apps,all}\n"
        "\n"
        "examples:\n"
        "  fast-rio-ctrl.bat dev run all\n"
        "  fast-rio-ctrl.bat dev start all\n"
        "  fast-rio-ctrl.bat dev stop apps\n"
        "  fast-rio-ctrl.bat dev down all\n"
        "  fast-rio-ctrl.bat dev purge infra\n"
        "  fast-rio-ctrl.bat dev reset all\n"
        "\n"
        "run/start: compose up + host uvicorn/rio\n"
        "stop:   compose stop / kill host apps (containers kept)\n"
        "down:   compose down / kill host apps (volumes kept)\n"
        "purge:  compose down -v (wipe volumes, do not start)\n"
        "reset:  compose down -v then run (wipe volumes)\n"
        "order:  run infra->apps; stop/down/purge/reset: apps->infra\n"
        "Local only - not SSH / production VMs."
    )
    return 0


def build_dev_subparser(sub: argparse._SubParsersAction) -> None:
    sp = sub.add_parser(
        "dev",
        help="Run/stop/down/purge/reset local Docker Desktop / host app stacks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  fast-rio-ctrl.bat dev run all\n"
            "  fast-rio-ctrl.bat dev start all\n"
            "  fast-rio-ctrl.bat dev stop apps\n"
            "  fast-rio-ctrl.bat dev down all\n"
            "  fast-rio-ctrl.bat dev purge infra\n"
            "  fast-rio-ctrl.bat dev reset all\n"
            "\n"
            "run/start: compose up + host uvicorn/rio\n"
            "stop:   compose stop / kill host apps (containers kept)\n"
            "down:   compose down / kill host apps (volumes kept)\n"
            "purge:  compose down -v (wipe volumes, do not start)\n"
            "reset:  compose down -v then run (wipe volumes)\n"
            "order:  run infra->apps; stop/down/purge/reset: apps->infra\n"
            "Local only - not SSH / production VMs."
        ),
    )
    sp.set_defaults(func=_dev_help)

    actions = sp.add_subparsers(dest="dev_action", required=False)

    for name, help_, fn in [
        ("run", "Start local stack(s)", cmd_dev_run),
        ("start", "Alias for run", cmd_dev_run),
        ("stop", "Stop services (compose stop — keep containers)", cmd_dev_stop),
        ("down", "Remove containers/networks (compose down — keep volumes)", cmd_dev_down),
        ("purge", "Wipe Docker volumes and leave stack down", cmd_dev_purge),
        ("reset", "Wipe Docker volumes then start again", cmd_dev_reset),
    ]:
        action_sp = actions.add_parser(name, help=help_)
        action_sp.add_argument(
            "target",
            choices=list(TARGETS),
            help="which local stack to act on",
        )
        action_sp.set_defaults(func=fn)
