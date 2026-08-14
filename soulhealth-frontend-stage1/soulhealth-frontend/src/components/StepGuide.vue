<template>
  <div class="step-guide">
    <div class="sg-row">
      <button v-if="currentIdx > 0" class="sg-link" @click="goPrev">◀ {{ prevName }}</button>
      <router-link v-else to="/" class="sg-link">◀ 返回首页</router-link>

      <div class="sg-dots">
        <span
          v-for="(s, idx) in steps"
          :key="s.path"
          class="sg-dot"
          :class="{ current: idx === currentIdx, done: s.done && idx !== currentIdx }"
          @click="goTo(idx)"
        ></span>
      </div>

      <button v-if="currentIdx < steps.length - 1" class="sg-link sg-next" @click="goNext">{{ nextName }} ▶</button>
      <router-link v-else to="/report" class="sg-link sg-next">生成方案 ➔</router-link>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usePatientStore } from '../store/patient'

const router = useRouter()
const route = useRoute()
const store = usePatientStore()

const steps = computed(() => [
  { path: '/profile', name: '基础信息', done: store.profileDone },
  { path: '/lab', name: '体检录入', done: store.labsDone },
  { path: '/tongue', name: '舌面诊', done: store.tongueDone },
  { path: '/questionnaire', name: '症状问诊', done: store.symptomsDone },
])

const currentIdx = computed(() => {
  const idx = steps.value.findIndex((s) => s.path === route.path)
  return idx >= 0 ? idx : 0
})

const prevName = computed(() => currentIdx.value > 0 ? steps.value[currentIdx.value - 1].name : '')
const nextName = computed(() => currentIdx.value < steps.value.length - 1 ? steps.value[currentIdx.value + 1].name : '')

function goTo(idx) { router.push(steps.value[idx].path) }
function goNext() { if (currentIdx.value < steps.value.length - 1) router.push(steps.value[currentIdx.value + 1].path) }
function goPrev() { if (currentIdx.value > 0) router.push(steps.value[currentIdx.value - 1].path) }
</script>

<style scoped>
.step-guide {
  margin: 24px 0 16px;
  padding: 12px 0;
  border-top: 1px dashed var(--line);
}
.sg-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sg-link {
  background: none;
  border: none;
  color: var(--ink-2);
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  padding: 4px 0;
  transition: color 0.2s;
  text-decoration: none;
  white-space: nowrap;
}
.sg-link:hover { color: var(--primary); }
.sg-next { color: var(--primary); font-weight: 600; }

.sg-dots {
  display: flex;
  align-items: center;
  gap: 6px;
}
.sg-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--line);
  cursor: pointer;
  transition: all 0.2s ease;
}
.sg-dot.current {
  background: var(--primary);
  transform: scale(1.3);
}
.sg-dot.done {
  background: var(--gold);
}
</style>
