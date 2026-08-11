<template>
  <div class="page-container">
    <div class="page-header">
      <div class="serif page-title">📜 调理组方与四维全维度溯源报告</div>
      <div class="page-desc">
        结合体检指标异常分级、舌面诊量化特征与十七/二十维问诊结果，由 8 大引擎推演得出。
      </div>
    </div>

    <!-- 一键生成/重新生成按钮条 -->
    <div class="action-top-bar card">
      <div class="bar-info">
        <span v-if="store.report" class="status-chip ok-chip">
          ✓ 已生成方案 ({{ formatTime(store.report.generated_at) }})
        </span>
        <span v-else class="status-chip warn-chip">⚠️ 尚未生成调理报告</span>
      </div>
      <div class="btn-group">
        <button v-if="store.report" class="btn btn-sm" @click="exportReportWord">
          📄 导出 Word 报告
        </button>
        <button v-if="store.report" class="btn btn-sm" @click="exportReportPDF">
          🖨️ 导出 / 打印 PDF
        </button>
        <button class="btn btn-primary" :disabled="generating" @click="generateReport">
          <span v-if="generating">⚡ 8大引擎推演中...</span>
          <span v-else>{{ store.report ? '🔄 重新推演生成方案' : '⚡ 立即生成四维方案' }}</span>
        </button>
      </div>
    </div>

    <div v-if="errorMessage" class="card error-card">
      <div class="error-title">❌ 生成方案失败</div>
      <div class="error-desc">{{ errorMessage }}</div>
    </div>

    <div v-if="!store.report && !generating" class="card empty-report-card">
      <div class="empty-icon">🔮</div>
      <div class="empty-title serif">点击上方"立即生成四维方案"</div>
      <div class="empty-desc">系统将串联 8 大引擎生成包含权威溯源在内的 10 项结构化分析报告。</div>
    </div>

    <div v-if="generating" class="card loading-report-card">
      <div class="pulse-ring"></div>
      <div class="loading-text serif">8 大引擎协同推演中...</div>
      <div class="loading-sub">体检分级(G0-G3) → 证型辩证 → 0.1g剂量微调 → 中西药冲突筛查 → 四维解释合成</div>
    </div>

    <!-- ===== 报告内容 (已生成) ===== -->
    <div v-if="store.report && !generating" class="report-content-body">

      <!-- BLOCKED 安全拦截 -->
      <div v-if="store.report.dosage_result?.status === 'BLOCKED'" class="card blocked-card">
        <div class="blocked-header">
          <span class="blocked-icon">🚫</span>
          <div class="blocked-title serif">
            {{ store.report.dosage_result?.blocked_title || '安全高风险拦截' }}
          </div>
        </div>
        <div class="blocked-reason"><strong>拦截原因：</strong>{{ store.report.dosage_result?.reason || store.report.dosage_result?.signoff }}</div>
        <div class="blocked-advice"><strong>下一步：</strong>建议前往线下三甲医院中医科，由执业中医师面诊开方。</div>
      </div>

      <!-- ===== OK 状态 ===== -->
      <template v-else>
        <!-- ① 用户概况 -->
        <div class="card section-card">
          <div class="card-section-header"><span class="section-num">①</span><span class="serif section-name">用户身体概况卡片</span></div>
          <div class="sub-block">
            <div class="sub-title">体检异常指标摘要 ({{ store.report.lab_result?.abnormal_count || 0 }} 项异常)</div>
            <div v-if="!store.report.lab_result?.indicators?.length" class="no-anomaly">各项指标均在参考范围内或未录入。</div>
            <div v-else class="anomaly-chips">
              <div v-for="ind in store.report.lab_result.indicators" :key="ind.name_raw" class="anomaly-chip" :class="gradeClass(ind.grade)">
                <span class="ind-name">{{ ind.name_raw }}</span>
                <span class="ind-val">{{ ind.value }} {{ ind.unit }}</span>
                <span class="ind-grade-tag">{{ gradeTagText(ind.grade) }}</span>
              </div>
            </div>
          </div>
          <div class="sub-block">
            <div class="sub-title">中医证型分布占比</div>
            <div class="syndrome-summary">
              <span class="syndrome-primary">主证型：<strong>{{ store.report.syndrome_result?.primary }}</strong></span>
              <span v-if="store.report.syndrome_result?.ranked?.length > 1" class="syndrome-secondary">
                兼夹：{{ store.report.syndrome_result.ranked.slice(1, 3).join('、') }}
              </span>
            </div>
            <div ref="radarChartRef" class="radar-chart-box"></div>
          </div>
        </div>

        <!-- ② 精准组方清单 -->
        <div class="card section-card">
          <div class="card-section-header">
            <span class="section-num">②</span><span class="serif section-name">精准组方清单</span>
            <span class="formula-name">【{{ store.report.dosage_result?.base_formula?.name }} · {{ store.report.dosage_result?.base_formula?.book }}】</span>
          </div>
          <div v-if="store.report.drug_interaction?.conflicts?.length" class="conflict-warning-banner">
            <span class="warn-icon">⚠</span>
            <div class="warn-content">
              <div class="warn-headline">检测到中西药禁忌冲突：</div>
              <div v-for="(c, i) in store.report.drug_interaction.conflicts" :key="i" class="conf-item">
                「{{ c.herb }}」× 西药「{{ c.drug }}」→ <strong>{{ c.consequence }}</strong>
              </div>
            </div>
          </div>
          <div class="herb-table-wrapper">
            <table class="herb-table">
              <thead><tr><th>配伍</th><th>药材</th><th>剂量</th><th>属性</th></tr></thead>
              <tbody>
                <tr v-for="(h, i) in store.report.dosage_result?.prescription" :key="i">
                  <td><span class="role-badge" :class="roleBadgeClass(h.role)">{{ h.role }}</span></td>
                  <td class="herb-name">{{ h.herb }}</td>
                  <td class="herb-dose">{{ h.dose_g }} g</td>
                  <td><span v-if="h.is_yshy" class="yshy-tag">🌿 药食同源</span><span v-else class="normal-herb-tag">常规中药</span></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="prescription-footer">
            <div>共 {{ store.report.dosage_result?.prescription?.length }} 味，合计 <strong>{{ store.report.dosage_result?.total_g }} g</strong></div>
            <div class="signoff-note">{{ store.report.dosage_result?.signoff }}</div>
          </div>
        </div>

        <!-- ③ 宏观中医配伍原理 (维度一) — 从 markdown.explain 渲染 -->
        <div class="card section-card">
          <div class="card-section-header"><span class="section-num">③</span><span class="serif section-name">宏观中医配伍原理</span></div>
          <div class="markdown-body" v-html="renderSection(store.report.markdown?.explain, '维度一', '维度二')"></div>
        </div>

        <!-- ④ 微观临床医学作用机制 (维度二) -->
        <div class="card section-card">
          <div class="card-section-header"><span class="section-num">④</span><span class="serif section-name">微观临床医学作用机制</span></div>
          <div class="markdown-body" v-html="renderSection(store.report.markdown?.explain, '维度二', '维度三')"></div>
        </div>

        <!-- ⑤ 每一味药材克重计算依据 (维度三) -->
        <div class="card section-card">
          <div class="card-section-header"><span class="section-num">⑤</span><span class="serif section-name">每一味药材克重计算依据</span></div>
          <div class="markdown-body" v-html="renderSection(store.report.markdown?.explain, '维度三', '维度四')"></div>
        </div>

        <!-- ⑥ 反向排除说明 (维度四) -->
        <div class="card section-card">
          <div class="card-section-header"><span class="section-num">⑥</span><span class="serif section-name">反向排除说明</span></div>
          <div class="markdown-body" v-html="renderSection(store.report.markdown?.explain, '维度四', '溯源附录')"></div>
        </div>

        <!-- ⑦ 毒理安全鉴定报告 — 从后端 toxicology 读取 -->
        <div class="card section-card">
          <div class="card-section-header"><span class="section-num">⑦</span><span class="serif section-name">毒理安全鉴定报告</span></div>
          <div class="toxicology-conclusion">
            <span :class="store.report.toxicology?.conclusion?.pass ? 'tox-pass' : 'tox-fail'">
              {{ store.report.toxicology?.conclusion?.pass ? '✅ 全部通过' : '⚠️ 存在风险' }}
            </span>
            <span class="tox-text">{{ store.report.toxicology?.conclusion?.text }}</span>
          </div>
          <div class="markdown-body" v-html="renderMarkdown(store.report.markdown?.toxicology)"></div>
        </div>

        <!-- ⑧ 权威溯源附录 — 从 explain 的溯源附录段落 -->
        <div class="card section-card">
          <div class="card-section-header"><span class="section-num">⑧</span><span class="serif section-name">权威溯源附录</span></div>
          <div class="markdown-body" v-html="renderSection(store.report.markdown?.explain, '溯源附录', null)"></div>
        </div>

        <!-- ⑨ 服用方法 & 调理周期 — 从后端 dosage_result.usage -->
        <div class="card section-card">
          <div class="card-section-header"><span class="section-num">⑨</span><span class="serif section-name">服用方法 & 调理周期</span></div>
          <div class="usage-box">
            <div v-if="store.report.dosage_result?.usage" class="usage-row">{{ store.report.dosage_result.usage }}</div>
            <div v-else class="usage-row">水煎服，每日 1 剂，早晚饭后 30 分钟温服。建议 7 天为 1 疗程。</div>
          </div>
        </div>

        <!-- ⑩ 生活干预方案 — 从后端 markdown.lifestyle -->
        <div class="card section-card">
          <div class="card-section-header"><span class="section-num">⑩</span><span class="serif section-name">个人专属生活干预方案</span></div>
          <div class="lifestyle-tabs">
            <button v-for="tab in lifestyleTabs" :key="tab.key" class="lifestyle-tab-btn" :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
              {{ tab.label }}
            </button>
          </div>
          <div class="markdown-body" v-html="renderMarkdown(store.report.markdown?.lifestyle)"></div>
        </div>
      </template>
    </div>

    <div class="page-footer-actions">
      <router-link to="/questionnaire" class="btn">◀ 返回智能问诊</router-link>
      <router-link to="/timeline" class="btn btn-primary">查看终身病历时间轴 ➔</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { usePatientStore } from '../store/patient'
import { api } from '../api'
import { marked } from 'marked'
import * as echarts from 'echarts'
import { exportToWord, exportToPDF } from '../utils/exportDoc'

function exportReportPDF() {
  exportToPDF()
}

function exportReportWord() {
  const rep = store.report
  if (!rep) return

  let html = `
    <div class="meta-box">
      <p><strong>主证型：</strong>${rep.syndrome_result?.primary || '辩证组方'}</p>
      <p><strong>生成时间：</strong>${new Date(rep.generated_at).toLocaleString()}</p>
    </div>
    <h2>一、调理组方清单</h2>
    <h3>【${rep.dosage_result?.base_formula?.name || '定制组方'}】</h3>
    <table>
      <thead><tr><th>配伍</th><th>药材名称</th><th>精准剂量(g)</th><th>分类</th></tr></thead>
      <tbody>
  `

  rep.dosage_result?.prescription?.forEach(item => {
    html += `<tr><td>${item.role}</td><td>${item.herb}</td><td>${item.dose_g}g</td><td>${item.is_yshy ? '药食同源' : '常规中药'}</td></tr>`
  })

  html += `
      </tbody>
    </table>
    <p><strong>合计克重：</strong>${rep.dosage_result?.total_g || 0}g</p>
    <p><strong>服用说明：</strong>${rep.dosage_result?.signoff || ''}</p>
    <h2>二、四维全维度解读</h2>
  `

  if (rep.markdown?.explain) {
    html += `<h3>1. 宏观中医配伍原理</h3><div>${marked.parse(rep.markdown.explain)}</div>`
  }
  if (rep.markdown?.toxicology) {
    html += `<h3>2. 毒理学与中西药相互作用</h3><div>${marked.parse(rep.markdown.toxicology)}</div>`
  }
  if (rep.markdown?.lifestyle) {
    html += `<h3>3. 生活方式与食疗指导</h3><div>${marked.parse(rep.markdown.lifestyle)}</div>`
  }

  exportToWord(`SoulHealth_调理组方报告_${Date.now()}`, "SOULHEALTH 四维全维度调理报告", html)
}

const store = usePatientStore()
const generating = ref(false)
const errorMessage = ref('')
const radarChartRef = ref(null)
const activeTab = ref('all')
let chartInstance = null

const lifestyleTabs = [
  { key: 'all', label: '📋 完整方案' },
]

onMounted(() => { if (store.report) nextTick(() => renderRadarChart()) })
watch(() => store.report, (v) => { if (v) nextTick(() => renderRadarChart()) })

async function generateReport() {
  generating.value = true
  errorMessage.value = ''
  try {
    const res = await api.fullReport(store.payload)
    store.setReport(res)
  } catch (err) {
    errorMessage.value = err.message || '后端服务不可达，请确认 uvicorn 已在 8000 端口启动。'
  } finally {
    generating.value = false
  }
}

function renderRadarChart() {
  if (!radarChartRef.value) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(radarChartRef.value)
  const pct = store.report?.syndrome_result?.percent || {}
  const keys = Object.keys(pct)
  const values = Object.values(pct)
  if (!keys.length) return
  chartInstance.setOption({
    radar: {
      indicator: keys.map(k => ({ name: k, max: 100 })),
      splitNumber: 4,
      axisName: { color: '#2D5F4B', fontWeight: 'bold', fontSize: 11 },
      splitArea: { areaStyle: { color: ['rgba(201,168,108,0.05)', 'rgba(45,95,75,0.05)'] } },
    },
    series: [{
      name: '证型占比', type: 'radar',
      data: [{ value: values, name: '%',
        areaStyle: { color: 'rgba(45,95,75,0.35)' },
        lineStyle: { color: '#2D5F4B', width: 2 },
        itemStyle: { color: '#C9A86C' },
      }],
    }],
  })
}

function renderMarkdown(content) {
  if (!content) return '<p style="color:var(--ink-3)">（后端未返回此段内容）</p>'
  try { return marked.parse(content) } catch { return content }
}

/** 从完整 markdown 中按"维度X"关键词截取对应段落 */
function renderSection(fullMd, startKey, endKey) {
  if (!fullMd) return '<p style="color:var(--ink-3)">（后端未返回此段内容）</p>'
  const lines = fullMd.split('\n')
  let collecting = false
  let result = []
  for (const line of lines) {
    if (line.includes(startKey)) { collecting = true }
    if (endKey && collecting && line.includes(endKey)) { break }
    if (collecting) result.push(line)
  }
  if (result.length === 0) {
    // 如果没有按维度分段，返回全部
    return renderMarkdown(fullMd)
  }
  return renderMarkdown(result.join('\n'))
}

function formatTime(iso) { return iso ? new Date(iso).toLocaleString() : '' }
function gradeClass(g) { return g === 3 ? 'g3-danger' : g === 2 ? 'g2-alert' : g === 1 ? 'g1-warn' : 'g0-ok' }
function gradeTagText(g) { return g === 3 ? 'G3 重度' : g === 2 ? 'G2 中度' : g === 1 ? 'G1 轻度' : 'G0 正常' }
function roleBadgeClass(r) { return r === '君' ? 'role-jun' : r === '臣' ? 'role-chen' : r === '佐' ? 'role-zuo' : 'role-shi' }
</script>

<style scoped>
.page-container { max-width: 860px; margin: 0 auto; padding: 20px 16px 90px; }
.page-title { font-size: 22px; color: var(--primary-deep); margin-bottom: 6px; }
.page-desc { font-size: 14px; color: var(--ink-2); margin-bottom: 20px; }

.action-top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding: 14px 18px; }
.ok-chip { background: rgba(76,175,80,0.15); color: var(--ok); padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; }
.warn-chip { background: var(--gold-tint); color: var(--primary-deep); padding: 4px 12px; border-radius: 20px; font-size: 13px; }

.error-card { border-color: var(--danger); background: rgba(244,67,54,0.05); margin-bottom: 20px; }
.error-title { font-weight: 700; color: var(--danger); }
.error-desc { font-size: 13px; color: var(--ink-2); margin-top: 4px; }

.empty-report-card { text-align: center; padding: 50px 20px; margin-bottom: 30px; }
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-title { font-size: 18px; color: var(--primary-deep); margin-bottom: 8px; }
.empty-desc { font-size: 13px; color: var(--ink-2); }

.loading-report-card { text-align: center; padding: 50px 20px; margin-bottom: 30px; }
.pulse-ring { width: 48px; height: 48px; border-radius: 50%; background: var(--primary); margin: 0 auto 16px; animation: pulse 1.5s infinite ease-in-out; }
@keyframes pulse { 0% { transform: scale(0.8); opacity: 0.5; } 50% { transform: scale(1.1); opacity: 1; } 100% { transform: scale(0.8); opacity: 0.5; } }
.loading-text { font-size: 18px; color: var(--primary-deep); margin-bottom: 8px; }
.loading-sub { font-size: 12px; color: var(--ink-2); }

.report-content-body { display: flex; flex-direction: column; gap: 20px; }

.blocked-card { border: 2px solid var(--danger); background: rgba(244,67,54,0.04); }
.blocked-header { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.blocked-icon { font-size: 32px; }
.blocked-title { font-size: 18px; color: var(--danger); font-weight: 700; }
.blocked-reason, .blocked-advice { font-size: 14px; line-height: 1.6; margin-bottom: 10px; }

.section-card { position: relative; }
.card-section-header { display: flex; align-items: center; gap: 10px; border-bottom: 1px solid var(--line); padding-bottom: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.section-num { width: 24px; height: 24px; background: var(--primary); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }
.section-name { font-size: 17px; color: var(--primary-deep); }
.formula-name { font-size: 12px; color: var(--gold); margin-left: auto; font-weight: 600; }

.sub-block { margin-bottom: 16px; }
.sub-title { font-size: 13px; color: var(--ink-2); font-weight: 700; margin-bottom: 8px; }
.no-anomaly { font-size: 13px; color: var(--ink-3); }

.anomaly-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.anomaly-chip { display: flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 6px; font-size: 12px; }
.g0-ok { background: rgba(76,175,80,0.1); color: var(--ok); }
.g1-warn { background: rgba(255,193,7,0.2); color: #8a6400; }
.g2-alert { background: rgba(255,152,0,0.2); color: var(--alert); }
.g3-danger { background: rgba(244,67,54,0.2); color: var(--danger); }
.ind-name { font-weight: 600; }
.ind-grade-tag { font-size: 10px; opacity: 0.8; }

.syndrome-summary { font-size: 14px; margin-bottom: 12px; }
.syndrome-primary { color: var(--primary-deep); margin-right: 14px; }
.syndrome-secondary { color: var(--ink-2); }
.radar-chart-box { width: 100%; height: 280px; }

.conflict-warning-banner { display: flex; gap: 12px; background: rgba(244,67,54,0.1); border: 1px solid var(--danger); padding: 12px 16px; border-radius: var(--radius-sm); margin-bottom: 16px; color: var(--danger); }
.warn-icon { font-size: 20px; }
.warn-headline { font-weight: 700; margin-bottom: 4px; }
.conf-item { font-size: 13px; }

.herb-table-wrapper { overflow-x: auto; margin-bottom: 16px; }
.herb-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.herb-table th { background: var(--bg); color: var(--ink-2); text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--line); font-weight: 600; }
.herb-table td { padding: 10px 12px; border-bottom: 1px dashed var(--line); }
.role-badge { padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 700; color: #fff; }
.role-jun { background: #A6402E; }
.role-chen { background: var(--primary); }
.role-zuo { background: var(--gold); }
.role-shi { background: var(--ink-3); }
.herb-name { font-weight: 700; }
.herb-dose { font-size: 16px; font-weight: 700; color: var(--primary-deep); font-family: var(--font-display); }
.yshy-tag { background: rgba(76,175,80,0.15); color: var(--ok); padding: 2px 8px; border-radius: 12px; font-size: 11px; }
.normal-herb-tag { font-size: 11px; color: var(--ink-3); }
.prescription-footer { display: flex; justify-content: space-between; align-items: center; padding-top: 10px; border-top: 1px solid var(--line); font-size: 14px; }
.signoff-note { font-size: 12px; color: var(--ink-3); }

.toxicology-conclusion { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; font-size: 14px; }
.tox-pass { color: var(--ok); font-weight: 700; }
.tox-fail { color: var(--danger); font-weight: 700; }
.tox-text { color: var(--ink-2); }

.usage-box { background: var(--bg); padding: 14px; border-radius: var(--radius-sm); font-size: 14px; }

.lifestyle-tabs { display: flex; gap: 8px; margin-bottom: 12px; }
.lifestyle-tab-btn { flex: 1; padding: 8px; border-radius: var(--radius-sm); border: 1px solid var(--line); background: var(--bg); cursor: pointer; font-size: 13px; color: var(--ink-2); }
.lifestyle-tab-btn.active { background: var(--primary); color: #fff; border-color: var(--primary); font-weight: 600; }

.markdown-body { font-size: 14px; line-height: 1.7; color: var(--ink); }
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { color: var(--primary-deep); margin: 16px 0 8px; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 20px; }
.markdown-body :deep(strong) { color: var(--primary); }

.page-footer-actions { display: flex; justify-content: space-between; gap: 12px; margin-top: 30px; }
</style>
