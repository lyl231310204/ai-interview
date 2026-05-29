export interface SSEMessage {
  type: 'token' | 'scores' | 'done' | 'error'
  data: any
}

export const useSSE = () => {
  const isConnected = ref(false)
  const abortController = ref<AbortController | null>(null)

  const connect = async (
    url: string,
    body: any,
    onMessage: (message: SSEMessage) => void,
  ) => {
    const controller = new AbortController()
    abortController.value = controller
    isConnected.value = true

    try {
      const config = useRuntimeConfig()
      const response = await fetch(`${config.public.apiBase}${url}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
        body: JSON.stringify(body),
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('Response body is not readable')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed) continue

          for (const eventLine of trimmed.split('\n')) {
            const dataStr = eventLine.startsWith('data: ')
              ? eventLine.slice(6)
              : eventLine
            try {
              const parsed = JSON.parse(dataStr)
              if (parsed.type === 'token') {
                onMessage({ type: 'token', data: parsed })
              } else if (parsed.type === 'scores') {
                onMessage({ type: 'scores', data: parsed })
              } else if (parsed.type === 'done') {
                onMessage({ type: 'done', data: parsed })
              } else if (parsed.type === 'error') {
                onMessage({ type: 'error', data: parsed })
              } else {
                // 兼容纯文本 token
                onMessage({ type: 'token', data: { content: parsed.content || dataStr } })
              }
            } catch {
              // 非 JSON 数据，当作纯文本 token
              if (dataStr && dataStr !== '[DONE]') {
                onMessage({ type: 'token', data: { content: dataStr } })
              }
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        onMessage({ type: 'error', data: { message: err.message || '连接断开' } })
      }
    } finally {
      isConnected.value = false
    }
  }

  const disconnect = () => {
    abortController.value?.abort()
    abortController.value = null
    isConnected.value = false
  }

  return { connect, disconnect, isConnected }
}
