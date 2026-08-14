<template>
  <div class="step-guide-bar">
    <div class="guide-progress">
      <div
        v-for="(s, idx) in steps"
        :key="s.path"
        class="guide-dot"
        :class="{
          current: idx === currentIdx,
          done: s.done,
          future: idx > currentIdx && !s.done,
        }"
        @click="goTo(idx)"
      >
        <span class="gdot-inner">{{ s.done ? '✓' : idx + 1 }}</span>
        <span class="gdot-label">{{ s.shortName }}</span>
      </div>
    </div>

    <div class="guide-actions">
      <button v-if="currentIdx > 0" class="btn btn-back" @click="goPrev">
        ◀ 上一步
      </button>
      <router-link v-else to="/" class="btn btn-back">◀ 首页</router-link>

      <button class="btn btn-skip" @click="goSkip">跳过</button>

      <button
        v-if="currentIdx < steps.length - 1"
        class="btn btn-primary btn-next"
        @click="goNext"
      >
        下一步 ▶
      </button>
      <router-link
        v-else
        to="/report"
        class="btn btn-primary btn-next"
      >
        完成，生成方案 ➔
      </router-link>
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
  box-shadow: 0 -4px 20px -10px rgba(0, 0, 0, 0.12);
  z-index: 50;
  padding: 0 16px;
}

/* 顶部小圆点进度 */
.guide-progress {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 28px;
  padding: 10px 0 4px;
}
.guide-dot {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  position: relative;
}
.gdot-inner {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
  background: var(--bg);
  border: 2px solid var(--line);
  color: var(--ink-3);
  transition: all 0.25s ease;
}
.guide-dot.current .gdot-inner {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
  transform: scale(1.12);
  box-shadow: 0 2px 8px -2px rgba(45, 95, 75, 0.5);
}
.guide-dot.done .gdot-inner {
  background: var(--gold);
  border-color: var(--gold);
  color: #fff;
}
.gdot-label {
  font-size: 10px;
  color: var(--ink-3);
  margin-top: 2px;
}
.guide-dot.current .gdot-label {
  color: var(--primary);
  font-weight: 600;
}

/* 下方按钮行 */
.guide-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0 12px;
}
.btn-back {
  flex: 0 0 auto;
}
.btn-skip {
  flex: 0 0 auto;
  background: none;
  border: none;
  color: var(--ink-3);
  font-size: 13px;
  cursor: pointer;
  padding: 8px 12px;
  transition: color 0.2s;
}
.btn-skip:hover {
  color: var(--ink);
}
.btn-next {
  flex: 1;
  text-align: center;
}
</style>
