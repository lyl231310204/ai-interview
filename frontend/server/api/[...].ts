export default defineEventHandler(async (event) => {
  const target = 'http://localhost:8000/api' + event.path.replace('/api', '')
  const body = event.method !== 'GET' ? await readRawBody(event) : undefined

  try {
    const response = await fetch(target, {
      method: event.method,
      headers: {
        'Content-Type': event.headers.get('content-type') || 'application/json',
        Accept: event.headers.get('accept') || 'application/json',
      },
      body,
    })

    const contentType = response.headers.get('content-type') || ''
    const data = contentType.includes('application/json')
      ? await response.json()
      : await response.text()

    setResponseStatus(event, response.status)
    setResponseHeaders(event, Object.fromEntries(response.headers.entries()))
    return data
  } catch (e) {
    setResponseStatus(event, 502)
    return { detail: 'Backend unavailable' }
  }
})
