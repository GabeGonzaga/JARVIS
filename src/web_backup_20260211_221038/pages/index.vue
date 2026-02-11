<template>
  <div class="relative min-h-screen overflow-hidden bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-950">
    
    <!-- Animated Background Gradients -->
    <div class="fixed inset-0 opacity-30">
      <div class="absolute top-0 left-1/4 w-96 h-96 bg-blue-500 rounded-full mix-blend-screen filter blur-3xl animate-pulse-glow"></div>
      <div class="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-500 rounded-full mix-blend-screen filter blur-3xl animate-pulse-glow" style="animation-delay: 2s"></div>
      <div class="absolute bottom-1/4 left-1/3 w-96 h-96 bg-cyan-500 rounded-full mix-blend-screen filter blur-3xl animate-pulse-glow" style="animation-delay: 4s"></div>
    </div>

    <!-- Canvas for particles -->
    <canvas ref="canvas" class="fixed inset-0 pointer-events-none"></canvas>

    <!-- Interactive Glow Effect -->
    <div 
      ref="glowEffect"
      class="fixed pointer-events-none w-96 h-96 rounded-full"
      :style="{
        left: mouse.x + 'px',
        top: mouse.y + 'px',
        transform: 'translate(-50%, -50%)',
        background: 'radial-gradient(circle, rgba(96, 165, 250, 0.3) 0%, rgba(139, 92, 246, 0.2) 40%, transparent 70%)',
        filter: 'blur(40px)',
        opacity: mouseActive ? 0.8 : 0,
        transition: 'opacity 0.3s ease'
      }"
    ></div>

    <!-- Main Content -->
    <div class="relative z-10 min-h-screen flex flex-col">
      
      <!-- Header -->
      <header class="border-b border-white/5 backdrop-blur-xl bg-slate-950/20">
        <div class="container mx-auto px-6 py-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="relative">
                <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500 p-0.5">
                  <div class="w-full h-full rounded-2xl bg-slate-950 flex items-center justify-center">
                    <span class="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">J</span>
                  </div>
                </div>
              </div>
              <div>
                <h1 class="text-xl font-bold text-white">J.A.R.V.I.S.</h1>
                <p class="text-xs text-slate-400">Just A Rather Very Intelligent System</p>
              </div>
            </div>

            <div class="flex items-center gap-3">
              <USelectMenu v-model="selectedLang" :options="languages" size="sm">
                <template #label>
                  <span class="text-sm text-slate-300">{{ selectedLang.label }}</span>
                </template>
              </USelectMenu>
            </div>
          </div>
        </div>
      </header>

      <!-- Main Content Area -->
      <div class="flex-1 flex items-center justify-center px-6 py-12">
        <div class="max-w-4xl w-full">
          
          <!-- Central JARVIS Logo -->
          <div class="flex justify-center mb-16">
            <div class="relative">
              <!-- Outer rotating ring -->
              <div class="absolute -inset-8">
                <div class="w-full h-full border-2 border-dashed border-blue-400/20 rounded-full" style="animation: rotate-slow 30s linear infinite"></div>
              </div>
              
              <!-- Middle glow ring -->
              <div class="absolute -inset-4">
                <div class="w-full h-full bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-cyan-500/20 rounded-full blur-xl"></div>
              </div>
              
              <!-- Central orb -->
              <div class="relative w-40 h-40 rounded-full bg-gradient-to-br from-blue-500 via-purple-600 to-cyan-500 p-1">
                <div class="w-full h-full rounded-full bg-slate-950 flex items-center justify-center">
                  <div class="text-center">
                    <div class="text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent mb-1">
                      J
                    </div>
                    <div class="text-xs text-blue-300 font-medium tracking-wider">ONLINE</div>
                  </div>
                </div>
              </div>

              <!-- Animated particles around logo -->
              <div v-for="i in 8" :key="i" 
                   class="absolute w-2 h-2 bg-blue-400 rounded-full"
                   :style="{
                     top: '50%',
                     left: '50%',
                     animation: `float ${3 + i * 0.5}s ease-in-out infinite`,
                     animationDelay: `${i * 0.2}s`,
                     transform: `rotate(${i * 45}deg) translateX(100px)`
                   }"></div>
            </div>
          </div>

          <!-- Title -->
          <div class="text-center mb-12">
            <h2 class="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">
              Advanced AI Assistant
            </h2>
            <p class="text-lg text-slate-300 max-w-2xl mx-auto">
              Powered by intelligent systems and fluid interactions
            </p>
          </div>

          <!-- Glass Card Interface -->
          <div class="glass-card rounded-3xl p-8 mb-8">
            <!-- Input Area -->
            <div class="mb-6">
              <div class="flex gap-3">
                <div class="flex-1 relative">
                  <input
                    v-model="userInput"
                    @keypress.enter="processCommand"
                    :disabled="isProcessing"
                    placeholder="Enter your command..."
                    class="w-full px-6 py-4 bg-slate-900/50 border border-slate-700/50 rounded-2xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500/50 transition-all"
                  />
                  <div class="absolute right-4 top-1/2 -translate-y-1/2">
                    <div class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
                  </div>
                </div>
                <button
                  @click="processCommand"
                  :disabled="!userInput.trim() || isProcessing"
                  class="px-8 py-4 bg-gradient-to-r from-blue-500 via-purple-500 to-cyan-500 rounded-2xl text-white font-semibold hover:shadow-lg hover:shadow-blue-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {{ isProcessing ? 'Processing...' : 'Execute' }}
                </button>
              </div>
            </div>

            <!-- Response Area -->
            <div v-if="responses.length > 0" class="space-y-3 max-h-64 overflow-y-auto">
              <TransitionGroup name="fade">
                <div v-for="(resp, idx) in responses" :key="idx" 
                     class="p-4 bg-slate-900/30 border border-slate-700/30 rounded-xl">
                  <div class="flex items-start gap-3">
                    <div class="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-sm font-bold text-white">
                      J
                    </div>
                    <div class="flex-1">
                      <div class="text-xs text-slate-500 mb-1">{{ formatTime(resp.timestamp) }}</div>
                      <div class="text-sm text-slate-200 font-mono whitespace-pre-wrap">{{ resp.content }}</div>
                    </div>
                  </div>
                </div>
              </TransitionGroup>
            </div>
          </div>

          <!-- Feature Cards -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div v-for="feature in features" :key="feature.title"
                 class="glass-card rounded-2xl p-6 hover:border-blue-500/30 transition-all group">
              <div class="text-center">
                <div class="w-12 h-12 mx-auto mb-4 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <span class="text-2xl">{{ feature.icon }}</span>
                </div>
                <h3 class="text-lg font-semibold text-white mb-2">{{ feature.title }}</h3>
                <p class="text-sm text-slate-400">{{ feature.description }}</p>
              </div>
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
const mouse = ref({ x: 0, y: 0 })
const mouseActive = ref(false)

// Particle system
const canvas = ref(null)
let ctx = null
let particles = []
let animationFrame = null

class Particle {
  constructor(canvasWidth, canvasHeight) {
    this.x = Math.random() * canvasWidth
    this.y = Math.random() * canvasHeight
    this.size = Math.random() * 3 + 1
    this.speedX = Math.random() * 1 - 0.5
    this.speedY = Math.random() * 1 - 0.5
    this.color = `hsla(${Math.random() * 60 + 200}, 70%, 60%, ${Math.random() * 0.5 + 0.3})`
  }

  update(canvasWidth, canvasHeight, mouseX, mouseY) {
    // Mouse interaction
    const dx = mouseX - this.x
    const dy = mouseY - this.y
    const distance = Math.sqrt(dx * dx + dy * dy)
    
    if (distance < 150) {
      const force = (150 - distance) / 150
      this.x -= (dx / distance) * force * 5
      this.y -= (dy / distance) * force * 5
    }

    this.x += this.speedX
    this.y += this.speedY

    if (this.x < 0 || this.x > canvasWidth) this.speedX *= -1
    if (this.y < 0 || this.y > canvasHeight) this.speedY *= -1
  }

  draw(ctx) {
    ctx.fillStyle = this.color
    ctx.beginPath()
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
    ctx.fill()
    
    // Glow effect
    ctx.shadowBlur = 10
    ctx.shadowColor = this.color
  }
}

onMounted(() => {
  // Setup canvas
  const canvasEl = canvas.value
  ctx = canvasEl.getContext('2d')
  canvasEl.width = window.innerWidth
  canvasEl.height = window.innerHeight

  // Create particles
  for (let i = 0; i < 100; i++) {
    particles.push(new Particle(canvasEl.width, canvasEl.height))
  }

  // Animation loop
  const animate = () => {
    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height)
    
    particles.forEach(particle => {
      particle.update(canvasEl.width, canvasEl.height, mouse.value.x, mouse.value.y)
      particle.draw(ctx)
    })

    // Draw connections
    particles.forEach((p1, i) => {
      particles.slice(i + 1).forEach(p2 => {
        const dx = p1.x - p2.x
        const dy = p1.y - p2.y
        const distance = Math.sqrt(dx * dx + dy * dy)
        
        if (distance < 120) {
          ctx.strokeStyle = `rgba(96, 165, 250, ${0.2 * (1 - distance / 120)})`
          ctx.lineWidth = 0.5
          ctx.beginPath()
          ctx.moveTo(p1.x, p1.y)
          ctx.lineTo(p2.x, p2.y)
          ctx.stroke()
        }
      })
    })

    animationFrame = requestAnimationFrame(animate)
  }
  animate()

  // Mouse tracking
  const handleMouseMove = (e) => {
    mouse.value = { x: e.clientX, y: e.clientY }
    mouseActive.value = true
  }

  const handleResize = () => {
    canvasEl.width = window.innerWidth
    canvasEl.height = window.innerHeight
  }

  document.addEventListener('mousemove', handleMouseMove)
  window.addEventListener('resize', handleResize)

  onBeforeUnmount(() => {
    document.removeEventListener('mousemove', handleMouseMove)
    window.removeEventListener('resize', handleResize)
    if (animationFrame) cancelAnimationFrame(animationFrame)
  })
})

// Language
const languages = [
  { label: 'English', value: 'en' },
  { label: 'Português', value: 'pt' },
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

    if (responses.value.length > 5) responses.value.pop()
  } catch (error) {
    responses.value.unshift({
      content: 'Connection error. Start backend: python -m uvicorn jarvis.apps.web_api:app --port 8000',
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

const features = [
  { icon: '🌐', title: 'Multi-Language', description: 'EN • PT • ES • FR support' },
  { icon: '⚡', title: 'Real-Time', description: 'Instant AI responses' },
  { icon: '🔒', title: 'Secure', description: 'Local processing' }
]
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
