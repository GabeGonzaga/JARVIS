#!/bin/bash
# JARVIS Complete Redesign - Blueprint Style
# Terminal commands only - Copy & Paste

cd /Users/gabrielgonzaga/Desktop/jarvis/JARVIS

echo "🎨 JARVIS Complete Redesign - Starting..."

# Stop processes
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Clean old web
rm -rf src/web src/web_*

# Create structure
mkdir -p src/web/{pages,components,composables,assets/{css,images},server/api,public}

echo "📦 Creating files..."

# ============================================
# 1. PACKAGE.JSON
# ============================================
cat > src/web/package.json << 'EOF'
{
  "name": "jarvis-web",
  "version": "2.0.0",
  "private": true,
  "scripts": {
    "dev": "nuxt dev",
    "build": "nuxt build"
  },
  "dependencies": {
    "@nuxt/ui": "^2.14.0",
    "@vueuse/core": "^10.9.0",
    "nuxt": "^3.10.3",
    "vue": "^3.4.21"
  }
}
EOF

# ============================================
# 2. NUXT.CONFIG.TS
# ============================================
cat > src/web/nuxt.config.ts << 'EOF'
export default defineNuxtConfig({
  modules: ['@nuxt/ui'],
  
  colorMode: {
    preference: 'system',
    fallback: 'light',
    classSuffix: ''
  },

  ui: {
    global: true,
    icons: ['heroicons']
  },

  app: {
    head: {
      title: 'J.A.R.V.I.S. - Just A Rather Very Intelligent System',
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap' }
      ]
    }
  },

  devtools: { enabled: false },
  compatibilityDate: '2026-02-06'
})
EOF

# ============================================
# 3. APP.CONFIG.TS
# ============================================
cat > src/web/app.config.ts << 'EOF'
export default defineAppConfig({
  ui: {
    primary: 'blue',
    gray: 'slate'
  }
})
EOF

# ============================================
# 4. GLOBAL CSS
# ============================================
cat > src/web/assets/css/main.css << 'EOF'
@import "tailwindcss";

:root {
  --blueprint-blue: #2563eb;
  --blueprint-light: #60a5fa;
  --blueprint-dark: #1e3a8a;
  --bg-light: #f8fafc;
  --bg-dark: #0f172a;
  --text-light: #1e293b;
  --text-dark: #f1f5f9;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.dark body {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

.blueprint-pattern {
  background-image: 
    linear-gradient(rgba(37, 99, 235, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(37, 99, 235, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
}

.dark .blueprint-pattern {
  background-image: 
    linear-gradient(rgba(96, 165, 250, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(96, 165, 250, 0.05) 1px, transparent 1px);
}

.hexagon {
  clip-path: polygon(30% 0%, 70% 0%, 100% 50%, 70% 100%, 30% 100%, 0% 50%);
}

.blueprint-glow {
  box-shadow: 0 0 20px rgba(37, 99, 235, 0.3);
}

@keyframes pulse-ring {
  0% {
    transform: scale(0.9);
    opacity: 1;
  }
  100% {
    transform: scale(1.3);
    opacity: 0;
  }
}

.pulse-ring {
  animation: pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.rotate-slow {
  animation: rotate 20s linear infinite;
}
EOF

# ============================================
# 5. APP.VUE
# ============================================
cat > src/web/app.vue << 'EOF'
<template>
  <div>
    <link rel="stylesheet" href="/assets/css/main.css">
    <NuxtPage />
  </div>
</template>
EOF

# ============================================
# 6. INDEX.VUE - MAIN PAGE (BLUEPRINT STYLE)
# ============================================
cat > src/web/pages/index.vue << 'EOF'
<template>
  <div class="min-h-screen relative overflow-hidden transition-colors duration-300"
       :class="isDark ? 'bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950' : 'bg-slate-50'">
    
    <!-- Blueprint Grid Pattern -->
    <div class="absolute inset-0 blueprint-pattern opacity-40"></div>

    <!-- Radial Gradient Overlays -->
    <div class="absolute inset-0 pointer-events-none">
      <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
      <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl"></div>
    </div>

    <!-- Mouse Glow Effect -->
    <div 
      ref="mouseGlow"
      class="fixed pointer-events-none z-50 w-64 h-64 rounded-full transition-opacity duration-300"
      :style="{
        left: mousePos.x + 'px',
        top: mousePos.y + 'px',
        transform: 'translate(-50%, -50%)',
        background: isDark 
          ? 'radial-gradient(circle, rgba(59, 130, 246, 0.2) 0%, transparent 70%)'
          : 'radial-gradient(circle, rgba(37, 99, 235, 0.15) 0%, transparent 70%)',
        opacity: showGlow ? 0.8 : 0
      }"
    />

    <div class="relative z-10">
      <!-- Header -->
      <header class="border-b backdrop-blur-xl"
              :class="isDark ? 'border-slate-800 bg-slate-950/30' : 'border-slate-200 bg-white/30'">
        <div class="container mx-auto px-6 py-4">
          <div class="flex items-center justify-between">
            <!-- Logo -->
            <div class="flex items-center gap-3">
              <div class="relative w-10 h-10">
                <div class="w-10 h-10 rounded-lg flex items-center justify-center font-bold text-lg"
                     :class="isDark ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'">
                  J
                </div>
              </div>
              <div>
                <h1 class="text-lg font-bold" :class="isDark ? 'text-white' : 'text-slate-900'">
                  J.A.R.V.I.S.
                </h1>
                <p class="text-xs" :class="isDark ? 'text-slate-400' : 'text-slate-600'">
                  Just A Rather Very Intelligent System
                </p>
              </div>
            </div>

            <!-- Controls -->
            <div class="flex items-center gap-3">
              <USelectMenu v-model="selectedLang" :options="languages" class="w-36">
                <template #label>
                  <span class="text-sm">{{ selectedLang.label }}</span>
                </template>
              </USelectMenu>

              <ClientOnly>
                <UButton
                  :icon="isDark ? 'i-heroicons-moon-20-solid' : 'i-heroicons-sun-20-solid'"
                  color="gray"
                  variant="ghost"
                  @click="toggleDark"
                />
              </ClientOnly>
            </div>
          </div>
        </div>
      </header>

      <!-- Main Content -->
      <div class="container mx-auto px-6 py-12">
        <!-- Central JARVIS Interface -->
        <div class="max-w-5xl mx-auto">
          
          <!-- Central Logo with Pulsing Ring -->
          <div class="flex justify-center mb-12">
            <div class="relative">
              <!-- Outer ring (pulsing) -->
              <div class="absolute inset-0 w-48 h-48 rounded-full border-2 pulse-ring"
                   :class="isDark ? 'border-blue-500/30' : 'border-blue-600/30'"></div>
              
              <!-- Middle ring (rotating) -->
              <div class="absolute inset-4 rounded-full border rotate-slow"
                   :class="isDark ? 'border-blue-400/20 border-dashed' : 'border-blue-500/20 border-dashed'"></div>
              
              <!-- Central circle -->
              <div class="w-48 h-48 rounded-full flex items-center justify-center relative overflow-hidden"
                   :class="isDark ? 'bg-gradient-to-br from-blue-600 to-blue-800 shadow-2xl shadow-blue-500/30' : 'bg-gradient-to-br from-blue-500 to-blue-700 shadow-2xl shadow-blue-600/30'">
                <div class="text-center">
                  <div class="text-6xl font-bold text-white mb-2">J</div>
                  <div class="text-xs text-blue-100 font-medium">ONLINE</div>
                </div>
                
                <!-- Scanning line effect -->
                <div class="absolute inset-0 bg-gradient-to-b from-transparent via-white/10 to-transparent h-8 animate-pulse"></div>
              </div>
            </div>
          </div>

          <!-- Title -->
          <div class="text-center mb-12">
            <h2 class="text-4xl md:text-5xl font-bold mb-4"
                :class="isDark ? 'text-white' : 'text-slate-900'">
              Advanced AI Assistant
            </h2>
            <p class="text-lg max-w-2xl mx-auto"
               :class="isDark ? 'text-slate-300' : 'text-slate-600'">
              Multi-language support • Real-time processing • Intelligent responses
            </p>
          </div>

          <!-- Command Input (Center) -->
          <UCard class="mb-8 backdrop-blur-xl shadow-2xl"
                 :class="isDark ? 'bg-slate-900/50 border-slate-800' : 'bg-white/80 border-slate-200'">
            <div class="flex gap-3">
              <UInput
                v-model="userInput"
                placeholder="Enter command or query..."
                size="lg"
                :disabled="isProcessing"
                @keypress.enter="processCommand"
                class="flex-1"
              >
                <template #leading>
                  <UIcon name="i-heroicons-command-line" class="w-5 h-5" 
                         :class="isDark ? 'text-blue-400' : 'text-blue-600'" />
                </template>
              </UInput>
              <UButton
                icon="i-heroicons-play"
                size="lg"
                :loading="isProcessing"
                :disabled="!userInput.trim() || isProcessing"
                @click="processCommand"
                class="px-6"
                :class="isDark ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-500 hover:bg-blue-600'"
              >
                Execute
              </UButton>
            </div>
          </UCard>

          <!-- Response Area (Blueprint Style) -->
          <UCard v-if="responses.length > 0" 
                 class="backdrop-blur-xl shadow-2xl"
                 :class="isDark ? 'bg-slate-900/50 border-slate-800' : 'bg-white/80 border-slate-200'">
            <div class="space-y-4 max-h-96 overflow-y-auto">
              <div v-for="(resp, idx) in responses" :key="idx" class="p-4 rounded-lg border"
                   :class="isDark ? 'bg-slate-800/50 border-slate-700' : 'bg-slate-50 border-slate-200'">
                <div class="flex items-start gap-3">
                  <div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                       :class="isDark ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'">
                    J
                  </div>
                  <div class="flex-1">
                    <div class="text-xs mb-1 opacity-60">{{ formatTime(resp.timestamp) }}</div>
                    <div class="text-sm whitespace-pre-wrap font-mono"
                         :class="isDark ? 'text-slate-200' : 'text-slate-800'">{{ resp.content }}</div>
                  </div>
                </div>
              </div>
            </div>
          </UCard>

          <!-- Technical Specs Grid (Hexagons) -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
            <UCard v-for="spec in technicalSpecs" :key="spec.title"
                   class="backdrop-blur-xl hover:shadow-xl transition-all duration-300"
                   :class="isDark ? 'bg-slate-900/30 border-slate-800 hover:border-blue-500/50' : 'bg-white/60 border-slate-200 hover:border-blue-400/50'">
              <div class="text-center">
                <div class="w-16 h-16 mx-auto mb-4 hexagon flex items-center justify-center"
                     :class="isDark ? 'bg-blue-500/20' : 'bg-blue-100'">
                  <UIcon :name="spec.icon" class="w-8 h-8"
                         :class="isDark ? 'text-blue-400' : 'text-blue-600'" />
                </div>
                <h3 class="text-lg font-semibold mb-2"
                    :class="isDark ? 'text-white' : 'text-slate-900'">{{ spec.title }}</h3>
                <p class="text-sm"
                   :class="isDark ? 'text-slate-400' : 'text-slate-600'">{{ spec.description }}</p>
              </div>
            </UCard>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const colorMode = useColorMode()
const isDark = computed(() => colorMode.value === 'dark')
const toggleDark = () => colorMode.preference = isDark.value ? 'light' : 'dark'

// Mouse tracking
const mousePos = ref({ x: 0, y: 0 })
const showGlow = ref(false)

onMounted(() => {
  const handleMove = (e) => {
    mousePos.value = { x: e.clientX, y: e.clientY }
    showGlow.value = true
  }
  document.addEventListener('mousemove', handleMove)
  onBeforeUnmount(() => document.removeEventListener('mousemove', handleMove))
})

// Language
const languages = [
  { label: 'English', value: 'en' },
  { label: 'Português (PT)', value: 'pt' },
  { label: 'Español', value: 'es' },
  { label: 'Français', value: 'fr' }
]
const selectedLang = ref(languages[1])

// Command processing
const userInput = ref('')
const isProcessing = ref(false)
const responses = ref([])

const processCommand = async () => {
  if (!userInput.value.trim() || isProcessing.value) return
  
  const cmd = userInput.value
  userInput.value = ''
  isProcessing.value = true

  try {
    const res = await $fetch('/api/chat', {
      method: 'POST',
      body: { message: cmd, language: selectedLang.value.value }
    })

    responses.value.unshift({
      content: res.ok ? res.response : `Error: ${res.error}`,
      timestamp: new Date()
    })
  } catch (error) {
    responses.value.unshift({
      content: 'Connection error. Ensure backend is running on port 8000.',
      timestamp: new Date()
    })
  }

  isProcessing.value = false
}

const formatTime = (date) => {
  return new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(date)
}

// Technical specs
const technicalSpecs = [
  {
    icon: 'i-heroicons-language',
    title: 'Multi-Language',
    description: 'EN • PT • ES • FR with real-time translation'
  },
  {
    icon: 'i-heroicons-bolt',
    title: 'Real-Time Processing',
    description: 'Instant AI-powered responses via Ollama'
  },
  {
    icon: 'i-heroicons-shield-check',
    title: 'Secure & Private',
    description: 'Local processing with Touch ID auth'
  }
]
</script>
EOF

# ============================================
# 7. API ENDPOINT
# ============================================
cat > src/web/server/api/chat.post.ts << 'EOF'
export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const { message, language = 'pt' } = body

  if (!message) {
    return { ok: false, error: 'No message provided' }
  }

  try {
    const response = await $fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      body: { message, language }
    })
    return response
  } catch (error) {
    return {
      ok: false,
      error: 'Backend offline. Start with: python -m uvicorn jarvis.apps.web_api:app --port 8000'
    }
  }
})
EOF

# ============================================
# 8. Install dependencies
# ============================================
echo "📦 Installing npm packages..."
cd src/web
npm install

cd ../..

echo ""
echo "✅ JARVIS Web - Blueprint Style COMPLETE!"
echo ""
echo "Now updating CLI with colors..."

# ============================================
# UPDATE CLI WITH COLORS (from cli.py)
# ============================================
cat > src/jarvis/cli/repl.py << 'EOFCLI'
"""
JARVIS CLI - Command Line Interface
Rich colored terminal with blueprint aesthetics
"""
import subprocess
from typing import Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from jarvis.core.orchestrator import Orchestrator

console = Console()

_PT_WEEKDAYS = {
    1: "segunda-feira", 2: "terça-feira", 3: "quarta-feira",
    4: "quinta-feira", 5: "sexta-feira", 6: "sábado", 7: "domingo",
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
- `/clear` - Limpar ecrã
- `/time` ou `/hora` - Hora atual
- `/date` ou `/data` - Data atual

**Ações:**
- Controlar música, abrir apps, criar notas, listar ficheiros
    """
    console.print(Panel(Markdown(help_text), title="Ajuda", border_style="cyan"))

def _handle_meta_command(cmd: str) -> Tuple[bool, bool]:
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
    return False, False

def main() -> None:
    print_banner()
    try:
        console.print("[yellow]Inicializando JARVIS...[/yellow]")
        jarvis = Orchestrator()
        console.print("[green]✓ JARVIS online e pronto![/green]\n")
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        return

    console.print("[dim]Digite /help para comandos disponíveis[/dim]\n")

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
                console.print(f"[red]Erro: {e}[/red]")

            console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Use /quit para sair[/yellow]")
            continue
        except EOFError:
            break

if __name__ == "__main__":
    main()
EOFCLI

echo "✅ CLI updated with colors!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 JARVIS COMPLETE SETUP DONE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 To start:"
echo ""
echo "Terminal 1 (Backend):"
echo "  python -m uvicorn jarvis.apps.web_api:app --host 127.0.0.1 --port 8000"
echo ""
echo "Terminal 2 (Web - Blueprint Style):"
echo "  cd src/web && npm run dev"
echo ""
echo "Terminal 3 (CLI - Colored):"
echo "  python -m jarvis.cli.repl"
echo ""
echo "Or use unified launcher:"
echo "  python -m jarvis"
echo ""