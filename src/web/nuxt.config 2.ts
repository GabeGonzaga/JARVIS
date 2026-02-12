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
