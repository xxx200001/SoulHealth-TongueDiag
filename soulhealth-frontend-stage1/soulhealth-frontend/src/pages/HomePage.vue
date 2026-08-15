<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePatientStore } from '../store/patient'

const router = useRouter()
const store = usePatientStore()
const showFollowup = ref(true)

// 动态计算距上次调理天数
const daysSinceLastVisit = computed(() => {
  if (!store.history || store.history.length === 0) return -1
  const lastDate = new Date(store.history[0].date)
  if (isNaN(lastDate.getTime())) return -1
  const now = new Date()
  return Math.floor((now - lastDate) / (1000 * 60 * 60 * 24))
})
const shouldShowFollowup = computed(() => showFollowup.value && daysSinceLastVisit.value >= 0)

// ── 方案生成进度 ──
const steps = computed(() => [
  { to: '/profile', char: '人', name: '基础信息与用药', hint: '年龄 · 身高体重 · 过敏 · 西药', done: store.profileDone },
  { to: '/lab', char: '检', name: '体检指标录入', hint: '25 类指标 · OCR 智能识别', done: store.labsDone },
  { to: '/tongue', char: '舌', name: '舌面诊拍摄', hint: '舌象 / 面色量化（可选）', done: store.tongueDone },
  { to: '/questionnaire', char: '问', name: '症状问诊问卷', hint: '分步问答 · 逐类作答', done: store.symptomsDone },
])
const doneCount = computed(() => steps.value.filter((s) => s.done).length)

// ── 统一快捷入口（合并 TCM + Bio，不再分两组）──
const entries = [
  { to: '/lab', char: '检', title: '体检上传', desc: '指标录入 · OCR识别 · 分级', color: 'tcm' },
  { to: '/tongue', char: '诊', title: '舌面诊', desc: '引导拍摄 · 质量校验', color: 'tcm' },
  { to: '/questionnaire', char: '问', title: '智能问诊', desc: '症状问答 · 分步引导', color: 'tcm' },
  { to: '/archive', char: '档', title: '健康档案', desc: '档案建立 · 身份匹配', color: 'bio' },
  { to: '/archive', char: '析', title: 'AI 分析', desc: '风险识别 · 生物计算', color: 'bio' },
  { to: '/timeline', char: '案', title: '历史病历', desc: '时间轴 · 回顾追踪', color: 'tcm' },
]

function generate() {
  if (store.readyToGenerate) router.push('/report')
}
</script>

<template>
  <div>
    <!-- 随访提醒 -->
    <transition name="slide">
      <div v-if="shouldShowFollowup" class="notice">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 9.5a6 6 0 0 1 12 0c0 4.2 1.8 5.3 1.8 5.3H4.2S6 13.7 6 9.5ZM10 18.5a2 2 0 0 0 4 0" />
        </svg>
        <span>随访提醒：距上次调理已 {{ daysSinceLastVisit }} 天，建议复评体质变化</span>
        <button aria-label="关闭提醒" @click="showFollowup = false">✕</button>
      </div>
    </transition>

    <!-- 主视觉 -->
    <section class="hero">
      <svg class="enso" viewBox="0 0 200 200" aria-hidden="true">
        <circle cx="100" cy="100" r="82" fill="none" stroke="currentColor" stroke-width="11"
          stroke-linecap="round" stroke-dasharray="356 160" transform="rotate(-60 100 100)" />
      </svg>
      <p class="hero-tag">辨证溯源 <i>·</i> 生物计算</p>
      <h1>今日调理，<br />从了解自己开始</h1>
      <p class="hero-sub">融合中医辨证与现代生物计算，生成个人专属健康分析、组方与生活干预方案。</p>
    </section>

    <!-- 方案生成进度 -->
    <section class="card prog">
      <div class="prog-head">
        <h3 class="serif">方案生成进度</h3>
        <span class="chip">{{ doneCount }} / {{ steps.length }} 项已备</span>
      </div>
      <div class="prog-bar"><i :style="{ width: (doneCount / steps.length) * 100 + '%' }"></i></div>

      <router-link v-for="s in steps" :key="s.to" :to="s.to" class="step">
        <span class="medal serif" :class="{ lit: s.done }">{{ s.char }}</span>
        <span class="step-txt">
          <b>{{ s.name }}</b>
          <small>{{ s.hint }}</small>
        </span>
        <span v-if="s.done" class="mark done">已完成</span>
        <span v-else class="mark todo">去填写 ›</span>
      </router-link>

      <button class="btn btn-primary btn-block gen" :disabled="!store.readyToGenerate" @click="generate">
        生成调理方案
      </button>
      <p v-if="!store.readyToGenerate" class="gen-hint">需先完成「基础信息」与「症状问卷」</p>
    </section>

    <!-- 统一功能入口 -->
    <h2 class="section-title">功能入口 <small>FEATURES</small></h2>
    <section class="grid">
      <router-link v-for="e in entries" :key="e.char" :to="e.to" class="card entry" :class="e.color">
        <span class="medal lg serif" :class="e.color">{{ e.char }}</span>
        <b>{{ e.title }}</b>
        <small>{{ e.desc }}</small>
      </router-link>
    </section>

    <p class="foot serif">以证为纲 · 溯源而治 · 生物计算</p>
  </div>
</template>

<style scoped>
/* 随访通知条 */
.notice {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; margin-bottom: 14px;
  font-size: 12.5px; color: var(--ink-2);
  background: var(--gold-tint); border: 1px solid var(--line);
  border-radius: var(--radius-sm);
}
.notice svg { color: var(--gold); flex-shrink: 0; }
.notice span { flex: 1; }
.notice button { border: none; background: none; color: var(--ink-3); cursor: pointer; font-size: 12px; padding: 2px; }
.slide-leave-active { transition: all 0.25s ease; }
.slide-leave-to { opacity: 0; transform: translateY(-8px); }

/* 主视觉 */
.hero { position: relative; padding: 26px 4px 8px; overflow: hidden; }
.enso {
  position: absolute; top: -34px; right: -46px;
  width: 190px; color: var(--gold);
  opacity: 0.16; pointer-events: none;
}
.hero-tag {
  margin: 0 0 8px; font-size: 12px; letter-spacing: 0.3em;
  color: var(--gold); font-weight: 700;
}
.hero-tag i { font-style: normal; color: var(--seal); }
.hero h1 { margin: 0 0 10px; font-size: 30px; line-height: 1.32; font-weight: 900; }
.hero-sub { margin: 0; max-width: 34ch; font-size: 13.5px; color: var(--ink-2); }

/* 进度卡 */
.prog { margin-top: 20px; }
.prog-head { display: flex; align-items: center; justify-content: space-between; }
.prog-head h3 { margin: 0; font-size: 16px; }
.prog-bar {
  height: 5px; margin: 12px 0 6px; border-radius: 999px;
  background: var(--primary-tint); overflow: hidden;
}
.prog-bar i {
  display: block; height: 100%; border-radius: inherit;
  background: linear-gradient(90deg, var(--primary), var(--gold));
  transition: width 0.45s cubic-bezier(0.2, 0.8, 0.3, 1);
}
.step {
  display: flex; align-items: center; gap: 12px;
  padding: 11px 2px; border-bottom: 1px dashed var(--line);
}
.step:last-of-type { border-bottom: none; }
.medal {
  width: 40px; height: 40px; flex-shrink: 0;
  display: grid; place-items: center;
  border-radius: 50%; font-size: 17px; color: var(--ink-3);
  background: var(--bg); border: 1px solid var(--line);
  transition: all 0.3s ease;
}
.medal.lit {
  color: var(--gold-soft);
  background: radial-gradient(circle at 32% 28%, #3d7a62, var(--primary-deep));
  border-color: transparent;
  box-shadow: 0 6px 14px -6px rgba(45, 95, 75, 0.55);
}
.step-txt { flex: 1; line-height: 1.35; }
.step-txt b { display: block; font-size: 14px; }
.step-txt small { color: var(--ink-3); font-size: 11.5px; }
.mark { font-size: 12px; }
.mark.done { color: var(--gold); font-weight: 600; }
.mark.todo { color: var(--ink-3); }
.gen { margin-top: 14px; }
.gen-hint { margin: 8px 0 0; text-align: center; font-size: 11.5px; color: var(--ink-3); }

/* 统一功能入口 */
.grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.entry {
  display: flex; flex-direction: column; align-items: flex-start; gap: 3px;
  padding: 16px; transition: transform 0.18s ease, box-shadow 0.25s ease;
}
.entry:active { transform: scale(0.97); }
.entry b { margin-top: 8px; font-size: 14px; }
.entry small { font-size: 11px; color: var(--ink-3); }

/* TCM 绿色系 */
.medal.lg {
  width: 44px; height: 44px; font-size: 19px;
  color: var(--gold-soft);
  background: radial-gradient(circle at 32% 28%, #3d7a62, var(--primary-deep));
  border: none;
  box-shadow: inset 0 0 0 1px rgba(231, 216, 182, 0.28), 0 8px 16px -8px rgba(45, 95, 75, 0.6);
}

/* Bio 蓝色系 */
.medal.lg.bio {
  background: radial-gradient(circle at 32% 28%, #3d5a8a, #1a3a6a);
  box-shadow: inset 0 0 0 1px rgba(180, 200, 240, 0.28), 0 8px 16px -8px rgba(40, 60, 120, 0.6);
}
.entry.bio { border-left: 3px solid rgba(60, 100, 180, 0.2); }

.foot {
  margin: 30px 0 6px; text-align: center;
  font-size: 12px; letter-spacing: 0.4em; color: var(--ink-3);
}
</style>
