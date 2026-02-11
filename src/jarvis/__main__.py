#!/usr/bin/env python3
"""
JARVIS - Main Entry Point
Launch JARVIS in Terminal or Web mode with Touch ID authentication
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


def clear_screen():
    """Clear the terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def print_banner():
    """Print JARVIS ASCII banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗              ║
    ║     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝              ║
    ║     ██║███████║██████╔╝██║   ██║██║███████╗              ║
    ║██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║              ║
    ║╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║              ║
    ║ ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝              ║
    ║                                                           ║
    ║          Your Advanced AI Assistant                      ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def authenticate():
    """Simulate Touch ID authentication."""
    print("\n🔐 Authentication Required")
    print("━" * 60)
    print("\nPlease authenticate using Touch ID...")
    
    try:
        # On macOS, use security command for Touch ID
        result = subprocess.run(
            ["security", "authorizationdb", "read", "system.login.screensaver"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✓ Authentication successful!")
            time.sleep(0.5)
            return True
        else:
            print("✗ Authentication failed")
            return False
    except subprocess.TimeoutExpired:
        print("✗ Authentication timeout")
        return False
    except Exception:
        # Fallback for non-macOS or demo mode
        print(f"\n⚠️  Touch ID not available, using demo mode")
        time.sleep(1)
        return True


def show_menu():
    """Display the main menu."""
    print("\n📋 Select Interface Mode")
    print("━" * 60)
    print("\n  [1] Terminal Mode - Classic CLI interface")
    print("  [2] Web Interface - Modern web UI (localhost:3000)")
    print("  [3] Exit")
    print()


def launch_terminal_mode():
    """Launch JARVIS in terminal mode."""
    clear_screen()
    print("\n🚀 Launching Terminal Mode...")
    print("━" * 60)
    time.sleep(0.5)
    
    try:
        from jarvis.cli.repl import main as repl_main
        print("\n✓ Terminal mode ready!")
        print()
        repl_main()
    except ImportError:
        # Fallback simple mode
        print("\n✓ Terminal mode ready!")
        print("\nType your commands below (or 'exit' to quit):\n")
        
        from jarvis.core.orchestrator import Orchestrator
        orchestrator = Orchestrator()
        
        while True:
            try:
                user_input = input("You> ").strip()
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\nJARVIS> Goodbye, Sir.")
                    break
                if user_input:
                    response = orchestrator.handle(user_input)
                    print(f"JARVIS> {response}")
            except KeyboardInterrupt:
                print("\n\nJARVIS> Goodbye, Sir.")
                break
            except EOFError:
                break


def launch_web_mode():
    """Launch JARVIS web interface."""
    clear_screen()
    print("\n🌐 Launching Web Interface...")
    print("━" * 60)
    
    # Find project root (where 'web' folder should be)
    project_root = Path(__file__).parent.parent
    web_dir = project_root / "web"
    
    if not web_dir.exists():
        print(f"\n✗ Error: Web interface not found at {web_dir}")
        print("\nPlease create the web directory and install dependencies:")
        print(f"  cd {project_root}")
        print("  mkdir -p web")
        print("  # Copy web files")
        print("  cd web && npm install")
        time.sleep(3)
        return
    
    print("\n📦 Starting services...")
    
    # Start FastAPI backend
    print("  1. Starting JARVIS API server (port 8000)...")
    api_process = None
    try:
        api_process = subprocess.Popen(
            [sys.executable, "-m", "jarvis.api.server"],
            stdout=None,
            stderr=None
        )
        time.sleep(2)
        print("     ✓ API server running")
    except Exception as e:
        print(f"     ✗ Failed to start API server: {e}")
        print("     Make sure FastAPI is installed: pip install fastapi uvicorn")
    
    # Start Nuxt dev server
    print("  2. Starting web interface (port 3000)...")
    web_process = None
    try:
        web_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=web_dir,
            stdout=None,
            stderr=None
        )
        time.sleep(3)
        print("     ✓ Web interface running")
    except Exception as e:
        print(f"     ✗ Failed to start web interface: {e}")
        print(f"     Make sure to run 'npm install' in {web_dir}")
    
    print("\n" + "━" * 60)
    print("\n✓ JARVIS Web Interface is ready!")
    print("\n📍 Access at: http://localhost:3000")
    print("\n💡 Press Ctrl+C to stop the servers")
    print()
    
    try:
        # Open browser
        subprocess.run(["open", "http://localhost:3000"], check=False)
        
        # Wait for user interrupt
        if web_process:
            web_process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        if web_process:
            web_process.terminate()
        if api_process:
            api_process.terminate()
        time.sleep(1)
        print("✓ Services stopped")


def main():
    """Main launcher function."""
    clear_screen()
    print_banner()
    
    # Authenticate first
    if not authenticate():
        print("\n✗ Authentication required to use JARVIS")
        sys.exit(1)
    
    # Show menu
    while True:
        clear_screen()
        print_banner()
        show_menu()
        
        try:
            choice = input("Select option [1-3]: ").strip()
            
            if choice == "1":
                launch_terminal_mode()
                break
            elif choice == "2":
                launch_web_mode()
                break
            elif choice == "3":
                print("\nGoodbye, Sir.")
                break
            else:
                print("\n✗ Invalid option. Please select 1, 2, or 3.")
                time.sleep(1.5)
        except KeyboardInterrupt:
            print("\n\nGoodbye, Sir.")
            break
        except EOFError:
            print("\n\nGoodbye, Sir.")
            break


if __name__ == "__main__":
    main()
