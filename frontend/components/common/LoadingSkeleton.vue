<template>
  <div class="skeleton-wrap">
    <div v-for="i in rows" :key="i" class="skeleton-row" :style="{ width: `${60 + Math.random() * 40}%` }">
      <div class="skeleton-bar animate-shimmer"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ rows?: number }>(), { rows: 5 })
</script>

<style scoped>
.skeleton-wrap { display:flex;flex-direction:column;gap:12px;padding:20px }
.skeleton-row { height:16px;border-radius:4px;overflow:hidden }
.skeleton-bar { height:100%;background:linear-gradient(90deg,#F0F0F3 25%,#E8E8ED 50%,#F0F0F3 75%);background-size:200% 100%;animation:shimmer 1.5s ease-in-out infinite }
@keyframes shimmer { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
</style>
