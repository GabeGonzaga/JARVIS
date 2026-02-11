#!/bin/bash
# JARVIS Web Interface - Complete Setup Script
# Run this from your JARVIS project root

set -e  # Exit on any error

echo "🚀 JARVIS Web Interface - Complete Setup"
echo "========================================"
echo ""

# Get the directory where the script is run from
PROJECT_ROOT=$(pwd)
WEB_DIR="$PROJECT_ROOT/web"

echo "📁 Project root: $PROJECT_ROOT"
echo "📁 Web directory: $WEB_DIR"
echo ""

# Step 1: Clean old installation
echo "🧹 Step 1: Cleaning old installation..."
if [ -d "$WEB_DIR" ]; then
    echo "   Removing old web directory..."
    rm -rf "$WEB_DIR"
fi
echo "   ✅ Clean!"
echo ""

# Step 2: Create directory structure
echo "📂 Step 2: Creating directory structure..."
mkdir -p "$WEB_DIR/pages"
mkdir -p "$WEB_DIR/server/api"
echo "   ✅ Directories created!"
echo ""

# Step 3: Create package.json
echo "📦 Step 3: Creating package.json..."
cat > "$WEB_DIR/package.json" << 'EOF'
{
  "name": "jarvis-web",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "nuxt dev",
    "build": "nuxt build",
    "preview": "nuxt preview"
  },
  "dependencies": {
    "@nuxt/ui": "^2.14.0",
    "nuxt": "^3.10.3",
    "vue": "^3.4.21"
  }
}
EOF
echo "   ✅ package.json created!"
echo ""

# Step 4: Create nuxt.config.ts
echo "⚙️  Step 4: Creating nuxt.config.ts..."
cat > "$WEB_DIR/nuxt.config.ts" << 'EOF'
export default defineNuxtConfig({
  modules: ['@nuxt/ui'],
  
  devtools: { enabled: false },
  
  compatibilityDate: '2026-02-06'
})
EOF
echo "   ✅ nuxt.config.ts created!"
echo ""

# Step 5: Create app.config.ts
echo "⚙️  Step 5: Creating app.config.ts..."
cat > "$WEB_DIR/app.config.ts" << 'EOF'
export default {
  ui: {
    primary: 'blue',
    gray: 'slate'
  }
}
EOF
echo "   ✅ app.config.ts created!"
echo ""

# Step 6: Create app.vue
echo "📄 Step 6: Creating app.vue..."
cat > "$WEB_DIR/app.vue" << 'EOF'
<template>
  <div>
    <NuxtPage />
  </div>
</template>
EOF
echo "   ✅ app.vue created!"
echo ""

# Step 7: Create pages/index.vue
echo "📄 Step 7: Creating pages/index.vue..."
cat > "$WEB_DIR/pages/index.vue" << 'EOF'
<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
    <!-- Mouse glow effect -->
    <div 
      class="pointer-events-none fixed w-96 h-96 rounded-full opacity-0 transition-opacity duration-300"
      :style="{
        left: mouseX + 'px',
        top: mouseY + 'px',
        transform: 'translate(-50%, -50%)',
        background: 'radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%)',
        opacity: showGlow ? 0.6 : 0
      }"
    ></div>

    <!-- Header -->
    <div class="max-w-4xl mx-auto mb-8">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">
            <span class="text-white font-bold text-2xl">J</span>
          </div>
          <div>
            <h1 class="text-3xl font-bold text-white">JARVIS</h1>
            <p class="text-sm text-slate-400">Your AI Assistant</p>
          </div>
        </div>
        
        <!-- Language selector -->
        <select 
          v-model="currentLanguage" 
          class="px-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-700 focus:border-blue-500 outline-none"
        >
          <option value="pt">Português (PT)</option>
          <option value="en">English</option>
          <option value="es">Español</option>
          <option value="fr">Français</option>
        </select>
      </div>

      <!-- Auth Modal -->
      <div v-if="!authenticated" class="text-center py-12">
        <div class="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center mx-auto mb-6">
          <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4"></path>
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-white mb-4">Authentication Required</h2>
        <p class="text-slate-400 mb-6">Please authenticate with Touch ID to access JARVIS</p>
        <button 
          @click="authenticate"
          :disabled="isAuthenticating"
          class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition disabled:opacity-50"
        >
          {{ isAuthenticating ? 'Authenticating...' : 'Authenticate with Touch ID' }}
        </button>
      </div>

      <!-- Chat Interface -->
      <div v-else class="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-2xl">
        <!-- Messages -->
        <div ref="messagesContainer" class="h-96 overflow-y-auto mb-4 space-y-4">
          <div 
            v-for="(msg, i) in messages" 
            :key="i"
            :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
          >
            <div 
              :class="[
                'max-w-[80%] rounded-2xl px-4 py-3',
                msg.role === 'user' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-slate-800 text-slate-100 border border-slate-700'
              ]"
            >
              <p class="text-sm whitespace-pre-wrap">{{ msg.content }}</p>
              <span class="text-xs opacity-60 mt-1 block">{{ formatTime(msg.timestamp) }}</span>
            </div>
          </div>
          
          <!-- Loading -->
          <div v-if="loading" class="flex justify-start">
            <div class="bg-slate-800 border border-slate-700 rounded-2xl px-4 py-3">
              <div class="flex gap-1">
                <div class="w-2 h-2 rounded-full bg-blue-500 animate-bounce"></div>
                <div class="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style="animation-delay: 150ms"></div>
                <div class="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style="animation-delay: 300ms"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Input -->
        <div class="flex gap-2">
          <input
            v-model="input"
            @keypress.enter="sendMessage"
            :disabled="loading"
            placeholder="Ask JARVIS anything..."
            class="flex-1 px-4 py-3 bg-slate-800 text-white rounded-lg border border-slate-700 focus:border-blue-500 outline-none disabled:opacity-50"
          />
          <button
            @click="sendMessage"
            :disabled="loading || !input.trim()"
            class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition disabled:opacity-50"
          >
            Send
          </button>
        </div>

        <!-- Quick actions -->
        <div class="mt-4 flex flex-wrap gap-2">
          <button
            v-for="action in quickActions"
            :key="action.label"
            @click="input = action.query"
            class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded-lg transition"
          >
            {{ action.label }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'

// Mouse glow
const mouseX = ref(0)
const mouseY = ref(0)
const showGlow = ref(false)

const handleMouseMove = (e) => {
  mouseX.value = e.clientX
  mouseY.value = e.clientY
  showGlow.value = true
}

onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', handleMouseMove)
})

// Auth
const authenticated = ref(false)
const isAuthenticating = ref(false)

const authenticate = async () => {
  isAuthenticating.value = true
  await new Promise(resolve => setTimeout(resolve, 1500))
  authenticated.value = true
  isAuthenticating.value = false
}

// Language
const currentLanguage = ref('pt')

// Chat
const messages = ref([
  {
    role: 'assistant',
    content: 'Sir, I am JARVIS. How may I assist you today?',
    timestamp: new Date()
  }
])

const messagesContainer = ref(null)
const input = ref('')
const loading = ref(false)

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const sendMessage = async () => {
  if (!input.value.trim() || loading.value) return

  messages.value.push({
    role: 'user',
    content: input.value,
    timestamp: new Date()
  })

  const query = input.value
  input.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const response = await $fetch('/api/chat', {
      method: 'POST',
      body: {
        message: query,
        language: currentLanguage.value
      }
    })

    messages.value.push({
      role: 'assistant',
      content: response.ok ? response.response : `Sir, error: ${response.error}`,
      timestamp: new Date()
    })
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: 'Sir, I encountered an error connecting to the backend. Please ensure the API server is running on port 8000.',
      timestamp: new Date()
    })
  }

  loading.value = false
  await scrollToBottom()
}

const formatTime = (date) => {
  return new Intl.DateTimeFormat('en', {
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

const quickActions = [
  { label: 'Time', query: 'what time is it?' },
  { label: 'Music', query: 'play some music' },
  { label: 'Weather', query: 'weather in Lisbon' }
]
</script>

<style>
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
.animate-bounce {
  animation: bounce 1s infinite;
}
</style>
EOF
echo "   ✅ pages/index.vue created!"
echo ""

# Step 8: Create server/api/chat.post.ts
echo "📄 Step 8: Creating server/api/chat.post.ts..."
cat > "$WEB_DIR/server/api/chat.post.ts" << 'EOF'
export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const { message, language = 'pt' } = body

  if (!message) {
    return {
      ok: false,
      error: 'No message provided'
    }
  }

  try {
    // Forward to Python backend (FastAPI server on port 8000)
    const response = await $fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      body: {
        message,
        language
      }
    })

    return response
  } catch (error) {
    // If backend is not available, return friendly error
    return {
      ok: false,
      error: 'Cannot connect to JARVIS backend. Please start it with: python -m jarvis.api.server'
    }
  }
})
EOF
echo "   ✅ server/api/chat.post.ts created!"
echo ""

# Step 9: Install dependencies
echo "📦 Step 9: Installing npm dependencies..."
echo "   This may take 2-3 minutes..."
cd "$WEB_DIR"
npm install
echo "   ✅ Dependencies installed!"
echo ""

# Step 10: Done!
echo "✅ Setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 JARVIS Web Interface is ready!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To start the web interface:"
echo ""
echo "1. Start the JARVIS API backend (in one terminal):"
echo "   cd $PROJECT_ROOT"
echo "   python -m jarvis.api.server"
echo ""
echo "2. Start the web interface (in another terminal):"
echo "   cd $WEB_DIR"
echo "   npm run dev"
echo ""
echo "3. Open your browser at: http://localhost:3000"
echo ""
echo "Or use the integrated launcher:"
echo "   python -m jarvis"
echo "   Select [2] Web Interface"
echo ""
