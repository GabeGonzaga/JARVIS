#!/usr/bin/env python3
"""
JARVIS Main Entry Point
Unified launcher with Terminal mode and Web interface
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

# ============================================
# CLI MODE (Terminal)
# ============================================

_PT_WEEKDAYS = {
    1: "segunda-feira",
    2: "terça-feira",
    3: "quarta-feira",
    4: "quinta-feira",
    5: "sexta-feira",
    6: "sábado",
    7: "domingo",
}

QUIT_CMDS = {"/quit", "/exit", "/sair"}
HELP_CMDS = {"/help", "/ajuda"}
CLEAR_CMDS = {"/clear", "/limpar"}
SHORTCUT_CMDS = {"/time", "/date", "/weekday", "/day", "/hora", "/data", "/dia"}


def _sys_date(fmt: str) -> str:
    return subprocess.check_output(["/bin/date", f"+{fmt}"], text=True).strip()


def _get_date_ddmmyyyy() -> str:
    return _sys_date("%d-%m-%Y")


def _get_time_hhmm() -> str:
    return _sys_date("%H:%M")


def _get_weekday_pt() -> str:
    n = int(_sys_date("%u"))
    return _PT_WEEKDAYS.get(n, "desconhecido")


def _handle_shortcuts(cmd: str) -> Optional[str]:
    if cmd in {"/time", "/hora"}:
        return f"Hora: {_get_time_hhmm()}"
    if cmd in {"/date", "/data"}:
        return f"Data: {_get_date_ddmmyyyy()}"
    if cmd == "/weekday":
        return f"Dia da semana: {_get_weekday_pt()}"
    if cmd in {"/day", "/dia"}:
        return f"Dia: {_get_weekday_pt()}, {_get_date_ddmmyyyy()}"
    return None


def _boxed(lines: list[str], inner_width: int = 59) -> str:
    top = "╔" + ("═" * inner_width) + "╗"
    bot = "╚" + ("═" * inner_width) + "╝"
    out = [top]
    for s in lines:
        s = s[:inner_width]
        out.append("║" + s.ljust(inner_width) + "║")
    out.append(bot)
    return "\n".join(out)


def _center(s: str, width: int = 59) -> str:
    if len(s) >= width:
        return s[:width]
    pad = (width - len(s)) // 2
    return (" " * pad) + s + (" " * (width - pad - len(s)))


def print_cli_banner() -> None:
    art = [
        _center(""),
        _center("J.A.R.V.I.S."),
        _center("Just A Rather Very Intelligent System Mark 2"),
        _center(""),
        _center("macOS Personal Assistant"),
        _center(""),
    ]
    console.print(_boxed(art), style="bold cyan")
    console.print()


def print_help() -> None:
    help_text = """
**Comandos Disponíveis:**

- `/quit` ou `/exit` - Sair do JARVIS
- `/help` - Mostrar esta ajuda
- `/clear` - Limpar ecrã
- `/reset` - Limpar histórico de conversa
- `/tools` - Listar ferramentas disponíveis

**Data/Hora (local, sem LLM):**

- `/time` ou `/hora` - Hora atual (HH:MM)
- `/date` ou `/data` - Data atual (DD-MM-YYYY)
- `/weekday` - Dia da semana
- `/day` ou `/dia` - Dia da semana + data

**Ações Disponíveis:**

- Abrir aplicações (ex: "abre o Safari")
- Criar notas (ex: "cria uma nota com título X")
- Listar ficheiros (ex: "lista o Desktop")
- Ler ficheiros (ex: "lê o ficheiro X")
- Controlar música (ex: "play music", "pause", "next")
- Ver tempo (ex: "weather in Lisbon")
    """
    console.print(Panel(Markdown(help_text), title="Ajuda", border_style="cyan"))


def _handle_meta_command(cmd: str) -> Tuple[bool, bool]:
    """Returns (handled, should_exit)"""
    if cmd in QUIT_CMDS:
        console.print("\n[yellow]Desligando JARVIS. Até breve![/yellow]")
        return True, True

    if cmd in HELP_CMDS:
        print_help()
        return True, False

    if cmd in CLEAR_CMDS:
        console.clear()
        print_cli_banner()
        return True, False

    if cmd == "/reset":
        console.print("[yellow]Histórico limpo[/yellow]")
        return True, False

    return False, False


def run_terminal_mode() -> None:
    console.clear()
    print_cli_banner()

    try:
        console.print("[yellow]Inicializando JARVIS...[/yellow]")
        from jarvis.core.orchestrator import Orchestrator

        jarvis = Orchestrator()
        console.print("[green]✓ JARVIS online e pronto![/green]\n")
    except Exception as e:
        console.print(f"[red]Erro ao inicializar: {e}[/red]")
        import traceback

        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return

    console.print("[dim]Digite /help para ver comandos disponíveis[/dim]")
    console.print("[dim]Digite sua pergunta ou comando para começar[/dim]\n")

    while True:
        try:
            user_input = console.input("[bold green]You>[/bold green] ").strip()
            if not user_input:
                continue

            cmd = user_input.lower()

            if cmd in SHORTCUT_CMDS:
                shortcut_response = _handle_shortcuts(cmd)
                if shortcut_response:
                    console.print("[bold cyan]JARVIS>[/bold cyan]", shortcut_response)
                    console.print()
                    continue

            handled, should_exit = _handle_meta_command(cmd)
            if handled:
                if should_exit:
                    break
                continue

            console.print()
            try:
                response = jarvis.handle(user_input)
                if response:
                    console.print("[bold cyan]JARVIS>[/bold cyan]", response)
            except KeyboardInterrupt:
                console.print("\n[yellow]Operação cancelada[/yellow]")
                continue
            except Exception as e:
                console.print(f"[red]Erro ao processar: {e}[/red]")
                console.print("[dim]Digite /help se precisar de ajuda[/dim]")

            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Use /quit para sair[/yellow]")
            continue
        except EOFError:
            console.print("\n[yellow]EOF detectado. Encerrando...[/yellow]")
            break


# ============================================
# WEB MODE
# ============================================

def _project_root() -> Path:
    p = Path(__file__).resolve()
    # expected: .../JARVIS/src/jarvis/__main__.py  -> parents[2] == .../JARVIS
    try:
        return p.parents[2]
    except Exception:
        return p.parent.parent


def _find_web_dir(root: Path) -> Optional[Path]:
    candidates = [
        root / "web",
        root / "src" / "web",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def run_web_mode() -> None:
    console.clear()
    console.print("\n[bold cyan]Launching Web Interface...[/bold cyan]")
    console.print("━" * 60)

    root = _project_root()
    web_dir = _find_web_dir(root)

    if not web_dir:
        console.print(f"\n[red]Error: web folder not found under {root}[/red]")
        console.print("[yellow]Expected one of:[/yellow]")
        console.print(f"  {root}/web")
        console.print(f"  {root}/src/web")
        time.sleep(2)
        return

    console.print("\n[yellow]Starting services...[/yellow]")
    console.print("  1) Starting JARVIS API server (port 8000)...")

    api_process = None
    try:
        api_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "jarvis.apps.web_api:app", "--host", "127.0.0.1", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(2)
        console.print("     [green]✓ API server running[/green]")
    except Exception as e:
        console.print(f"     [red]Failed to start API server: {e}[/red]")
        return

    console.print("  2) Starting web interface (port 3000)...")

    web_process = None
    try:
        web_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=web_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(3)
        console.print("     [green]✓ Web interface running[/green]")
    except Exception as e:
        console.print(f"     [red]Failed to start web interface: {e}[/red]")
        return

    console.print("\n" + "━" * 60)
    console.print("\n[green]✓ JARVIS Web Interface is ready[/green]")
    console.print("\n[bold cyan]Access: http://localhost:3000[/bold cyan]")
    console.print("\n[dim]Press Ctrl+C to stop[/dim]\n")

    try:
        subprocess.run(["open", "http://localhost:3000"], check=False)
        if web_process:
            web_process.wait()
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down services...[/yellow]")
        if web_process:
            web_process.terminate()
        if api_process:
            api_process.terminate()
        time.sleep(1)
        console.print("[green]✓ Services stopped[/green]")


# ============================================
# MAIN LAUNCHER
# ============================================

def print_main_banner() -> None:
    art_lines = [
        "",
        "       ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗        ",
        "       ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝        ",
        "       ██║███████║██████╔╝██║   ██║██║███████╗        ",
        "  ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║        ",
        "  ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║        ",
        "   ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝        ",
        "",
        _center("J.A.R.V.I.S.  Just A Rather Very Intelligent System Mark 2"),
        _center(""),
        _center("Unified Launcher"),
        _center(""),
    ]
    # Normalize to inner width (59)
    norm = [_center(s) if s.strip() else " " * 59 for s in art_lines]
    console.print(_boxed(norm), style="bold cyan")


def authenticate() -> bool:
    console.print("\n[bold cyan]Authentication Required[/bold cyan]")
    console.print("━" * 60)
    console.print("\n[yellow]Authenticate using Touch ID...[/yellow]")

    try:
        result = subprocess.run(
            ["security", "authorizationdb", "read", "system.login.screensaver"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            console.print("[green]✓ Authentication successful[/green]")
            time.sleep(0.5)
            return True
        console.print("[red]✗ Authentication failed[/red]")
        return False
    except subprocess.TimeoutExpired:
        console.print("[red]✗ Authentication timeout[/red]")
        return False
    except Exception:
        console.print("\n[yellow]Touch ID not available, using demo mode[/yellow]")
        time.sleep(1)
        return True


def show_menu() -> None:
    console.print("\n[bold cyan]Select Interface Mode[/bold cyan]")
    console.print("━" * 60)
    console.print("\n  [bold green][1][/bold green] Terminal Mode - CLI with colors")
    console.print("  [bold blue][2][/bold blue] Web Interface - localhost:3000")
    console.print("  [bold red][3][/bold red] Exit\n")


def main() -> None:
    console.clear()
    print_main_banner()

    if not authenticate():
        console.print("\n[red]Authentication required to use JARVIS[/red]")
        sys.exit(1)

    while True:
        console.clear()
        print_main_banner()
        show_menu()

        try:
            choice = console.input("[bold yellow]Select option [1-3]:[/bold yellow] ").strip()
            if choice == "1":
                run_terminal_mode()
                break
            if choice == "2":
                run_web_mode()
                break
            if choice == "3":
                console.print("\n[yellow]Goodbye, Sir.[/yellow]")
                break

            console.print("\n[red]Invalid option. Select 1, 2, or 3.[/red]")
            time.sleep(1.2)
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Goodbye, Sir.[/yellow]")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
