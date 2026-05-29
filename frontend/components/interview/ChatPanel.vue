<template>
  <div class="flex flex-col h-full">
    <!-- 消息列表 -->
    <div class="flex-1 overflow-y-auto px-4 py-5" ref="scrollRef">
      <div class="max-w-2xl mx-auto flex flex-col gap-6">
        <MessageBubble
          v-for="(msg, idx) in messages"
          :key="msg.id"
          :message="msg"
          :index="idx"
          :streaming="false"
        />

        <!-- 流式输出中 -->
        <div v-if="streaming && streamText" class="flex gap-2.5 max-w-[72%] self-start animate-msg-in">
          <div class="w-8 h-8 rounded-lg bg-gray-100 border border-gray-100 flex items-center justify-center shrink-0 mt-0.5">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="1.6" stroke-linecap="round"><rect x="2" y="2" width="20" height="20" rx="5.5"/><circle cx="8.5" cy="10" r="1.5" fill="#6B7280"/><circle cx="15.5" cy="10" r="1.5" fill="#6B7280"/><path d="M8 16.5c1.8 2.2 5 2.6 7.5 1.3"/></svg>
          </div>
          <div>
            <div class="bg-gray-100 text-gray-800 rounded-bl-sm rounded-xl px-4 py-3 text-sm leading-relaxed">
              {{ streamText }}<span class="cursor-blink"></span>
            </div>
          </div>
        </div>

        <!-- 思考中 -->
        <div v-if="loading && !streaming" class="flex gap-2.5 max-w-[72%] self-start animate-msg-in">
          <div class="w-8 h-8 rounded-lg bg-gray-100 border border-gray-100 flex items-center justify-center shrink-0 mt-0.5">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="1.6" stroke-linecap="round"><rect x="2" y="2" width="20" height="20" rx="5.5"/><circle cx="8.5" cy="10" r="1.5" fill="#6B7280"/><circle cx="15.5" cy="10" r="1.5" fill="#6B7280"/><path d="M8 16.5c1.8 2.2 5 2.6 7.5 1.3"/></svg>
          </div>
          <div class="bg-gray-100 rounded-bl-sm rounded-xl px-4 py-3">
            <div class="thinking-dots"><span></span><span></span><span></span></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div v-if="canSend" class="border-t border-gray-100 bg-white px-4 py-3">
      <div class="max-w-2xl mx-auto flex items-end gap-2.5 bg-gray-100 border border-gray-200 rounded-xl py-2 pl-4 pr-2 transition-all duration-200 focus-within:border-indigo-500 focus-within:bg-white focus-within:shadow-sm">
        <textarea
          ref="inputRef"
          v-model="inputText"
          :placeholder="placeholder"
          :disabled="disabled"
          rows="1"
          class="flex-1 border-none bg-transparent text-base leading-relaxed resize-none outline-none py-1.5 text-gray-900 placeholder-gray-400 disabled:opacity-40"
          style="max-height:80px;font-family:inherit;letter-spacing:-0.005em"
          @keydown="handleKey"
          @input="autoResize"
        ></textarea>
        <button
          :disabled="!inputText.trim() || disabled"
          class="w-10 h-10 shrink-0 rounded-lg flex items-center justify-center transition-all duration-200"
          :class="inputText.trim() && !disabled ? 'bg-indigo-500 text-white shadow-md hover:scale-105 hover:bg-indigo-600 active:scale-95' : 'bg-gray-200 text-gray-400 cursor-not-allowed'"
          @click="send"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>
      <div class="max-w-2xl mx-auto mt-2 text-xs text-gray-300 text-center">
        <kbd class="inline-block px-1.5 py-0.5 rounded-sm border border-gray-200 bg-gray-100 text-xs text-gray-400 font-sans">Enter</kbd> 发送 ·
        <kbd class="inline-block px-1.5 py-0.5 rounded-sm border border-gray-200 bg-gray-100 text-xs text-gray-400 font-sans">Shift</kbd> +
        <kbd class="inline-block px-1.5 py-0.5 rounded-sm border border-gray-200 bg-gray-100 text-xs text-gray-400 font-sans">Enter</kbd> 换行
      </div>
    </div>

    <!-- 结束状态 -->
    <div v-if="!canSend && !loading" class="border-t border-gray-100 bg-white p-8 text-center">
      <div class="text-3xl mb-3">🎉</div>
      <p class="text-gray-500 font-medium">面试已结束</p>
      <p class="text-gray-400 text-sm mt-1">评估报告已生成</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import MessageBubble from './MessageBubble.vue'

interface Message {
  id: number
  role: string
  content: string
  scores?: any
  created_at?: string
}

const props = withDefaults(defineProps<{
  messages: Message[]
  loading?: boolean
  streaming?: boolean
  streamText?: string
  canSend?: boolean
  disabled?: boolean
  placeholder?: string
}>(), {
  placeholder: '输入你的回答…',
})

const emit = defineEmits<{ send: [content: string] }>()

const inputText = ref('')
const inputRef = ref<HTMLTextAreaElement>()
const scrollRef = ref<HTMLElement>()

const send = () => {
  const text = inputText.value.trim()
  if (!text || props.disabled) return
  emit('send', text)
  inputText.value = ''
  nextTick(() => { if (inputRef.value) inputRef.value.style.height = 'auto' })
}

const autoResize = () => {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 80) + 'px'
}

const handleKey = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTo({ top: scrollRef.value.scrollHeight, behavior: 'smooth' })
    }
  })
}

watch(() => props.messages.length, scrollToBottom)
watch(() => props.streamText, scrollToBottom)
onMounted(() => { setTimeout(scrollToBottom, 300) })
</script>
