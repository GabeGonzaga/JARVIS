<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
    <!-- Simple gradient background -->
    <div class="absolute inset-0 opacity-20">
      <div class="absolute top-0 left-1/4 w-96 h-96 bg-blue-500 rounded-full blur-3xl"></div>
      <div class="absolute bottom-0 right-1/4 w-96 h-96 bg-cyan-500 rounded-full blur-3xl"></div>
    </div>

    <!-- Mouse glow (simple version) -->
    <div 
      class="fixed pointer-events-none w-64 h-64 rounded-full transition-opacity"
      :style="{
        left: mx + 'px',
        top: my + 'px',
        transform: 'translate(-50%, -50%)',
        background: 'radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%)',
        opacity: showGlow ? 0.6 : 0
      }"
    ></div>

    <div class="relative z-10">
      <!-- Header -->
      <header class="border-b border-slate-800 backdrop-blur-xl bg-slate-950/30">
        <div class="container mx-auto px-6 py-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">
                <span class="text-white font-bold text-2xl">J</span>
              </div>
              <div>
                <h1 class="text-2xl font-bold text-white">JARVIS</h1>
                <p class="text-xs text-slate-400">AI Assistant</p>
              </div>
            </div>

            <div class="flex items-center gap-3">
              <select v-model="lang" class="px-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-700">
                <option value="pt">Português</option>
                <option value="en">English</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
              </select>
            </div>
          </div>
        </div>
      </header>

      <!-- Main content -->
      <div class="container mx-auto px-6 py-12">
        <div class="max-w-4xl mx-auto">
          
          <!-- Logo -->
          <div class="flex justify-center mb-12">
            <div class="relative">
              <div class="w-40 h-40 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center shadow-2xl">
                <div class="text-center">
                  <div class="text-5xl font-bold text-white mb-1">J</div>
                  <div class="text-xs text-blue-100">ONLINE</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Title -->
          <div class="text-center mb-12">
            <h2 class="text-5xl font-bold text-white mb-4">
              J.A.R.V.I.S.
            </h2>
            <p class="text-xl text-slate-300">
              Just A Rather Very Intelligent System
            </p>
          </div>

          <!-- Input card -->
          <div class="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-2xl mb-8">
            <div class="flex gap-3 mb-4">
              <input
                v-model="input"
                @keypress.enter="send"
                :disabled="loading"
                placeholder="Ask JARVIS anything..."
                class="flex-1 px-4 py-3 bg-slate-800 text-white rounded-lg border border-slate-700 focus:border-blue-500 outline-none"
              />
              <button
                @click="send"
                :disabled="loading || !input.trim()"
                class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition disabled:opacity-50"
              >
                Send
              </button>
            </div>

            <!-- Responses -->
            <div v-if="responses.length > 0" class="space-y-3 max-h-64 overflow-y-auto">
              <div v-for="(r, i) in responses" :key="i" 
                   class="p-4 bg-slate-800/50 border border-slate-700 rounded-xl">
                <div class="flex items-start gap-3">
                  <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                    <span class="text-white text-sm font-bold">J</span>
                  </div>
                  <div class="flex-1">
                    <div class="text-xs text-slate-500 mb-1">{{ formatTime(r.time) }}</div>
                    <div class="text-sm text-slate-200 whitespace-pre-wrap">{{ r.text }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Features -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div v-for="f in features" :key="f.title"
                 class="bg-slate-900/30 backdrop-blur-xl border border-slate-800 rounded-xl p-6 text-center">
              <div class="text-4xl mb-3">{{ f.icon }}</div>
              <h3 class="text-lg font-semibold text-white mb-2">{{ f.title }}</h3>
              <p class="text-sm text-slate-400">{{ f.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

// Mouse tracking
const mx = ref(0), my = ref(0), showGlow = ref(false)
onMounted(() => {
  const move = (e) => { mx.value = e.clientX; my.value = e.clientY; showGlow.value = true }
  document.addEventListener('mousemove', move)
  onBeforeUnmount(() => document.removeEventListener('mousemove', move))
})

// Language
const lang = ref('pt')

// Chat
const input = ref('')
const loading = ref(false)
const responses = ref([])

const send = async () => {
  if (!input.value.trim() || loading.value) return
  
  const msg = input.value
  input.value = ''
  loading.value = true

  try {
    const res = await $fetch('/api/chat', {
      method: 'POST',
      body: { message: msg, language: lang.value }
    })

    responses.value.unshift({
      text: res.ok ? res.response : `Error: ${res.error}`,
      time: new Date()
    })

    if (responses.value.length > 5) responses.value.pop()
  } catch {
    responses.value.unshift({
      text: 'Connection error. Start backend: python -m uvicorn jarvis.apps.web_api:app --port 8000',
      time: new Date()
    })
  }

  loading.value = false
}

const formatTime = (d) => new Intl.DateTimeFormat('en-GB', {
  hour: '2-digit', minute: '2-digit', second: '2-digit'
}).format(d)

const features = [
  { icon: '🌐', title: 'Multi-Language', desc: 'EN • PT • ES • FR' },
  { icon: '⚡', title: 'Real-Time', desc: 'Instant responses' },
  { icon: '🔒', title: 'Secure', desc: 'Local processing' }
]
</script>
