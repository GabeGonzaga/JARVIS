"""
JARVIS CLI - Command Line Interface
Provides interactive chat with the JARVIS assistant
"""

import subprocess
from typing import Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from jarvis.core.orchestrator import Orchestrator

console = Console()

# ---- Local date/time helpers (macOS system clock, no LLM) ----
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
    # Uses macOS system clock + system timezone (same as menu bar)
    return subprocess.check_output(["/bin/date", f"+{fmt}"], text=True).strip()


def _get_date_ddmmyyyy() -> str:
    return _sys_date("%d-%m-%Y")


def _get_time_hhmm() -> str:
    return _sys_date("%H:%M")


def _get_weekday_pt() -> str:
    # %u -> 1..7 (Mon..Sun)
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


def print_banner() -> None:
    banner = """
    ╔═══════════════════════════════════════╗
    ║                                       ║
    ║            J.A.R.V.I.S.               ║
    ║   Just A Rather Very Intelligent      ║
    ║           System v0.1                 ║
    ║                                       ║
    ║        macOS Personal Assistant       ║
    ║                                       ║
    ╚═══════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")
    console.print()


def print_help() -> None:
    help_text = """
**Comandos Disponíveis:**

- `/quit` ou `/exit` - Sair do JARVIS
- `/help` - Mostrar esta ajuda
- `/tools` - Listar ferramentas disponíveis
- `/model <nome>` - Trocar modelo LLM (ex: `/model llama3.1:latest`)
- `/reset` - Limpar histórico de conversa
- `/clear` - Limpar ecrã

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

**Segurança:**

- Ações de risco médio/alto requerem autorização
- Digite sua master password quando solicitado
- Confirme com código AUTHORIZE quando pedido
    """
    console.print(Panel(Markdown(help_text), title="Ajuda", border_style="cyan"))


def _handle_meta_command(cmd: str) -> Tuple[bool, bool]:
    """
    Returns (handled, should_exit)
    """
    if cmd in QUIT_CMDS:
        console.print("\n[yellow]Desligando JARVIS. Até breve![/yellow]")
        return True, True

    if cmd in HELP_CMDS:
        print_help()
        return True, False

    if cmd in CLEAR_CMDS:
        console.clear()
        print_banner()
        return True, False

    if cmd == "/reset":
        console.print("[yellow]Histórico limpo[/yellow]")
        return True, False

    return False, False


def run_cli() -> None:
    print_banner()

    try:
        console.print("[yellow]Inicializando JARVIS...[/yellow]")
        jarvis = Orchestrator()
        console.print("[green]JARVIS online e pronto![/green]\n")

    except FileNotFoundError as e:
        console.print(f"[red]Ficheiro não encontrado: {e}[/red]")
        console.print("[yellow]Execute: cp config/settings.example.json config/settings.json[/yellow]")
        return

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
                if shortcut_response := _handle_shortcuts(cmd):
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
                if response := jarvis.handle(user_input):
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


if __name__ == "__main__":
    run_cli()
