<template>
  <div class="page-container">
    <!-- 顶部进度指示器 -->
    <div class="wizard-progress">
      <div
        v-for="(group, idx) in categoryList"
        :key="group.cat"
        class="progress-dot"
        :class="{
          active: idx === currentCategoryIndex,
          done: isCategoryDone(group.cat),
          future: idx > currentCategoryIndex && !isCategoryDone(group.cat),
        }"
        @click="jumpTo(idx)"
      >
        <span class="dot-inner">{{ idx + 1 }}</span>
        <span class="dot-label">{{ group.cat }}</span>
      </div>
      <div class="progress-line">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
    </div>

    <!-- 页面头部 -->
    <div class="page-header">
      <div class="serif page-title">📝 中医智能问诊</div>
      <div class="page-desc">
        请根据过去 7 天的实际情况完成以下问题。没有标准答案，选择最符合你的情况即可。
      </div>
    </div>

    <!-- 预设快捷填充 -->
    <div class="preset-bar">
      <span class="preset-label">快捷模版：</span>
      <button class="chip-btn" @click="loadPreset('liver')">🌿 肝郁脾虚型</button>
      <button class="chip-btn" @click="loadPreset('cold')">❄️ 脾胃虚寒型</button>
      <button class="chip-btn" @click="loadPreset('reset')">🔄 全部清空</button>
    </div>

    <!-- 加载提示 -->
    <div v-if="loading" class="card loading-card">
      <div class="spinner">⌛</div>
      <div>正在加载问诊量表...</div>
    </div>

    <!-- 当前分类的问题卡片 -->
    <div v-else>
      <transition name="fade-slide" mode="out-in">
        <div :key="currentCategory" class="category-block">
          <div class="section-title">
            {{ currentCategory }}
            <small>{{ currentGroup.length }} 个问题</small>
          </div>

          <div class="question-list">
            <div
              v-for="(dim, qIdx) in currentGroup"
              :key="dim.key"
              class="question-card"
              :class="{ answered: store.symptoms[dim.key] != null }"
            >
              <div class="q-number">Q{{ qIdx + 1 }}</div>
              <div class="q-body">
                <div class="q-label">{{ dim.label || dim.key }}</div>
                <div class="q-prompt">{{ dim.prompt }}</div>

                <!-- 第一类：主观症状 五级选择 -->
                <div v-if="dim.type === 'subjective' || !dim.type" class="choice-group">
                  <button
                    v-for="opt in SUBJECTIVE_OPTIONS"
                    :key="opt.value"
                    class="choice-btn"
                    :class="{ selected: store.symptoms[dim.key] === opt.value }"
                    @click="selectAnswer(dim.key, opt.value)"
                  >
                    {{ opt.label }}
                  </button>
                </div>

                <!-- 第二类：可量化症状 事实选择 -->
                <div v-else-if="dim.type === 'quantifiable'" class="choice-group">
                  <button
                    v-for="opt in dim.options"
                    :key="opt.value"
                    class="choice-btn fact-btn"
                    :class="{ selected: store.symptoms[dim.key] === opt.value }"
                    @click="selectAnswer(dim.key, opt.value)"
                  >
                    {{ opt.label }}
                  </button>
                </div>

                <!-- 第三类：分类选择 -->
                <div v-else-if="dim.type === 'classification'" class="choice-group classification">
                  <button
                    v-for="opt in dim.options"
                    :key="opt.value"
                    class="choice-btn classify-btn"
                    :class="{ selected: store.symptoms[dim.key] === opt.value }"
                    @click="selectAnswer(dim.key, opt.value)"
                  >
                    <span class="classify-icon">{{ opt.icon || '○' }}</span>
                    <span>{{ opt.label }}</span>
                  </button>
                </div>

                <!-- 已选提示 -->
                <transition name="fade">
                  <div v-if="store.symptoms[dim.key] != null" class="answer-tag">
                    ✓ 已选：{{ getDisplayLabel(dim, store.symptoms[dim.key]) }}
                  </div>
                </transition>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <!-- 分类内切换（内联按钮） -->
    <div class="cat-nav">
      <button
        v-if="currentCategoryIndex > 0"
        class="btn btn-back"
        @click="prevCategory"
      >
        ◀ 上一类
      </button>
      <span v-else></span>

      <span class="cat-nav-hint">{{ currentCategory }} {{ currentCategoryIndex + 1 }}/{{ categoryList.length }}</span>

      <button
        v-if="currentCategoryIndex < categoryList.length - 1"
        class="btn btn-sm"
        @click="nextCategory"
      >
        下一类 ▶
      </button>
      <span v-else class="cat-done-hint">✓ 已到最后一类</span>
    </div>

    <!-- 跨页步骤引导（共享组件） -->
    <StepGuide />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import StepGuide from '../components/StepGuide.vue'
import { usePatientStore } from '../store/patient'
import { api } from '../api'

const router = useRouter()
const store = usePatientStore()
const loading = ref(false)
const currentCategoryIndex = ref(0)

// ===== 第一类：主观症状的五级标准选项 =====
const SUBJECTIVE_OPTIONS = [
  { label: '没有', value: 0 },
  { label: '轻微', value: 2 },
  { label: '一般', value: 5 },
  { label: '明显', value: 7 },
  { label: '非常明显', value: 10 },
]

// ===== 问诊维度定义（三种类型） =====
const DEFAULT_DIMENSIONS = [
  // ---- 睡眠 ----
  {
    key: '入睡困难', label: '入睡困难', category: '睡眠',
    type: 'subjective',
    prompt: '过去 7 天，你入睡困难的情况有多明显？',
  },
  {
    key: '入睡时长', label: '入睡所需时间', category: '睡眠',
    type: 'quantifiable',
    prompt: '通常需要多久才能入睡？',
    options: [
      { label: '≤15 分钟', value: 0 },
      { label: '16–30 分钟', value: 2 },
      { label: '31–60 分钟', value: 5 },
      { label: '1–2 小时', value: 7 },
      { label: '>2 小时', value: 10 },
    ],
  },
  {
    key: '夜尿多', label: '夜间起夜', category: '睡眠',
    type: 'quantifiable',
    prompt: '平均每晚起夜几次？',
    options: [
      { label: '0 次', value: 0 },
      { label: '1 次', value: 2 },
      { label: '2 次', value: 5 },
      { label: '3 次', value: 7 },
      { label: '4 次及以上', value: 10 },
    ],
  },

  // ---- 消化 ----
  {
    key: '食欲差', label: '食欲减退', category: '消化',
    type: 'subjective',
    prompt: '过去 7 天，你的食欲减退有多明显？',
  },
  {
    key: '腹胀', label: '腹胀', category: '消化',
    type: 'subjective',
    prompt: '过去 7 天，你的腹胀感有多明显？',
  },

  // ---- 二便 ----
  {
    key: '大便性状', label: '大便情况', category: '二便',
    type: 'classification',
    prompt: '最近一周，你的大便更接近哪种情况？',
    options: [
      { label: '正常成形', value: 0, icon: '✅' },
      { label: '偏稀/不成形', value: 3, icon: '💧' },
      { label: '水样泄泻', value: 7, icon: '🌊' },
      { label: '偏干/费力', value: 4, icon: '🧱' },
      { label: '干结便秘', value: 8, icon: '🔒' },
      { label: '时稀时干交替', value: 5, icon: '🔄' },
    ],
  },
  {
    key: '尿黄', label: '小便颜色', category: '二便',
    type: 'classification',
    prompt: '最近一周，你的小便颜色更接近？',
    options: [
      { label: '清澈透明', value: 0, icon: '💎' },
      { label: '淡黄正常', value: 1, icon: '🟡' },
      { label: '深黄', value: 5, icon: '🟠' },
      { label: '浓茶色', value: 8, icon: '🟤' },
      { label: '偏红/带血', value: 10, icon: '🔴' },
    ],
  },

  // ---- 寒热 ----
  {
    key: '怕冷', label: '畏寒怕冷', category: '寒热',
    type: 'subjective',
    prompt: '过去 7 天，你的畏寒怕冷感觉有多明显？',
  },
  {
    key: '怕热', label: '怕热烦热', category: '寒热',
    type: 'subjective',
    prompt: '过去 7 天，你的怕热或手足心发热有多明显？',
  },

  // ---- 情志 ----
  {
    key: '情绪抑郁', label: '情绪低落', category: '情志',
    type: 'subjective',
    prompt: '过去 7 天，你心情低落或闷闷不乐的程度有多明显？',
  },
  {
    key: '烦躁易怒', label: '急躁易怒', category: '情志',
    type: 'subjective',
    prompt: '过去 7 天，你急躁、容易发怒的情况有多明显？',
  },

  // ---- 体能 ----
  {
    key: '疲劳', label: '疲劳乏力', category: '体能',
    type: 'subjective',
    prompt: '过去 7 天，你的疲劳感有多明显？',
  },

  // ---- 汗出 ----
  {
    key: '自汗', label: '白天出汗', category: '汗出',
    type: 'subjective',
    prompt: '过去 7 天，白天不因运动也出汗的情况有多明显？',
  },
  {
    key: '盗汗', label: '夜间盗汗', category: '汗出',
    type: 'subjective',
    prompt: '过去 7 天，睡后出汗、醒后汗止的情况有多明显？',
  },

  // ---- 疼痛 ----
  {
    key: '刺痛固定', label: '固定刺痛', category: '疼痛',
    type: 'subjective',
    prompt: '过去 7 天，你有固定位置的针刺样疼痛吗？',
  },
  {
    key: '胀痛走窜', label: '走窜胀痛', category: '疼痛',
    type: 'subjective',
    prompt: '过去 7 天，你有位置不固定的胀痛吗？',
  },

  // ---- 口味 ----
  {
    key: '口苦', label: '口苦口干', category: '口味',
    type: 'classification',
    prompt: '最近一周晨起时，你的口腔感觉更接近？',
    options: [
      { label: '正常', value: 0, icon: '😊' },
      { label: '口干', value: 3, icon: '🏜️' },
      { label: '口苦', value: 5, icon: '😖' },
      { label: '口干且口苦', value: 7, icon: '😣' },
      { label: '口中黏腻', value: 6, icon: '🫠' },
    ],
  },

  // ---- 经期(女) ----
  {
    key: '经期血块', label: '月经血块', category: '经期(女)',
    type: 'subjective',
    prompt: '近一周期，经血中出现血块的情况有多明显？',
  },
  {
    key: '经量少色淡', label: '经量稀少', category: '经期(女)',
    type: 'subjective',
    prompt: '近一周期，月经量减少或色淡的情况有多明显？',
  },
  {
    key: '经前乳胀', label: '经前乳胀', category: '经期(女)',
    type: 'subjective',
    prompt: '经前乳房胀痛不适的感觉有多明显？',
  },
]

const rawDimensions = ref([])

const dimensions = computed(() => {
  const dims = rawDimensions.value.length > 0 ? rawDimensions.value : DEFAULT_DIMENSIONS
  if (store.patient.sex === 'M') {
    return dims.filter((d) => d.category !== '经期(女)')
  }
  return dims
})

const categoryList = computed(() => {
  const map = {}
  const order = []
  dimensions.value.forEach((item) => {
    const cat = item.category || '综合症状'
    if (!map[cat]) {
      map[cat] = []
      order.push(cat)
    }
    map[cat].push(item)
  })
  return order.map((cat) => ({ cat, items: map[cat] }))
})

const currentCategory = computed(() => categoryList.value[currentCategoryIndex.value]?.cat || '')
const currentGroup = computed(() => categoryList.value[currentCategoryIndex.value]?.items || [])

const progressPercent = computed(() => {
  if (categoryList.value.length === 0) return 0
  return Math.round(((currentCategoryIndex.value + 1) / categoryList.value.length) * 100)
})

function isCategoryDone(cat) {
  const group = categoryList.value.find((g) => g.cat === cat)
  if (!group) return false
  return group.items.some((dim) => store.symptoms[dim.key] != null)
}

function selectAnswer(key, value) {
  // 点击已选的选项则取消选择
  if (store.symptoms[key] === value) {
    store.setSymptomScore(key, 0)
  } else {
    store.setSymptomScore(key, value)
  }
}

function getDisplayLabel(dim, value) {
  if (dim.type === 'subjective' || !dim.type) {
    const opt = SUBJECTIVE_OPTIONS.find((o) => o.value === value)
    return opt ? opt.label : ''
  }
  if (dim.options) {
    const opt = dim.options.find((o) => o.value === value)
    return opt ? opt.label : ''
  }
  return ''
}

function nextCategory() {
  if (currentCategoryIndex.value < categoryList.value.length - 1) {
    currentCategoryIndex.value++
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

function prevCategory() {
  if (currentCategoryIndex.value > 0) {
    currentCategoryIndex.value--
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

function skipCategory() {
  nextCategory()
  if (currentCategoryIndex.value >= categoryList.value.length - 1) {
    // 最后一步跳过 → 回首页
    router.push('/')
  }
}

function jumpTo(idx) {
  currentCategoryIndex.value = idx
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// ===== 预设填充 =====
const PRESET_MAP = {
  liver: { 情绪抑郁: 7, 胀痛走窜: 7, 入睡困难: 5, 食欲差: 5, 疲劳: 5, 口苦: 5 },
  cold: { 怕冷: 7, 大便性状: 3, 腹胀: 5, 疲劳: 7, 自汗: 5 },
}

function loadPreset(type) {
  if (type === 'reset') {
    store.setSymptoms({})
    return
  }
  store.setSymptoms(PRESET_MAP[type] || {})
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.questionnaire(store.patient.sex)
    if (res && res.dimensions) rawDimensions.value = res.dimensions
  } catch (err) {
    console.warn('API fallback to local defaults:', err)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.page-container {
  max-width: 680px;
  margin: 0 auto;
  padding: 16px 16px 100px;
}

/* ===== 顶部进度条 ===== */
.wizard-progress {
  display: flex;
  align-items: flex-start;
  gap: 0;
  margin-bottom: 20px;
  padding: 14px 8px 8px;
  position: relative;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
.progress-line {
  position: absolute;
  top: 27px;
  left: 24px;
  right: 24px;
  height: 3px;
  background: var(--line);
  border-radius: 2px;
  z-index: 0;
}
.progress-fill {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, var(--primary), var(--gold));
  transition: width 0.4s ease;
}
.progress-dot {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-width: 48px;
  cursor: pointer;
  z-index: 1;
}
.dot-inner {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 700;
  background: var(--card);
  border: 2px solid var(--line);
  color: var(--ink-3);
  transition: all 0.3s ease;
}
.progress-dot.active .dot-inner {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
  box-shadow: 0 3px 12px -4px rgba(45, 95, 75, 0.5);
  transform: scale(1.15);
}
.progress-dot.done .dot-inner {
  background: var(--gold);
  border-color: var(--gold);
  color: #fff;
}
.dot-label {
  font-size: 10px;
  color: var(--ink-3);
  margin-top: 4px;
  white-space: nowrap;
  transition: color 0.3s;
}
.progress-dot.active .dot-label {
  color: var(--primary);
  font-weight: 600;
}

/* ===== 页面头部 ===== */
.page-header { margin-bottom: 14px; }
.page-title {
  font-size: 22px;
  color: var(--primary-deep);
  margin-bottom: 4px;
}
.page-desc {
  font-size: 13.5px;
  color: var(--ink-2);
  line-height: 1.6;
}

.preset-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.preset-label { font-size: 12px; color: var(--ink-2); }
.chip-btn {
  background: var(--card);
  border: 1px solid var(--line);
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  cursor: pointer;
  color: var(--ink);
  transition: all 0.2s;
}
.chip-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.loading-card {
  text-align: center;
  padding: 40px;
  color: var(--ink-2);
}
.spinner { font-size: 32px; margin-bottom: 10px; }

/* ===== 问题卡片（扁平融入式） ===== */
.question-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.question-card {
  display: flex;
  gap: 14px;
  padding: 18px 4px;
  border-bottom: 1px solid var(--line);
  transition: background 0.25s ease;
}
.question-card:last-child {
  border-bottom: none;
}
.question-card.answered {
  background: var(--primary-tint);
  border-radius: var(--radius-sm);
  margin: 2px 0;
}
.q-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--primary-tint);
  color: var(--primary);
  font-size: 11px;
  font-weight: 700;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  margin-top: 2px;
}
.question-card.answered .q-number {
  background: var(--primary);
  color: #fff;
}
.q-body { flex: 1; min-width: 0; }
.q-label {
  font-weight: 700;
  font-size: 15px;
  color: var(--ink);
  margin-bottom: 2px;
}
.q-prompt {
  font-size: 13px;
  color: var(--ink-2);
  margin-bottom: 12px;
  line-height: 1.5;
}

/* ===== 选项按钮组 ===== */
.choice-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.choice-btn {
  padding: 8px 16px;
  border-radius: 20px;
  border: 1.5px solid var(--line);
  background: var(--bg);
  color: var(--ink);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}
.choice-btn:hover {
  border-color: var(--primary);
  background: var(--primary-tint);
}
.choice-btn.selected {
  background: var(--primary);
  border-color: var(--primary);
  color: #fff;
  box-shadow: 0 3px 10px -4px rgba(45, 95, 75, 0.45);
  transform: scale(1.03);
}

/* 分类选择按钮（稍宽，带图标） */
.classification {
  gap: 8px;
}
.classify-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 12px;
}
.classify-icon { font-size: 15px; }

/* 已选标签 */
.answer-tag {
  margin-top: 10px;
  font-size: 12px;
  color: var(--primary);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ===== 分类内联切换 ===== */
.cat-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 20px 0 8px;
  padding: 0 2px;
}
.cat-nav-hint {
  font-size: 12px;
  color: var(--ink-3);
}
.cat-done-hint {
  font-size: 12px;
  color: var(--gold);
  font-weight: 600;
}
.btn-sm {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--card);
  color: var(--ink);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-sm:hover {
  border-color: var(--primary);
  color: var(--primary);
}

/* ===== 过渡动画 ===== */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(30px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* 响应式 */
@media (max-width: 480px) {
  .choice-btn { padding: 7px 12px; font-size: 12px; }
  .classify-btn { padding: 7px 10px; }
}
</style>
