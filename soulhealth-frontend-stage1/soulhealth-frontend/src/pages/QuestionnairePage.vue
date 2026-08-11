<template>
  <div class="page-container">
    <div class="page-header">
      <div class="serif page-title">📝 中医十七/二十维智能问诊量表</div>
      <div class="page-desc">
        当前为 {{ sexLabel }}问诊量表（共 {{ dimensions.length }} 项）。请拖动滑块对近一周各项症状程度打分 (0分无症状 ~ 10分极严重)。
      </div>
    </div>

    <!-- 预设症状快捷填充 -->
    <div class="preset-bar">
      <span class="preset-label">快捷问诊模版：</span>
      <button class="chip-btn" @click="loadPreset('liver')">🌿 肝郁脾虚型</button>
      <button class="chip-btn" @click="loadPreset('cold')">❄️ 脾胃虚寒型</button>
      <button class="chip-btn" @click="loadPreset('reset')">🔄 全部清空</button>
    </div>

    <!-- 加载提示或错误 -->
    <div v-if="loading" class="card loading-card">
      <div class="spinner">⌛</div>
      <div>正在加载针对您性别的四诊合参问诊量表...</div>
    </div>

    <div v-else>
      <!-- 分组展示量表 -->
      <div v-for="(group, cat) in groupedDimensions" :key="cat" class="category-block">
        <div class="section-title">
          {{ cat }}
          <small>{{ group.length }} 项维度</small>
        </div>

        <div class="symptom-grid">
          <div v-for="dim in group" :key="dim.key" class="card symptom-card">
            <div class="symptom-header">
              <span class="symptom-label">{{ dim.label || dim.key }}</span>
              <span class="symptom-score" :class="scoreClass(store.symptoms[dim.key] || 0)">
                {{ store.symptoms[dim.key] || 0 }} 分
              </span>
            </div>

            <div class="symptom-prompt">{{ dim.prompt || '近一周症状严重程度' }}</div>

            <div class="slider-wrapper">
              <input
                type="range"
                min="0"
                max="10"
                step="1"
                :value="store.symptoms[dim.key] || 0"
                @input="onSliderChange(dim.key, $event.target.value)"
              />
              <div class="slider-ticks">
                <span>0 无</span>
                <span>5 中等</span>
                <span>10 剧烈</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 确认底部栏 -->
    <div class="page-footer-actions">
      <router-link to="/profile" class="btn">◀ 个人信息登记</router-link>
      <router-link to="/report" class="btn btn-primary">一键生成调理方案 ➔</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePatientStore } from '../store/patient'
import { api } from '../api'

const store = usePatientStore()

const loading = ref(false)
const rawDimensions = ref([])

const sexLabel = computed(() => (store.patient.sex === 'F' ? '女性专属' : '男性'))

// 规格书指定默认 17/20 维度备用
const DEFAULT_DIMENSIONS = [
  { key: '入睡困难', label: '睡眠质量', prompt: '近一周入睡困难程度', category: '睡眠' },
  { key: '食欲差', label: '食欲减退', prompt: '近一周食欲不振程度', category: '消化' },
  { key: '腹胀', label: '脘腹胀满', prompt: '饭后或平时腹部胀满', category: '消化' },
  { key: '便溏', label: '大便稀溏', prompt: '大便不成形或泄泻', category: '二便' },
  { key: '便秘', label: '大便秘结', prompt: '排便困难或周期延长', category: '二便' },
  { key: '尿黄', label: '小便黄赤', prompt: '尿色偏黄或有灼热感', category: '二便' },
  { key: '夜尿多', label: '夜间频繁', prompt: '起夜次数过多', category: '二便' },
  { key: '怕冷', label: '畏寒肢冷', prompt: '喜暖怕冷或手足不温', category: '寒热' },
  { key: '怕热', label: '五心烦热', prompt: '发热或自觉手足心发热', category: '寒热' },
  { key: '情绪抑郁', label: '情志抑郁', prompt: '心情闷闷不乐或善太息', category: '情志' },
  { key: '烦躁易怒', label: '急躁易怒', prompt: '情绪急躁容易发怒', category: '情志' },
  { key: '疲劳', label: '神疲乏力', prompt: '身体疲惫少气懒言', category: '体能' },
  { key: '自汗', label: '动则汗出', prompt: '白天不因劳累而出汗', category: '汗出' },
  { key: '盗汗', label: '夜间盗汗', prompt: '睡后汗出醒后汗止', category: '汗出' },
  { key: '刺痛固定', label: '血瘀刺痛', prompt: '痛处固定如针刺感', category: '疼痛' },
  { key: '胀痛走窜', label: '气滞胀痛', prompt: '痛无定处伴发胀感', category: '疼痛' },
  { key: '口苦', label: '口苦口干', prompt: '早起口中发苦或发干', category: '口味' },
  // 女性额外3项
  { key: '经期血块', label: '月经血块', prompt: '经色紫暗伴有血块', category: '经期(女)' },
  { key: '经量少色淡', label: '经量稀少', prompt: '月经量明显减少色淡', category: '经期(女)' },
  { key: '经前乳胀', label: '经前乳胀', prompt: '经前乳房胀痛不适', category: '经期(女)' },
]

const dimensions = computed(() => {
  if (rawDimensions.value.length > 0) return rawDimensions.value
  if (store.patient.sex === 'M') {
    return DEFAULT_DIMENSIONS.filter((d) => d.category !== '经期(女)')
  }
  return DEFAULT_DIMENSIONS
})

const groupedDimensions = computed(() => {
  const map = {}
  dimensions.value.forEach((item) => {
    const cat = item.category || '综合症状'
    if (!map[cat]) map[cat] = []
    map[cat].push(item)
  })
  return map
})

onMounted(async () => {
  loading.value = true
  try {
    const res = await api.questionnaire(store.patient.sex)
    if (res && res.dimensions) {
      rawDimensions.value = res.dimensions
    }
  } catch (err) {
    console.warn('API Questionnaire fetch fallback to local defaults:', err)
  } finally {
    loading.value = false
  }
})

function onSliderChange(key, val) {
  store.setSymptomScore(key, Number(val))
}

function scoreClass(val) {
  if (val === 0) return 'score-0'
  if (val <= 3) return 'score-low'
  if (val <= 6) return 'score-mid'
  return 'score-high'
}

function loadPreset(type) {
  if (type === 'reset') {
    store.setSymptoms({})
    return
  }
  if (type === 'liver') {
    store.setSymptoms({
      情绪抑郁: 6,
      胀痛走窜: 7,
      入睡困难: 5,
      食欲差: 4,
      疲劳: 5,
      口苦: 3,
    })
  } else if (type === 'cold') {
    store.setSymptoms({
      怕冷: 7,
      便溏: 6,
      腹胀: 5,
      疲劳: 6,
      自汗: 4,
    })
  }
}
</script>

<style scoped>
.page-container {
  max-width: 840px;
  margin: 0 auto;
  padding: 20px 16px 80px;
}
.page-title {
  font-size: 22px;
  color: var(--primary-deep);
  margin-bottom: 6px;
}
.page-desc {
  font-size: 14px;
  color: var(--ink-2);
  margin-bottom: 20px;
}

.preset-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.preset-label {
  font-size: 12px;
  color: var(--ink-2);
}
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
.spinner {
  font-size: 32px;
  margin-bottom: 10px;
}

.category-block {
  margin-bottom: 24px;
}

.symptom-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
}
.symptom-card {
  padding: 14px 16px;
}
.symptom-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.symptom-label {
  font-weight: 700;
  font-size: 15px;
  color: var(--ink);
}
.symptom-score {
  font-weight: 700;
  font-size: 14px;
  padding: 2px 8px;
  border-radius: 12px;
}
.score-0 {
  background: rgba(0, 0, 0, 0.05);
  color: var(--ink-3);
}
.score-low {
  background: rgba(76, 175, 80, 0.15);
  color: var(--ok);
}
.score-mid {
  background: var(--gold-tint);
  color: #8a6400;
}
.score-high {
  background: rgba(244, 67, 54, 0.15);
  color: var(--danger);
}

.symptom-prompt {
  font-size: 12px;
  color: var(--ink-2);
  margin-bottom: 12px;
}

.slider-wrapper input[type='range'] {
  width: 100%;
  accent-color: var(--primary);
  cursor: pointer;
}
.slider-ticks {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--ink-3);
  margin-top: 2px;
}

.page-footer-actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 30px;
}
</style>
