<template>
  <div class="page-container">
    <div class="page-header">
      <div class="serif page-title">📜 终身病历与溯源时间轴</div>
      <div class="page-desc">
        按时间顺序归档体检报告、舌面诊影像、四诊问诊与调理组方历史。支持快捷检索与 Markdown 档案导出。
      </div>
    </div>

    <!-- 顶部工具与筛选栏 -->
    <div class="card filter-bar">
      <div class="filter-group">
        <span class="filter-label">类型筛选：</span>
        <button
          v-for="type in types"
          :key="type.key"
          class="chip-btn"
          :class="{ active: activeType === type.key }"
          @click="activeType = type.key"
        >
          {{ type.label }}
        </button>
      </div>

      <div class="export-actions">
        <button class="btn btn-sm" @click="handleExportWord">
          📄 导出 Word 病历 (.doc)
        </button>
        <button class="btn btn-sm" @click="handleExportPDF">
          🖨️ 导出 / 打印 PDF
        </button>
      </div>
    </div>

    <!-- 时间轴空状态 -->
    <div v-if="filteredHistory.length === 0" class="card empty-timeline">
      <div class="empty-icon">⏳</div>
      <div class="empty-text">暂无相关的病历记录。请在首页或各模块中提交生成。</div>
    </div>

    <!-- 纵向时间轴 -->
    <div v-else class="timeline-container">
      <div
        v-for="entry in filteredHistory"
        :key="entry.id"
        class="timeline-item"
      >
        <div class="timeline-badge" :class="badgeClass(entry.type)">
          {{ typeIcon(entry.type) }}
        </div>

        <div class="timeline-content card">
          <div class="item-header">
            <span class="item-type-tag">{{ typeLabel(entry.type) }}</span>
            <span class="item-date">{{ formatDate(entry.date) }}</span>
          </div>

          <div class="item-summary serif">{{ entry.summary }}</div>

          <div v-if="entry.data" class="item-actions">
            <button class="btn btn-sm" @click="toggleExpand(entry.id)">
              {{ expandedMap[entry.id] ? '▲ 收起详情' : '▼ 查看详情' }}
            </button>
          </div>

          <!-- 展开详情 — 结构化展示 -->
          <div v-if="expandedMap[entry.id] && entry.data" class="expanded-detail">

            <!-- 报告类型：结构化展示 -->
            <template v-if="entry.type === 'report' && entry.data">
              <!-- 基本信息 -->
              <div v-if="entry.data.patient" class="detail-section">
                <div class="detail-section-title">📋 患者信息</div>
                <div class="detail-kv-grid">
                  <div class="kv-item"><span class="kv-k">年龄</span><span class="kv-v">{{ entry.data.patient.age || '—' }}</span></div>
                  <div class="kv-item"><span class="kv-k">性别</span><span class="kv-v">{{ entry.data.patient.sex === 'F' ? '女' : '男' }}</span></div>
                  <div class="kv-item"><span class="kv-k">体重</span><span class="kv-v">{{ entry.data.patient.weight_kg || '—' }} kg</span></div>
                  <div class="kv-item"><span class="kv-k">身高</span><span class="kv-v">{{ entry.data.patient.height_cm || '—' }} cm</span></div>
                </div>
              </div>

              <!-- 证型 -->
              <div v-if="entry.data.syndrome_result" class="detail-section">
                <div class="detail-section-title">🔮 辨证结果</div>
                <div class="syndrome-chips">
                  <span class="syndrome-chip primary-syn">{{ entry.data.syndrome_result.primary }}</span>
                  <span v-for="s in (entry.data.syndrome_result.ranked || []).slice(1, 4)" :key="s" class="syndrome-chip">{{ s }}</span>
                </div>
              </div>

              <!-- 组方 -->
              <div v-if="entry.data.dosage_result?.prescription" class="detail-section">
                <div class="detail-section-title">💊 组方清单（{{ entry.data.dosage_result.base_formula?.name }}）</div>
                <div class="mini-herb-list">
                  <div v-for="h in entry.data.dosage_result.prescription" :key="h.herb" class="mini-herb-item">
                    <span class="herb-role" :class="'role-' + h.role">{{ h.role }}</span>
                    <span class="herb-name">{{ h.herb }}</span>
                    <span class="herb-dose">{{ h.dose_g }}g</span>
                    <span v-if="h.is_yshy" class="yshy-mini">🌿</span>
                  </div>
                </div>
                <div class="herb-total">合计 {{ entry.data.dosage_result.total_g }}g · {{ entry.data.dosage_result.signoff }}</div>
              </div>

              <!-- 指标异常 -->
              <div v-if="entry.data.lab_result?.indicators?.length" class="detail-section">
                <div class="detail-section-title">📊 异常指标 ({{ entry.data.lab_result.abnormal_count }} 项)</div>
                <div class="mini-indicators">
                  <span v-for="ind in entry.data.lab_result.indicators.filter(i => i.grade > 0)" :key="ind.name_raw"
                        class="mini-ind" :class="'g' + ind.grade">
                    {{ ind.name_raw }} {{ ind.value }}{{ ind.unit }} (G{{ ind.grade }})
                  </span>
                </div>
              </div>

              <!-- 安全状态 -->
              <div v-if="entry.data.toxicology?.conclusion" class="detail-section">
                <div class="detail-section-title">🛡️ 安全鉴定</div>
                <div :class="entry.data.toxicology.conclusion.pass ? 'safe-pass' : 'safe-fail'">
                  {{ entry.data.toxicology.conclusion.pass ? '✅ 全部通过' : '⚠️ 存在风险' }}
                  — {{ entry.data.toxicology.conclusion.text }}
                </div>
              </div>
            </template>

            <!-- 非报告类型：简洁的 key-value 展示 -->
            <template v-else>
              <div class="detail-kv-grid">
                <div v-for="(val, key) in flattenData(entry.data)" :key="key" class="kv-item">
                  <span class="kv-k">{{ key }}</span>
                  <span class="kv-v">{{ truncateVal(val) }}</span>
                </div>
              </div>
            </template>

            <!-- 折叠式原始 JSON（高级用户） -->
            <details class="raw-json-details">
              <summary>📄 查看原始 JSON 数据</summary>
              <pre class="json-preview">{{ JSON.stringify(entry.data, null, 2) }}</pre>
            </details>
          </div>
        </div>
      </div>
    </div>

    <div class="page-footer-actions">
      <router-link to="/" class="btn">◀ 返回首页</router-link>
      <router-link to="/report" class="btn btn-primary">查看当前组方 ➔</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { usePatientStore } from '../store/patient'

const store = usePatientStore()

const activeType = ref('all')
const expandedMap = ref({})

const types = [
  { key: 'all', label: '全部记录' },
  { key: 'report', label: '💊 调理组方' },
  { key: 'lab', label: '📋 体检报告' },
  { key: 'tongue', label: '👅 舌面诊' },
  { key: 'symptom', label: '📝 四诊问诊' },
]

const filteredHistory = computed(() => {
  if (activeType.value === 'all') return store.history
  return store.history.filter((h) => h.type === activeType.value)
})

function typeIcon(t) {
  if (t === 'report') return '💊'
  if (t === 'lab') return '📋'
  if (t === 'tongue') return '👅'
  if (t === 'symptom') return '📝'
  return '📜'
}

function typeLabel(t) {
  if (t === 'report') return '调理组方方案'
  if (t === 'lab') return '体检报告录入'
  if (t === 'tongue') return '舌面诊采集'
  if (t === 'symptom') return '智能问诊'
  return '健康记录'
}

function badgeClass(t) {
  if (t === 'report') return 'badge-report'
  if (t === 'lab') return 'badge-lab'
  return 'badge-default'
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString()
}

function toggleExpand(id) {
  expandedMap.value[id] = !expandedMap.value[id]
}

/** 将嵌套对象扁平化为单层 key-value（最多展示 20 个字段） */
function flattenData(obj, prefix = '', result = {}, depth = 0) {
  if (depth > 2 || Object.keys(result).length > 20) return result
  for (const [k, v] of Object.entries(obj || {})) {
    const fullKey = prefix ? `${prefix}.${k}` : k
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      flattenData(v, fullKey, result, depth + 1)
    } else {
      result[fullKey] = v
    }
    if (Object.keys(result).length >= 20) break
  }
  return result
}

function truncateVal(v) {
  const s = Array.isArray(v) ? JSON.stringify(v) : String(v ?? '—')
  return s.length > 80 ? s.slice(0, 77) + '...' : s
}

import { exportToWord, exportToPDF } from '../utils/exportDoc'

function handleExportPDF() {
  exportToPDF()
}

function handleExportWord() {
  let html = `<div class="meta-box"><p><strong>患者姓名/账号：</strong>${store.patient?.name || '默认档案'}</p><p><strong>导出时间：</strong>${new Date().toLocaleString()}</p></div>`
  
  store.history.forEach((h, idx) => {
    html += `<h2>记录 ${idx + 1}：${h.summary}</h2>`
    html += `<p><strong>时间：</strong>${formatDate(h.date)} | <strong>类型：</strong><span class="badge">${typeLabel(h.type)}</span></p>`
    
    if (h.type === 'report' && h.data?.dosage_result?.prescription) {
      html += `<h3>【${h.data.dosage_result.base_formula?.name || '调理组方'}】</h3>`
      html += `<table><thead><tr><th>配伍</th><th>药材</th><th>克重(g)</th></tr></thead><tbody>`
      h.data.dosage_result.prescription.forEach(p => {
        html += `<tr><td>${p.role}</td><td>${p.herb}</td><td>${p.dose_g}g</td></tr>`
      })
      html += `</tbody></table>`
      html += `<p><strong>合计：</strong>${h.data.dosage_result.total_g}g · ${h.data.dosage_result.signoff || ''}</p>`
    }
  })

  exportToWord(`SoulHealth_病历档案_${Date.now()}`, "SoulHealth 终身中医电子病历档案", html)
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
  margin-bottom: 20px;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 24px;
  padding: 12px 16px;
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.filter-label {
  font-size: 12px;
  color: var(--ink-2);
}
.chip-btn {
  background: var(--bg);
  border: 1px solid var(--line);
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 12px;
  cursor: pointer;
  color: var(--ink);
  transition: all 0.2s;
}
.chip-btn.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.export-actions {
  display: flex;
  gap: 8px;
}

.empty-timeline {
  text-align: center;
  padding: 40px;
  color: var(--ink-2);
}
.empty-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.timeline-container {
  position: relative;
  padding-left: 28px;
  margin-bottom: 30px;
}
.timeline-container::before {
  content: '';
  position: absolute;
  left: 11px;
  top: 10px;
  bottom: 10px;
  width: 2px;
  background: var(--line);
}

.timeline-item {
  position: relative;
  margin-bottom: 18px;
}
.timeline-badge {
  position: absolute;
  left: -28px;
  top: 14px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--card);
  border: 2px solid var(--gold);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  z-index: 2;
}
.badge-report { border-color: var(--primary); }
.badge-lab { border-color: var(--gold); }

.timeline-content {
  padding: 14px 16px;
}
.item-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.item-type-tag {
  font-size: 11px;
  background: var(--gold-tint);
  color: var(--primary-deep);
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}
.item-date {
  font-size: 12px;
  color: var(--ink-3);
}

.item-summary {
  font-size: 15px;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 10px;
}

.expanded-detail {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed var(--line);
}

/* 结构化详情 */
.detail-section {
  margin-bottom: 14px;
}
.detail-section-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--primary-deep);
  margin-bottom: 6px;
}
.detail-kv-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 6px;
}
.kv-item {
  display: flex;
  flex-direction: column;
  padding: 6px 10px;
  background: var(--bg);
  border-radius: var(--radius-sm);
}
.kv-k {
  font-size: 11px;
  color: var(--ink-3);
}
.kv-v {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  word-break: break-all;
}

.syndrome-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.syndrome-chip {
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 12px;
  background: var(--bg);
  border: 1px solid var(--line);
  color: var(--ink);
}
.primary-syn {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
  font-weight: 700;
}

.mini-herb-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.mini-herb-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  font-size: 12px;
}
.herb-role {
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 10px;
  color: #fff;
  font-weight: 700;
}
.role-君 { background: #A6402E; }
.role-臣 { background: var(--primary); }
.role-佐 { background: var(--gold); }
.role-使 { background: var(--ink-3); }
.herb-name { font-weight: 600; }
.herb-dose { color: var(--primary); font-weight: 700; }
.yshy-mini { font-size: 10px; }
.herb-total {
  margin-top: 6px;
  font-size: 12px;
  color: var(--ink-2);
}

.mini-indicators {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.mini-ind {
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11px;
}
.g1 { background: rgba(255, 193, 7, 0.2); color: #8a6400; }
.g2 { background: rgba(255, 152, 0, 0.2); color: var(--alert); }
.g3 { background: rgba(244, 67, 54, 0.2); color: var(--danger); }

.safe-pass {
  font-size: 13px;
  color: var(--ok);
  font-weight: 600;
}
.safe-fail {
  font-size: 13px;
  color: var(--danger);
  font-weight: 600;
}

/* 折叠式原始 JSON */
.raw-json-details {
  margin-top: 12px;
}
.raw-json-details summary {
  cursor: pointer;
  font-size: 12px;
  color: var(--ink-3);
  padding: 4px 0;
}
.raw-json-details summary:hover {
  color: var(--primary);
}
.json-preview {
  background: var(--bg);
  padding: 10px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  max-height: 240px;
  overflow: auto;
  color: var(--ink);
  margin-top: 6px;
}

.page-footer-actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 30px;
}
</style>
