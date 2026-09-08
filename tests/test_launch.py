"""Boot the shipped CLI entry and hit GET / over real HTTP."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from kurpaest.app import root

ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_cli_entry_serves_root_identity() -> None:
    port = _free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "kurpaest",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    url = f"http://127.0.0.1:{port}/"
    try:
        body = None
        last_err: Exception | None = None
        for _ in range(80):
            time.sleep(0.1)
            if proc.poll() is not None:
                err = (proc.stderr.read() or b"").decode()
                raise AssertionError(f"server exited {proc.returncode}: {err}")
            try:
                with urllib.request.urlopen(url, timeout=0.5) as resp:
                    assert resp.status == 200
                    body = json.loads(resp.read().decode())
                break
            except (
                urllib.error.URLError,
                TimeoutError,
                ConnectionError,
                OSError,
            ) as exc:
                last_err = exc
        else:
            raise AssertionError(f"server did not respond at {url}: {last_err}")
        assert body == root()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
