# src/jarvis/apps/launcher.py
import argparse
import os
import subprocess
import sys
import time
import webbrowser
from urllib.request import urlopen

DEFAULT_URL = "http://127.0.0.1:8000"

def _server_up(url: str) -> bool:
    try:
        urlopen(url, timeout=0.4)
        return True
    except Exception:
        return False

def run_server() -> None:
    # Uses python -m uvicorn so it always uses the venv interpreter
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "jarvis.web.app:app",
         "--reload", "--reload-dir", "src", "--reload-exclude", ".venv"],
        stdout=sys.stdout, stderr=sys.stderr,
    )

def main() -> None:
    p = argparse.ArgumentParser(prog="jarvis")
    sub = p.add_subparsers(dest="mode")

    sub.add_parser("cli")
    sub.add_parser("gui")
    sub.add_parser("both")

    args = p.parse_args()
    mode = args.mode or "cli"
    url = os.environ.get("JARVIS_URL", DEFAULT_URL)

    if mode in ("gui", "both"):
        if not _server_up(url):
            run_server()
            for _ in range(40):
                if _server_up(url):
                    break
                time.sleep(0.15)
        webbrowser.open(url)

    if mode in ("cli", "both"):
        from jarvis.apps.cli_client import run_cli_client
        run_cli_client(url)

if __name__ == "__main__":
    main()
