<template>
  <div class="msg-row" :class="isUser ? 'msg-user' : 'msg-ai'" :style="{ animationDelay: `${index * 0.03}s` }">
    <!-- Avatar -->
    <div class="msg-avatar" :class="isUser ? 'avatar-user' : 'avatar-ai'">
      <svg v-if="!isUser" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <rect x="2" y="2" width="20" height="20" rx="5.5"/><circle cx="8.5" cy="10" r="1.5" fill="#6B7280"/><circle cx="15.5" cy="10" r="1.5" fill="#6B7280"/><path d="M8 16.5c1.8 2.2 5 2.6 7.5 1.3"/>
      </svg>
      <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#FFF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="8" r="4.5"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/>
      </svg>
    </div>

    <!-- Body -->
    <div class="msg-body">
      <div class="bubble" :class="isUser ? 'bubble-user' : 'bubble-ai'">
        <span class="whitespace-pre-wrap">{{ message.content }}</span>
        <span v-if="streaming" class="cursor-blink"></span>
      </div>

      <!-- Score pill (AI messages with scores) -->
      <div v-if="!isUser && message.scores && !streaming" class="score-inline">
        <div class="score-grid">
          <div v-for="d in scoreDims" :key="d.key" class="score-item">
            <span class="score-label">{{ d.label }}</span>
            <div class="score-bar-wrap">
              <div class="score-bar-fill" :class="scoreColor(message.scores[d.key])" :style="{ width: `${(message.scores[d.key] || 0) * 10}%` }"></div>
            </div>
            <span class="score-val" :class="scoreTextColor(message.scores[d.key])">{{ message.scores[d.key] || 0 }}</span>
          </div>
        </div>
        <p v-if="message.scores.comment" class="score-comment">{{ message.scores.comment }}</p>
      </div>

      <!-- Time -->
      <div class="msg-meta" :class="isUser ? 'meta-right' : ''">
        <span class="msg-time">{{ formatTime(message.created_at) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Message {
  id: number
  role: string
  content: string
  scores?: Record<string, any> | null
  created_at?: string
}

const props = defineProps<{
  message: Message
  streaming?: boolean
  index?: number
}>()

const isUser = computed(() => {
  const r = props.message.role
  return r === 'candidate' || r === 'CANDIDATE' || r === 'user'
})

const scoreDims = [
  { key: 'correctness', label: '正确性' },
  { key: 'depth', label: '深度' },
  { key: 'logic', label: '逻辑' },
  { key: 'practice', label: '实践' },
]

const scoreColor = (s: number) => s >= 8 ? 'bar-green' : s >= 6 ? 'bar-amber' : 'bar-red'
const scoreTextColor = (s: number) => s >= 8 ? 'text-emerald-600' : s >= 6 ? 'text-amber-600' : 'text-red-600'

const formatTime = (iso?: string) => {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.msg-row {
  display: flex; gap: 10px; max-width: 72%;
  animation: msgPopIn 0.4s var(--ease-spring) both;
}
.msg-ai { align-self: flex-start; }
.msg-user { align-self: flex-end; flex-direction: row-reverse; }

.msg-avatar {
  width: 34px; height: 34px; border-radius: 10px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; margin-top: 1px;
}
.avatar-ai { background: #F3F4F6; border: 1px solid #F0F0F3; }
.avatar-user {
  background: linear-gradient(135deg, #5C5CEA, #7C3AED);
  box-shadow: 0 4px 12px rgba(92,92,234,0.3);
}

.msg-body { min-width: 0; }
.bubble {
  padding: 12px 16px; font-size: 14px; line-height: 1.6;
  word-break: break-word; position: relative;
}
.bubble-ai {
  background: #F3F4F6; color: #1F2937;
  border-radius: 3px 16px 16px 16px;
}
.bubble-user {
  background: #5C5CEA; color: #FFF;
  border-radius: 16px 3px 16px 16px;
}

/* Score inline */
.score-inline {
  margin-top: 8px; padding: 10px 12px;
  background: #FFFBEB; border: 1px solid #FDE68A;
  border-radius: 10px;
}
.score-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 12px; }
.score-item { display: flex; align-items: center; gap: 6px; }
.score-label { font-size: 11px; color: #6B7280; min-width: 32px; }
.score-bar-wrap { flex: 1; height: 4px; background: #E5E7EB; border-radius: 2px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 2px; transition: width 0.6s var(--ease-out); }
.bar-green { background: #10B981; }
.bar-amber { background: #F59E0B; }
.bar-red { background: #EF4444; }
.score-val { font-size: 11px; font-weight: 600; min-width: 18px; text-align: right; }
.score-comment { font-size: 11px; color: #6B7280; margin-top: 6px; padding-top: 6px; border-top: 1px solid #FDE68A; font-style: italic; }

.msg-meta { display: flex; align-items: center; gap: 6px; margin-top: 4px; padding: 0 6px; }
.meta-right { justify-content: flex-end; }
.msg-time { font-size: 10px; color: #D1D5DB; }
</style>
