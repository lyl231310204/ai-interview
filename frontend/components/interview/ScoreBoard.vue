<template>
  <div class="score-panel" v-if="hasScores">
    <div class="score-header">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
      <span>实时评分</span>
    </div>
    <div class="score-bars">
      <div v-for="d in dims" :key="d.key" class="score-row">
        <span class="dim-label">{{ d.label }}</span>
        <div class="dim-bar-track">
          <div class="dim-bar-fill" :class="barColor(scores[d.key])" :style="{ width: `${(scores[d.key] || 0) * 10}%` }"></div>
        </div>
        <span class="dim-val" :class="textColor(scores[d.key])">{{ scores[d.key] || 0 }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ scores: Record<string, number> | null }>()

const dims = [
  { key: 'correctness', label: '正确性' },
  { key: 'depth', label: '深度' },
  { key: 'logic', label: '逻辑' },
  { key: 'practice', label: '实践' },
]

const hasScores = computed(() => {
  if (!props.scores) return false
  return Object.values(props.scores).some(v => typeof v === 'number' && v > 0)
})

const barColor = (s: number) => s >= 8 ? 'bg-emerald-500' : s >= 6 ? 'bg-amber-500' : 'bg-red-500'
const textColor = (s: number) => s >= 8 ? 'text-emerald-600' : s >= 6 ? 'text-amber-600' : 'text-red-600'
</script>

<style scoped>
.score-panel {
  background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 10px;
  padding: 10px 14px; min-width: 160px; animation: fadeSlideIn 0.3s ease;
}
.score-header {
  display: flex; align-items: center; gap: 5px;
  font-size: 11px; font-weight: 600; color: #92400E; margin-bottom: 8px;
}
.score-bars { display: flex; flex-direction: column; gap: 4px; }
.score-row { display: flex; align-items: center; gap: 6px; }
.dim-label { font-size: 10px; color: #6B7280; width: 28px; flex-shrink: 0; }
.dim-bar-track { flex: 1; height: 3px; background: #FDE68A; border-radius: 2px; overflow: hidden; }
.dim-bar-fill { height: 100%; border-radius: 2px; transition: width 0.6s ease; }
.dim-val { font-size: 10px; font-weight: 700; width: 18px; text-align: right; }
</style>
