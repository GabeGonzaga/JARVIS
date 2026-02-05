#!/usr/bin/env python3
"""
JARVIS Main Entry Point
- Touch ID startup gate (once per launch)
- Unified launcher: CLI / GUI / BOTH

Usage:
  python -m jarvis                 # default: CLI
  python -m jarvis cli             # CLI only
  python -m jarvis gui             # GUI only (web)
  python -m jarvis both            # GUI + CLI (shared server if you implement cli_client later)
  python -m jarvis --no-auth gui   # skip Touch ID (dev)
"""

import sys
import traceback


def main() -> None:
    """Main entry point for JARVIS"""
    try:
        # Parse minimal flags here (avoid importing argparse if you want ultra-minimal)
        argv = sys.argv[1:]
        no_auth = False
        if "--no-auth" in argv:
            no_auth = True
            argv = [a for a in argv if a != "--no-auth"]

        # ---- Touch ID gate (once per launch) ----
        if not no_auth:
            from jarvis.core.startup_auth import StartupAuthError, require_touchid_once

            try:
                require_touchid_once()
            except StartupAuthError as e:
                print(f"❌ {e}", file=sys.stderr)
                sys.exit(1)

        # ---- Mode selection ----
        # Default behavior: CLI
        mode = (argv[0].lower() if argv else "cli").strip()

        if mode in {"cli", "terminal"}:
            from jarvis.apps.cli import run_cli

            run_cli()
            return

        if mode in {"gui", "web"}:
            # Starts FastAPI/uvicorn server (implement in launcher)
            # and opens browser automatically.
            from jarvis.apps.launcher import main as launcher_main

            # delegate to launcher so you don't duplicate server logic here
            sys.argv = [sys.argv[0], "gui"]
            launcher_main()
            return

        if mode in {"both"}:
            from jarvis.apps.launcher import main as launcher_main

            sys.argv = [sys.argv[0], "both"]
            launcher_main()
            return

        # Backwards compatible: if user types anything else, run CLI
        from jarvis.apps.cli import run_cli

        run_cli()

    except ImportError as e:
        print(f"❌ Erro de importação: {e}", file=sys.stderr)
        print("\n💡 Solução:", file=sys.stderr)
        print("  1. Certifique-se que está na venv: source .venv/bin/activate", file=sys.stderr)
        print("  2. Reinstale o pacote: python -m pip install -e .", file=sys.stderr)
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n👋 JARVIS desligado. Até breve!")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Erro fatal: {e}", file=sys.stderr)
        print("\n📋 Stack trace completa:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
