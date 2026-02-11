#!/bin/bash
set -euo pipefail

ROOT="/Users/gabrielgonzaga/Desktop/jarvis/JARVIS"
cd "$ROOT"

# Stop ports (still forceful, but scoped to ports)
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Rebuild web folder from scratch
rm -rf src/web
mkdir -p src/web/{pages,components,assets/css,server/api,public}

# ----------------------------
# package.json
# ----------------------------
cat > src/web/package.json <<'JSON'
{
  "name": "jarvis-web",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "nuxt dev --host 127.0.0.1 --port 3000",
    "build": "nuxt build",
    "preview": "nuxt preview",
    "postinstall": "nuxt prepare"
  },
  "dependencies": {
    "@nuxt/ui": "^2.14.0",
    "nuxt": "^3.10.3",
    "vue": "^3.4.21"
  },
  "devDependencies": {
    "@nuxtjs/tailwindcss": "^6.11.4",
    "tailwindcss": "^3.4.17",
    "postcss": "^8.4.38",
    "autoprefixer": "^10.4.19"
  }
}
JSON

# ----------------------------
# nuxt.config.ts
# ----------------------------
cat > src/web/nuxt.config.ts <<'TS'
export default defineNuxtConfig({
  modules: ['@nuxt/ui', '@nuxtjs/tailwindcss'],
  css: ['~/assets/css/main.css'],

  colorMode: {
    preference: 'system',
    fallback: 'dark',
    classSuffix: ''
  },

  ui: {
    global: true,
    icons: ['heroicons', 'lucide']
  },

  devtools: { enabled: false },
  compatibilityDate: '2026-02-07'
})
TS

# ----------------------------
# app.config.ts
# ----------------------------
cat > src/web/app.config.ts <<'TS'
export default defineAppConfig({
  ui: {
    primary: 'cyan',
    gray: 'slate',
    strategy: 'override'
  }
})
TS

# ----------------------------
# app.vue
# ----------------------------
cat > src/web/app.vue <<'VUE'
<template><NuxtPage /></template>
VUE

# ----------------------------
# tailwind.config.ts
# ----------------------------
cat > src/web/tailwind.config.ts <<'TS'
import type { Config } from 'tailwindcss'

export default <Partial<Config>>{
  darkMode: 'class',
  content: [
    './components/**/*.{vue,js,ts}',
    './pages/**/*.{vue,js,ts}',
    './app.vue'
  ],
  theme: { extend: {} },
  plugins: []
}
TS

# ----------------------------
# assets/css/main.css
# ----------------------------
cat > src/web/assets/css/main.css <<'CSS'
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Blueprint-ish base */
:root {
  --jarvis-cyan: 0, 217, 255;
  --jarvis-blue: 0, 132, 255;
  --jarvis-dark: 5, 8, 16;
  --jarvis-mid: 10, 14, 26;
}

html, body, #__nuxt { height: 100%; }

body {
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Inter, Arial, "Apple Color Emoji", "Segoe UI Emoji";
  background: rgb(var(--jarvis-dark));
}

/* subtle scanlines */
.jarvis-scanlines::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: repeating-linear-gradient(
    to bottom,
    rgba(0, 217, 255, 0.03) 0px,
    rgba(0, 217, 255, 0.03) 1px,
    transparent 2px,
    transparent 6px
  );
  mix-blend-mode: overlay;
  opacity: .35;
}

/* glass + border */
.jarvis-glass {
  background: rgba(10, 14, 26, 0.55);
  border: 1px solid rgba(0, 217, 255, 0.14);
  backdrop-filter: blur(14px);
}

html:not(.dark) body {
  background: #f6fbff;
}

html:not(.dark) .jarvis-glass {
  background: rgba(255,255,255,0.70);
  border: 1px solid rgba(0, 120, 200, 0.14);
}
CSS

# ----------------------------
# components/JarvisBackdrop.vue  (octagons + particles)
# ----------------------------
cat > src/web/components/JarvisBackdrop.vue <<'VUE'
<template>
  <div class="fixed inset-0 -z-10 overflow-hidden">
    <!-- gradients -->
    <div class="absolute inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 dark:opacity-100 opacity-0"></div>
    <div class="absolute inset-0 bg-gradient-to-br from-white via-slate-50 to-slate-100 dark:opacity-0 opacity-100"></div>

    <!-- blueprint grid -->
    <div class="absolute inset-0 opacity-15 dark:opacity-10"
      :style="{
        backgroundImage:
          'linear-gradient(rgba(0,217,255,0.10) 1px, transparent 1px), linear-gradient(90deg, rgba(0,217,255,0.10) 1px, transparent 1px)',
        backgroundSize: '48px 48px'
      }"
    />

    <!-- canvas octagons/particles -->
    <canvas ref="cv" class="absolute inset-0"></canvas>

    <!-- scanlines overlay -->
    <div class="absolute inset-0 jarvis-scanlines"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, computed } from 'vue'

const cv = ref<HTMLCanvasElement | null>(null)
const colorMode = useColorMode()
const isDark = computed(() => colorMode.value === 'dark')

type P = { x:number; y:number; vx:number; vy:number; r:number; a:number }
type O = { x:number; y:number; s:number; rot:number; v:number; a:number }

let raf = 0
let ctx: CanvasRenderingContext2D | null = null
let w = 0, h = 0
let particles: P[] = []
let octs: O[] = []

function resize() {
  if (!cv.value) return
  const dpr = Math.max(1, window.devicePixelRatio || 1)
  w = cv.value.clientWidth
  h = cv.value.clientHeight
  cv.value.width = Math.floor(w * dpr)
  cv.value.height = Math.floor(h * dpr)
  ctx = cv.value.getContext('2d')
  if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
}

function rand(min:number, max:number){ return min + Math.random()*(max-min) }

function init() {
  particles = Array.from({ length: 80 }, () => ({
    x: rand(0,w), y: rand(0,h),
    vx: rand(-0.15,0.15), vy: rand(-0.15,0.15),
    r: rand(0.7,1.8), a: rand(0.15,0.55)
  }))
  octs = Array.from({ length: 18 }, () => ({
    x: rand(0,w), y: rand(0,h),
    s: rand(18,56), rot: rand(0, Math.PI),
    v: rand(-0.002,0.002), a: rand(0.06,0.18)
  }))
}

function drawOct(x:number,y:number,s:number,rot:number){
  if (!ctx) return
  ctx.beginPath()
  for (let i=0;i<8;i++){
    const ang = rot + (i*Math.PI)/4
    const px = x + Math.cos(ang)*s
    const py = y + Math.sin(ang)*s
    if (i===0) ctx.moveTo(px,py); else ctx.lineTo(px,py)
  }
  ctx.closePath()
}

function tick() {
  if (!ctx) return
  ctx.clearRect(0,0,w,h)

  const stroke = isDark.value ? 'rgba(0,217,255,0.22)' : 'rgba(0,120,200,0.16)'
  const dot = isDark.value ? 'rgba(0,217,255,0.55)' : 'rgba(0,120,200,0.40)'

  // octagons
  ctx.lineWidth = 1
  ctx.strokeStyle = stroke
  for (const o of octs) {
    o.rot += o.v
    o.y += 0.06
    if (o.y - o.s > h) { o.y = -o.s; o.x = rand(0,w) }
    drawOct(o.x,o.y,o.s,o.rot)
    ctx.stroke()
  }

  // particles
  for (const p of particles) {
    p.x += p.vx; p.y += p.vy
    if (p.x < -10) p.x = w+10
    if (p.x > w+10) p.x = -10
    if (p.y < -10) p.y = h+10
    if (p.y > h+10) p.y = -10
    ctx.fillStyle = dot.replace(/0\.55|0\.40/, String(p.a))
    ctx.beginPath()
    ctx.arc(p.x,p.y,p.r,0,Math.PI*2)
    ctx.fill()
  }

  raf = requestAnimationFrame(tick)
}

onMounted(() => {
  resize()
  init()
  tick()
  window.addEventListener('resize', () => { resize(); init() })
})

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  window.removeEventListener('resize', () => {})
})
</script>
VUE

# ----------------------------
# pages/index.vue
# ----------------------------
cat > src/web/pages/index.vue <<'VUE'
<template>
  <div class="relative min-h-screen">
    <JarvisBackdrop />

    <!-- mouse glow -->
    <div class="fixed pointer-events-none z-10 w-[520px] h-[520px] rounded-full transition-opacity duration-200"
      :style="{
        left: mx + 'px',
        top: my + 'px',
        transform: 'translate(-50%,-50%)',
        background: isDark
          ? 'radial-gradient(circle, rgba(0,217,255,0.18) 0%, transparent 70%)'
          : 'radial-gradient(circle, rgba(0,120,200,0.14) 0%, transparent 72%)',
        opacity: glow ? 1 : 0
      }"
    />

    <header class="sticky top-0 z-20 border-b border-slate-800/40 bg-slate-950/25 backdrop-blur-xl">
      <div class="mx-auto max-w-5xl px-4 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="relative">
            <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 grid place-items-center jarvis-glow">
              <span class="text-white font-black text-xl">J</span>
            </div>
            <div class="absolute -inset-1 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 opacity-25 blur-md"></div>
          </div>
          <div>
            <div class="text-xl font-extrabold bg-gradient-to-r from-cyan-300 to-blue-400 bg-clip-text text-transparent">JARVIS</div>
            <div class="text-xs text-slate-400">Local web UI</div>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <USelectMenu v-model="lang" :options="langs" class="w-44">
            <template #label>
              <div class="flex items-center gap-2">
                <UIcon name="i-heroicons-language" class="w-4 h-4" />
                <span class="text-sm">{{ lang.label }}</span>
              </div>
            </template>
          </USelectMenu>

          <USelectMenu v-model="theme" :options="themes" class="w-36">
            <template #label>
              <div class="flex items-center gap-2">
                <UIcon name="i-heroicons-adjustments-horizontal" class="w-4 h-4" />
                <span class="text-sm">{{ theme.label }}</span>
              </div>
            </template>
          </USelectMenu>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-5xl px-4 py-10">
      <div class="text-center mb-10">
        <h1 class="text-5xl md:text-6xl font-black tracking-tight">
          <span class="bg-gradient-to-r from-cyan-300 via-blue-400 to-cyan-300 bg-clip-text text-transparent">
            Engineering Console
          </span>
        </h1>
        <p class="mt-3 text-slate-300/90">Blueprint aesthetics • octagons • particles • tri-mode theme</p>
      </div>

      <div class="jarvis-glass rounded-2xl p-5 shadow-2xl shadow-cyan-900/10">
        <div ref="box" class="h-[520px] overflow-y-auto space-y-3 pr-2">
          <div v-for="(m,i) in msgs" :key="i" class="flex" :class="m.role==='user' ? 'justify-end' : 'justify-start'">
            <div class="max-w-[78%] rounded-2xl px-4 py-3 text-sm"
              :class="m.role==='user'
                ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white'
                : 'bg-slate-900/55 border border-slate-700/50 text-slate-100'">
              <div class="whitespace-pre-wrap">{{ m.content }}</div>
              <div class="text-[11px] opacity-60 mt-1">{{ fmt(m.ts) }}</div>
            </div>
          </div>

          <div v-if="sending" class="flex justify-start">
            <div class="bg-slate-900/55 border border-slate-700/50 rounded-2xl px-4 py-3 text-sm text-slate-300">
              Processing…
            </div>
          </div>
        </div>

        <div class="mt-4 flex gap-2">
          <UInput v-model="input" size="lg" class="flex-1"
            :disabled="sending"
            placeholder="Ask JARVIS…"
            @keydown.enter="send"
            :ui="{ base:'bg-slate-950/40 border-slate-700/50 focus:border-cyan-500' }"
          />
          <UButton size="lg" color="cyan" :disabled="sending || !input.trim()" :loading="sending" @click="send">
            Send
          </UButton>
        </div>

        <div class="mt-4 flex flex-wrap gap-2">
          <UButton v-for="a in quick" :key="a.q" size="xs" variant="soft" color="gray" @click="input=a.q">
            <UIcon :name="a.i" class="w-3 h-3 mr-1" /> {{ a.t }}
          </UButton>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const colorMode = useColorMode()

const themes = [
  { label: 'System', value: 'system' },
  { label: 'Dark', value: 'dark' },
  { label: 'Light', value: 'light' }
]
const theme = ref(themes[0])
watch(theme, () => { colorMode.preference = theme.value.value }, { immediate: true })

const isDark = computed(() => colorMode.value === 'dark')

const langs = [
  { label: 'English', value: 'en' },
  { label: 'Português (PT)', value: 'pt' },
  { label: 'Español', value: 'es' },
  { label: 'Français', value: 'fr' }
]
const lang = ref(langs[1])

const mx = ref(0), my = ref(0), glow = ref(false)
const onMove = (e: MouseEvent) => { mx.value = e.clientX; my.value = e.clientY; glow.value = true }
onMounted(() => document.addEventListener('mousemove', onMove))
onBeforeUnmount(() => document.removeEventListener('mousemove', onMove))

type Msg = { role:'user'|'assistant', content:string, ts: Date }
const msgs = ref<Msg[]>([
  { role:'assistant', content:"Sir, I am JARVIS. How may I assist you today?", ts: new Date() }
])
const input = ref('')
const sending = ref(false)
const box = ref<HTMLElement | null>(null)

const quick = [
  { t:'Time', q:'what time is it?', i:'i-heroicons-clock' },
  { t:'Weather', q:'weather in Lisbon', i:'i-heroicons-cloud' },
  { t:'Music', q:'play some music', i:'i-heroicons-musical-note' }
]

const fmt = (d: Date) =>
  new Intl.DateTimeFormat('en', { hour:'2-digit', minute:'2-digit' }).format(d)

const scrollBottom = async () => {
  await nextTick()
  if (box.value) box.value.scrollTop = box.value.scrollHeight
}

const send = async () => {
  const q = input.value.trim()
  if (!q || sending.value) return
  msgs.value.push({ role:'user', content:q, ts:new Date() })
  input.value = ''
  sending.value = true
  await scrollBottom()

  try {
    const r: any = await $fetch('/api/chat', { method:'POST', body:{ message:q, language: lang.value.value } })
    msgs.value.push({ role:'assistant', content: r?.ok ? r.response : `Error: ${r?.error || 'unknown'}`, ts:new Date() })
  } catch {
    msgs.value.push({ role:'assistant', content:'Backend offline. Start API on port 8000.', ts:new Date() })
  } finally {
    sending.value = false
    await scrollBottom()
  }
}
</script>
VUE

# ----------------------------
# server/api/chat.post.ts
# ----------------------------
cat > src/web/server/api/chat.post.ts <<'TS'
export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const { message, language = 'pt' } = body || {}

  if (!message) return { ok: false, error: 'No message provided' }

  try {
    return await $fetch('http://127.0.0.1:8000/api/chat', {
      method: 'POST',
      body: { message, language }
    })
  } catch {
    return { ok: false, error: 'Cannot connect to backend on http://127.0.0.1:8000' }
  }
})
TS

# ----------------------------
# Install deps
# ----------------------------
cd src/web
rm -rf node_modules .nuxt .output package-lock.json
npm cache verify
npm install

echo "OK: web rebuilt."
echo "Run:"
echo "  Terminal A: backend on 8000"
echo "  Terminal B: cd $ROOT/src/web && npm run dev"

