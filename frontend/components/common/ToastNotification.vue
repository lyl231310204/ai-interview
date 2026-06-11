<template>
  <Teleport to="body">
    <div v-if="visible" class="toast" :class="type" @click="visible = false">
      <span class="toast-icon">{{ icon }}</span>
      <span>{{ message }}</span>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{ message: string; type?: string; duration?: number }>(), { type: 'info', duration: 3000 })
const visible = ref(true)
const icon = computed(() => ({ success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' } as any)[props.type] || 'ℹ️')
if (props.duration > 0) { setTimeout(() => { visible.value = false }, props.duration) }
</script>

<style scoped>
.toast { position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:10px;font-size:14px;font-weight:500;cursor:pointer;z-index:9999;display:flex;align-items:center;gap:8px;box-shadow:0 8px 24px rgba(0,0,0,0.12);animation:slideUp 0.3s ease;max-width:400px }
.toast.success { background:#ECFDF5;color:#065F46;border:1px solid #A7F3D0 }
.toast.error { background:#FEF2F2;color:#991B1B;border:1px solid #FECACA }
.toast.info { background:#EFF6FF;color:#1E40AF;border:1px solid #BFDBFE }
.toast.warning { background:#FFFBEB;color:#92400E;border:1px solid #FDE68A }
.toast-icon { font-size:16px }
@keyframes slideUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
</style>
