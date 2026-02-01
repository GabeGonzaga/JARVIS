#!/usr/bin/env python3
"""
JARVIS Main Entry Point
Handles CLI execution with proper error handling + Touch ID startup gate
"""

import sys
import traceback


def main() -> None:
    """Main entry point for JARVIS CLI"""
    try:
        # Import here to catch import errors properly
        from jarvis.core.startup_auth import require_touchid_once, StartupAuthError
        from jarvis.apps.cli import run_cli

        # Touch ID gate (once per launch)
        try:
            require_touchid_once()
        except StartupAuthError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)

        # Run the CLI
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
