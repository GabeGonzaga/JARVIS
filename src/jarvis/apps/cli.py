"""
JARVIS CLI - Command Line Interface
Provides interactive chat with the JARVIS assistant
"""

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from jarvis.core.orchestrator import Orchestrator

console = Console()


def print_banner():
    """Print JARVIS startup banner"""
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


def print_help():
    """Print available commands"""
    help_text = """
**Comandos Disponíveis:**

- `/quit` ou `/exit` - Sair do JARVIS
- `/help` - Mostrar esta ajuda
- `/tools` - Listar ferramentas disponíveis
- `/model <nome>` - Trocar modelo LLM (ex: `/model llama3.1:latest`)
- `/reset` - Limpar histórico de conversa
- `/clear` - Limpar ecrã

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
    console.print(Panel(Markdown(help_text), title="📖 Ajuda", border_style="cyan"))


def run_cli() -> None:
    """
    Run the interactive JARVIS CLI
    
    Provides a REPL-style interface for chatting with JARVIS
    and executing system actions
    """
    print_banner()
    
    try:
        # Initialize orchestrator
        console.print("[yellow]Inicializando JARVIS...[/yellow]")
        jarvis = Orchestrator()
        console.print("[green]✅ JARVIS online e pronto![/green]\n")
        
    except FileNotFoundError as e:
        console.print(f"[red]❌ Ficheiro não encontrado: {e}[/red]")
        console.print("[yellow]💡 Execute: cp config/settings.example.json config/settings.json[/yellow]")
        return
        
    except Exception as e:
        console.print(f"[red]❌ Erro ao inicializar: {e}[/red]")
        import traceback
        console.print("[dim]" + traceback.format_exc() + "[/dim]")
        return
    
    # Show initial help
    console.print("[dim]Digite /help para ver comandos disponíveis[/dim]")
    console.print("[dim]Digite sua pergunta ou comando para começar[/dim]\n")
    
    # Main REPL loop
    while True:
        try:
            # Get user input
            user_input = console.input("[bold green]You>[/bold green] ").strip()
            
            # Skip empty input
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() in ["/quit", "/exit", "/sair"]:
                console.print("\n[yellow]👋 Desligando JARVIS. Até breve![/yellow]")
                break
            
            if user_input.lower() in ["/help", "/ajuda"]:
                print_help()
                continue
            
            if user_input.lower() in ["/clear", "/limpar"]:
                console.clear()
                print_banner()
                continue
            
            if user_input.lower() == "/reset":
                # Reset conversation (future implementation)
                console.print("[yellow]🔄 Histórico limpo[/yellow]")
                continue
            
            # Process user input through orchestrator
            console.print()  # Blank line for readability
            
            try:
                response = jarvis.handle(user_input)
                
                if response:
                    # Print JARVIS response
                    console.print("[bold cyan]JARVIS>[/bold cyan]", response)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]⚠️  Operação cancelada[/yellow]")
                continue
                
            except Exception as e:
                console.print(f"[red]❌ Erro ao processar: {e}[/red]")
                console.print("[dim]Digite /help se precisar de ajuda[/dim]")
            
            console.print()  # Blank line after response
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Use /quit para sair[/yellow]")
            continue
            
        except EOFError:
            console.print("\n[yellow]👋 EOF detectado. Encerrando...[/yellow]")
            break


if __name__ == "__main__":
    run_cli()