<template>
  <div class="step-guide-bar">
    <div class="sg-dots">
      <div
        v-for="(s, idx) in steps"
        :key="s.path"
        class="sg-dot"
        :class="{ current: idx === currentIdx, done: s.done && idx !== currentIdx }"
        @click="goTo(idx)"
      >
        <span class="sg-num">{{ s.done ? '✓' : idx + 1 }}</span>
        <span class="sg-name">{{ s.shortName }}</span>
      </div>
    </div>

    <div class="sg-btns">
      <button v-if="currentIdx > 0" class="sg-btn" @click="goPrev">◀ 上一步</button>
      <router-link v-else to="/" class="sg-btn">◀ 首页</router-link>

      <button class="sg-btn sg-skip" @click="goSkip">跳过</button>

      <button
        v-if="currentIdx < steps.length - 1"
        class="sg-btn sg-primary"
        @click="goNext"
      >下一步 ▶</button>
      <router-link v-else to="/report" class="sg-btn sg-primary">生成方案 ➔</router-link>
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
  { path: '/profile', shortName: '信息', done: store.profileDone },
  { path: '/lab', shortName: '体检', done: store.labsDone },
  { path: '/tongue', shortName: '舌诊', done: store.tongueDone },
  { path: '/questionnaire', shortName: '问诊', done: store.symptomsDone },
])

const currentIdx = computed(() => {
  const idx = steps.value.findIndex((s) => s.path === route.path)
  return idx >= 0 ? idx : 0
})

function goTo(idx) {
  router.push(steps.value[idx].path)
}
function goNext() {
  if (currentIdx.value < steps.value.length - 1) {
    router.push(steps.value[currentIdx.value + 1].path)
  }
}
function goPrev() {
  if (currentIdx.value > 0) {
    router.push(steps.value[currentIdx.value - 1].path)
  }
}
function goSkip() {
  if (currentIdx.value < steps.value.length - 1) {
    router.push(steps.value[currentIdx.value + 1].path)
  } else {
    router.push('/')
  }
}
</script>

<style scoped>
.step-guide-bar {
  position: fixed;
  bottom: 56px;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 680px;
  background: var(--card);
  border-top: 1px solid var(--line);
  box-shadow: 0 -2px 12px -6px rgba(0, 0, 0, 0.1);
  z-index: 50;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
}

/* 圆点组（紧凑，左侧） */
.sg-dots {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.sg-dot {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  gap: 1px;
}
.sg-num {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 9px;
  font-weight: 700;
  background: var(--bg);
  border: 1.5px solid var(--line);
  color: var(--ink-3);
  transition: all 0.2s ease;
}
.sg-dot.current .sg-num {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
}
.sg-dot.done .sg-num {
  background: var(--gold);
  border-color: var(--gold);
  color: #fff;
  font-size: 8px;
}
.sg-name {
  font-size: 8px;
  color: var(--ink-3);
  line-height: 1;
}
.sg-dot.current .sg-name {
  color: var(--primary);
  font-weight: 600;
}

/* 按钮组（右侧） */
.sg-btns {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  justify-content: flex-end;
}
.sg-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--card);
  color: var(--ink);
  font-size: 11px;
  font-family: inherit;
  cursor: pointer;
  white-space: nowrap;
  text-decoration: none;
  transition: all 0.15s ease;
}
.sg-btn:active { transform: scale(0.96); }
.sg-skip {
  border: none;
  background: none;
  color: var(--ink-3);
  padding: 5px 6px;
}
.sg-skip:hover { color: var(--ink); }
.sg-primary {
  border: none;
  color: #F7F2E7;
  background: linear-gradient(135deg, var(--primary), var(--primary-deep));
  box-shadow: 0 3px 8px -4px rgba(45, 95, 75, 0.5);
  padding: 5px 14px;
}
</style>
