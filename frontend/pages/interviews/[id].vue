<template>
  <div class="flex flex-col h-full bg-white">
    <!-- Header -->
    <header class="flex items-center justify-between px-5 py-3.5 border-b border-gray-100 shrink-0 bg-white">
      <div class="flex items-center gap-3.5">
        <div class="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm animate-pulse"></div>
        <div>
          <span class="text-sm font-semibold text-gray-900">AI 技术面试</span>
          <span class="text-xs text-gray-400 ml-2">{{ progressText }}</span>
        </div>
        <span v-if="currentTopic" class="px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-500">{{ currentTopic }}</span>
      </div>
      <div class="flex items-center gap-3">
        <ScoreBoard v-if="latestScores" :scores="latestScores" />
        <button
          v-if="!isCompleted"
          @click="endInterview"
          :disabled="loading"
          class="text-sm text-gray-500 hover:text-red-500 hover:bg-red-50 px-3 py-1.5 rounded-lg transition-colors font-medium disabled:opacity-30"
        >结束面试</button>
      </div>
    </header>

    <!-- Chat -->
    <ChatPanel
      :messages="chatMessages"
      :loading="loading"
      :streaming="streaming"
      :streamText="streamText"
      :canSend="!isCompleted"
      :disabled="loading"
      placeholder="输入你的回答…"
      @send="sendMessage"
    />
  </div>
</template>

<script setup lang="ts">
import ChatPanel from '~/components/interview/ChatPanel.vue'
import ScoreBoard from '~/components/interview/ScoreBoard.vue'

const route = useRoute()
const { $api } = useNuxtApp()
const { connect, disconnect } = useSSE()

const interviewId = computed(() => Number(route.params.id))

const chatMessages = ref<any[]>([])
const loading = ref(false)
const streaming = ref(false)
const streamText = ref('')
const interviewStatus = ref('')
const latestScores = ref<any>(null)
const currentTopic = ref('')

const isCompleted = computed(() =>
  interviewStatus.value === 'COMPLETED' || interviewStatus.value === 'completed'
)
const progressText = computed(() => {
  const aiMsgs = chatMessages.value.filter(m => m.role === 'INTERVIEWER' || m.role === 'interviewer')
  return `第 ${aiMsgs.length} 题`
})

const sendMessage = async (content: string) => {
  chatMessages.value.push({
    id: Date.now(), role: 'CANDIDATE', content,
    created_at: new Date().toISOString(),
  })

  loading.value = true
  streaming.value = true
  streamText.value = ''
  let fullResponse = ''
  let msgScores: any = null
  let msgId = 0
  let questionNumber = 0

  try {
    // 使用 SSE 流式接口
    const config = useRuntimeConfig()
    const res = await fetch(`${config.public.apiBase}/interviews/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ interview_id: interviewId.value, message: content }),
    })

    const reader = res.body?.getReader()
    if (!reader) throw new Error('No stream')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        const line = part.trim()
        if (!line) continue

        const dataStr = line.startsWith('data: ') ? line.slice(6) : line
        if (dataStr === '[DONE]') continue

        try {
          const parsed = JSON.parse(dataStr)
          if (parsed.type === 'token') {
            fullResponse += parsed.content || ''
            streamText.value = fullResponse
          } else if (parsed.type === 'scores') {
            if (parsed.scores) {
              msgScores = parsed.scores
              latestScores.value = parsed.scores
            }
            if (parsed.question_number) questionNumber = parsed.question_number
          } else if (parsed.type === 'done') {
            msgId = parsed.message_id || Date.now()
            if (parsed.content) fullResponse = parsed.content
            if (parsed.question_number) questionNumber = parsed.question_number
          } else if (parsed.type === 'error') {
            console.error('SSE error:', parsed.message)
          }
        } catch { /* skip unparseable chunks */ }
      }
    }
  } catch (e: any) {
    // 回退到非流式接口
    console.warn('SSE failed, falling back:', e.message)
    try {
      const fallback = await $api.post('/interviews/chat', {
        interview_id: interviewId.value, message: content,
      })
      const data = fallback.data.data
      fullResponse = data.assistant_response || ''
      msgScores = data.scores
      msgId = data.message_id
      streamText.value = fullResponse
    } catch (e2) {
      console.error('Chat failed:', e2)
    }
  } finally {
    streaming.value = false
    loading.value = false
  }

  if (fullResponse) {
    chatMessages.value.push({
      id: msgId || Date.now() + 1,
      role: 'INTERVIEWER', content: fullResponse,
      scores: msgScores,
      created_at: new Date().toISOString(),
    })
    if (msgScores) latestScores.value = msgScores
    interviewStatus.value = 'IN_PROGRESS'
  }

  streamText.value = ''
}

const endInterview = async () => {
  if (!confirm('确定要结束本次面试吗？AI 将生成评估报告。')) return
  try {
    await $api.post(`/interviews/${interviewId.value}/end`)
    interviewStatus.value = 'COMPLETED'
    await navigateTo('/interviews')
  } catch (e: any) {
    alert('结束失败：' + (e?.response?.data?.detail || '请重试'))
  }
}

const loadInterview = async () => {
  try {
    const [intRes, msgRes] = await Promise.all([
      $api.get(`/interviews/${interviewId.value}`),
      $api.get(`/interviews/${interviewId.value}/messages`),
    ])
    interviewStatus.value = intRes.data.data.status || ''
    chatMessages.value = (msgRes.data.data || []).map((m: any) => ({
      ...m,
      role: m.role === 'CANDIDATE' || m.role === 'INTERVIEWER' ? m.role : m.role.toUpperCase(),
    }))

    // 恢复最新评分
    for (let i = chatMessages.value.length - 1; i >= 0; i--) {
      if (chatMessages.value[i].scores) {
        latestScores.value = chatMessages.value[i].scores
        break
      }
    }

    // 恢复当前题号 topic
    const aiMsgs = chatMessages.value.filter((m: any) => m.role === 'INTERVIEWER')
    if (aiMsgs.length && aiMsgs[aiMsgs.length - 1].scores?.topic) {
      currentTopic.value = aiMsgs[aiMsgs.length - 1].scores.topic
    }
  } catch (e) {
    console.error('加载面试失败:', e)
  }
}

onMounted(loadInterview)
onUnmounted(disconnect)
</script>
