export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const { message, language = 'pt' } = body

  if (!message) return { ok: false, error: 'No message' }

  try {
    return await $fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      body: { message, language }
    })
  } catch {
    return { ok: false, error: 'Backend offline' }
  }
})
