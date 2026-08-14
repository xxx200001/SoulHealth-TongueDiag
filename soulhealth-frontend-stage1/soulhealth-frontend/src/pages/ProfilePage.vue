<template>
  <div class="page-container">
    <div class="page-header">
      <div class="serif page-title">👤 个人信息与用药登记</div>
      <div class="page-desc">
        录入年龄、体重与常规用药，以便组方引擎精准推算 0.1g 克重并进行中西药相互作用与毒理禁忌核验。
      </div>
      <div class="demo-preset-bar">
        <span>💡 首次使用？</span>
        <button class="btn btn-sm" @click="store.loadDemoPreset()">⚡ 快速一键填入测试数据</button>
        <button v-if="store.profileDone" class="btn btn-sm btn-ghost" @click="store.resetAll()">清空重填</button>
      </div>
    </div>

    <!-- 基础体征信息卡片 -->
    <div class="card form-card">
      <div class="card-title serif">📌 基础体征与性别</div>
      <div class="form-grid">
        <div class="form-group">
          <label>性别</label>

          <div class="gender-toggle">
            <button
              type="button"
              class="toggle-btn"
              :class="{ active: store.patient.sex === 'M' }"
              @click="setSex('M')"
            >
              👨 男 (17项量表)
            </button>
            <button
              type="button"
              class="toggle-btn"
              :class="{ active: store.patient.sex === 'F' }"
              @click="setSex('F')"
            >
              👩 女 (20项量表)
            </button>
          </div>
        </div>

        <div class="form-group">
          <label>年龄 (岁)</label>
          <input
            v-model.number="store.patient.age"
            type="number"
            min="1"
            max="120"
            placeholder="例如: 34"
            @change="store.persist()"
          />
        </div>

        <div class="form-group">
          <label>身高 (cm)</label>
          <input
            v-model.number="store.patient.height_cm"
            type="number"
            min="50"
            max="230"
            placeholder="例如: 162"
            @change="store.persist()"
          />
        </div>

        <div class="form-group">
          <label>体重 (kg)</label>
          <input
            v-model.number="store.patient.weight_kg"
            type="number"
            min="10"
            max="200"
            placeholder="例如: 52"
            @change="store.persist()"
          />
        </div>
      </div>

      <div v-if="bmi" class="bmi-badge">
        <span>BMI 指数：<strong>{{ bmi }}</strong> ({{ bmiText }})</span>
      </div>

      <!-- 特殊生理状态 (仅女) -->
      <div v-if="store.patient.sex === 'F'" class="special-status">
        <label class="checkbox-label">
          <input
            type="checkbox"
            v-model="store.patient.pregnant"
            @change="store.persist()"
          />
          <span class="checkbox-text">⚠️ 处于妊娠期 / 备孕期 (触发红线安全禁忌拦截)</span>
        </label>
      </div>
    </div>

    <!-- 过敏药材录入 -->
    <div class="card form-card">
      <div class="card-title serif">🌿 过敏药材 / 禁忌标签</div>
      <div class="desc-tip">已录入过敏药材在组方推荐时会被严格排除或替代。</div>

      <div class="tags-container">
        <span
          v-for="(alg, idx) in store.patient.allergies"
          :key="idx"
          class="tag-chip danger-chip"
        >
          🚫 {{ alg }}
          <button class="tag-del" @click="removeAllergy(idx)">✕</button>
        </span>
      </div>

      <div class="add-tag-input">
        <input
          v-model="newAllergy"
          type="text"
          placeholder="输入过敏中药名 (如: 青霉素, 细辛)"
          @keyup.enter="addAllergy"
        />
        <button class="btn btn-sm" @click="addAllergy">添加过敏源</button>
      </div>
    </div>

    <!-- 当前服用西药录入 -->
    <div class="card form-card">
      <div class="card-title serif">💊 当前服用西药 (中西药相互作用校验)</div>
      <div class="desc-tip">
        例如华法林、阿司匹林、他汀等，用于后端口服药物冲突与出血风险安全筛查。
      </div>

      <!-- 常用快捷选择 -->
      <div class="drug-quick-list">
        <span class="quick-label">快捷填入：</span>
        <button
          v-for="drug in commonDrugs"
          :key="drug"
          class="chip-btn"
          :class="{ added: store.current_drugs.includes(drug) }"
          @click="toggleDrug(drug)"
        >
          {{ store.current_drugs.includes(drug) ? '✓ ' + drug : '+ ' + drug }}
        </button>
      </div>

      <div class="tags-container">
        <span
          v-for="(drug, idx) in store.current_drugs"
          :key="idx"
          class="tag-chip warn-chip"
        >
          💊 {{ drug }}
          <button class="tag-del" @click="removeDrug(idx)">✕</button>
        </span>
      </div>

      <div class="add-tag-input">
        <input
          v-model="newDrug"
          type="text"
          placeholder="手动输入西药名称"
          @keyup.enter="addDrug"
        />
        <button class="btn btn-sm" @click="addDrug">添加药名</button>
      </div>
    </div>

    <!-- 跨页步骤引导 -->
    <StepGuide />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { usePatientStore } from '../store/patient'
import StepGuide from '../components/StepGuide.vue'

const store = usePatientStore()

const newAllergy = ref('')
const newDrug = ref('')
const commonDrugs = ['华法林', '阿司匹林', '阿托伐他汀', '二甲双胍', '硝苯地平']

const bmi = computed(() => {
  const p = store.patient
  if (p.height_cm && p.weight_kg) {
    const h = p.height_cm / 100
    return (p.weight_kg / (h * h)).toFixed(1)
  }
  return null
})

const bmiText = computed(() => {
  if (!bmi.value) return ''
  const val = Number(bmi.value)
  if (val < 18.5) return '偏瘦'
  if (val < 24) return '正常体型'
  if (val < 28) return '超重'
  return '肥胖'
})

function setSex(s) {
  store.patient.sex = s
  if (s === 'M') {
    store.patient.pregnant = false
  }
  store.persist()
}

function addAllergy() {
  const val = newAllergy.value.trim()
  if (val && !store.patient.allergies.includes(val)) {
    store.patient.allergies.push(val)
    store.persist()
    newAllergy.value = ''
  }
}

function removeAllergy(idx) {
  store.patient.allergies.splice(idx, 1)
  store.persist()
}

function toggleDrug(drug) {
  const idx = store.current_drugs.indexOf(drug)
  if (idx >= 0) {
    store.current_drugs.splice(idx, 1)
  } else {
    store.current_drugs.push(drug)
  }
  store.persist()
}

function addDrug() {
  const val = newDrug.value.trim()
  if (val && !store.current_drugs.includes(val)) {
    store.current_drugs.push(val)
    store.persist()
    newDrug.value = ''
  }
}

function removeDrug(idx) {
  store.current_drugs.splice(idx, 1)
  store.persist()
}
</script>

<style scoped>
.page-container {
  max-width: 800px;
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
  margin-bottom: 12px;
}

.demo-preset-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding: 8px 14px;
  background: var(--gold-tint);
  border: 1px dashed var(--gold);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--primary-deep);
}
.btn-ghost {
  background: transparent;
  border: 1px solid var(--line);
  color: var(--ink-2);
}

.form-card {
  margin-bottom: 20px;
}
.card-title {
  font-size: 16px;
  color: var(--primary-deep);
  margin-bottom: 14px;
}
.desc-tip {
  font-size: 12px;
  color: var(--ink-2);
  margin-bottom: 12px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-group label {
  font-size: 12px;
  color: var(--ink-2);
  font-weight: 500;
}

.gender-toggle {
  display: flex;
  gap: 6px;
}
.toggle-btn {
  flex: 1;
  padding: 9px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--line);
  background: var(--bg);
  color: var(--ink-2);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}
.toggle-btn.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
  font-weight: 600;
}

.bmi-badge {
  background: var(--gold-tint);
  border: 1px solid var(--line);
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--primary-deep);
  display: inline-block;
  margin-bottom: 12px;
}

.special-status {
  padding-top: 10px;
  border-top: 1px dashed var(--line);
}
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.checkbox-text {
  font-size: 13px;
  color: var(--danger);
  font-weight: 600;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
}
.danger-chip {
  background: rgba(244, 67, 54, 0.1);
  color: var(--danger);
  border: 1px solid rgba(244, 67, 54, 0.3);
}
.warn-chip {
  background: var(--gold-tint);
  color: var(--primary-deep);
  border: 1px solid var(--line);
}
.tag-del {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 12px;
  opacity: 0.7;
}
.tag-del:hover {
  opacity: 1;
}

.add-tag-input {
  display: flex;
  gap: 8px;
}
.add-tag-input input {
  flex: 1;
}

.drug-quick-list {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.quick-label {
  font-size: 12px;
  color: var(--ink-2);
}
.chip-btn {
  background: var(--bg);
  border: 1px solid var(--line);
  padding: 3px 10px;
  border-radius: 16px;
  font-size: 12px;
  cursor: pointer;
  color: var(--ink);
  transition: all 0.2s;
}
.chip-btn.added {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

</style>
