<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const pid = computed(() => route.query.pid)

const analyzing = ref(false)
const result = ref(null)
const history = ref([])
const errorMsg = ref('')

const esc = (v) => String(v ?? '')
const fmtTime = (iso) => (iso || '').replace('T', ' ').replace('Z', '').slice(0, 16)

async function runAnalysis() {
  if (analyzing.value || !pid.value) return
  analyzing.value = true; errorMsg.value = ''
  try {
    const d = await api.runAnalysis(auth.token, pid.value)
    result.value = d
    await loadHistory()
  } catch (e) { errorMsg.value = e.message }
  finally { analyzing.value = false }
}

async function loadHistory() {
  try {
    const d = await api.listAnalyses(auth.token, pid.value)
    history.value = d.analyses || []
  } catch {}
}

async function viewAnalysis(aid) {
  try {
    const d = await api.getAnalysis(auth.token, aid)
    result.value = d
  } catch (e) { errorMsg.value = e.message }
}

function downloadUrl(rid) {
  return `/api/reports/${rid}/download?token=${encodeURIComponent(auth.token)}`
}

onMounted(() => {
  if (!pid.value) { router.push('/archive'); return }
  loadHistory()
})
</script>

<template>
  <div>
    <section class="card">
      <div class="card-head">
        <span class="step-no serif">03</span>
        <div><h2>AI 智能分析</h2><p>风险识别 → 知识匹配 → 机制链 → 生物计算，全程留痕</p></div>
      </div>
      <div class="action-bar">
        <button class="btn btn-primary" :disabled="analyzing" @click="runAnalysis">
          {{ analyzing ? 'Agent 分析中…' : '开始智能分析' }}
        </button>
        <button class="btn btn-ghost" @click="router.push(`/qa?pid=${pid}`)">→ 健康问答</button>
        <button class="btn btn-ghost" @click="router.push(`/upload?pid=${pid}`)">← 补充数据</button>
      </div>
      <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
    </section>

    <!-- 历史回放 -->
    <section v-if="history.length" class="card">
      <h3 class="serif">📊 历次分析（点击回放）</h3>
      <div class="history-list">
        <button v-for="a in history" :key="a.id" class="history-item" @click="viewAnalysis(a.id)">
          {{ fmtTime(a.created_at) }} · {{ a.id.slice(0, 8) }} <em>回放 →</em>
        </button>
      </div>
    </section>

    <!-- 分析结果 -->
    <template v-if="result">
      <!-- AI 综合解读 -->
      <section class="card result-block">
        <h3 class="serif">🧠 AI 综合解读</h3>
        <div v-if="result.interpretation?.available" class="interp-text" v-html="renderMd(result.interpretation.text)"></div>
        <div v-else class="hint">{{ result.interpretation?.reason || '本次未生成 AI 综合解读。' }}</div>
      </section>

      <!-- 健康风险 -->
      <section class="card result-block">
        <h3 class="serif">⚠️ 健康风险识别</h3>
        <div class="risk-grid">
          <div v-for="t in (result.risk_tags || [])" :key="t.label" class="risk" :class="t.severity">
            <b>{{ t.label }} · {{ {info:'提示', watch:'关注', high:'建议就医评估'}[t.severity] || '' }}</b>
            <ul><li v-for="(e, i) in t.evidence" :key="i">{{ e }}</li></ul>
          </div>
          <div v-for="s in (result.syndrome_tags || [])" :key="s.label" class="risk syn">
            <b>{{ s.label }} · 自述参考</b>
            <ul><li v-for="(e, i) in s.evidence" :key="i">{{ e }}</li></ul>
          </div>
        </div>
        <p v-if="!(result.risk_tags || []).length && !(result.syndrome_tags || []).length" class="hint">未识别出显著风险标签；建议保持定期体检随访。</p>
      </section>

      <!-- 机制链 -->
      <section class="card result-block">
        <h3 class="serif">🔗 机制解释链</h3>
        <div v-for="l in ((result.mechanism_chain?.levels) || []).filter(l => l.items.length)" :key="l.level" class="chain-level">
          <span class="chain-tag">{{ l.level }}</span>
          <span v-for="(it, i) in l.items" :key="i" class="chain-item">· {{ it }}</span>
        </div>
      </section>

      <!-- 组方 -->
      <section class="card result-block">
        <h3 class="serif">🍵 药食同源组方</h3>
        <template v-if="result.formula?.ingredients?.length">
          <div v-if="result.formula.formula_name" class="formula-head">
            <b>{{ result.formula.formula_name }}</b>
            <span>{{ result.formula.source }}</span>
            <span>治则：{{ result.formula.treatment_principle }}</span>
          </div>
          <table class="tbl">
            <tr><th>原料</th><th>用量</th><th>角色</th><th>要点</th></tr>
            <tr v-for="(ing, i) in result.formula.ingredients" :key="i">
              <td>{{ ing.display }}</td><td>{{ ing.grams }}g</td><td>{{ ing.role }}</td><td>{{ ing.purpose }}</td>
            </tr>
          </table>
        </template>
        <p v-else class="hint">本次未生成代茶饮配方。</p>
      </section>

      <!-- 生物计算 -->
      <section class="card result-block">
        <h3 class="serif">🧬 生物计算辅助</h3>
        <div class="bio-grid">
          <div v-for="(b, i) in (result.biocompute_plan || [])" :key="i" class="bio-item">
            <span class="gene">{{ b.gene }}</span>
            <span class="variant">{{ b.uniprot || b.variant }}</span>
            <template v-if="b.service === 'alphafold_db' && b.status === 'done'">
              <div class="bar"><i :style="{ width: Math.min(b.mean_plddt || 0, 100) + '%' }"></i></div>
              <div>平均 pLDDT <b>{{ b.mean_plddt }}</b></div>
            </template>
            <template v-else-if="b.service === 'evo2' && b.status === 'done'">
              <div>Δ logL <b>{{ b.delta_ll }}</b></div>
            </template>
            <div v-else class="hint">{{ b.note || b.status }}</div>
          </div>
        </div>
        <p v-if="!(result.biocompute_plan || []).length" class="hint">
          {{ result.mechanism_chain?.biocompute_applicability || '本次无生物计算调用。' }}
        </p>
      </section>

      <!-- 报告下载 -->
      <section class="card result-block">
        <h3 class="serif">📑 分析报告</h3>
        <div v-for="r in (result.reports || [])" :key="r.report_id" class="report-item">
          <b>{{ r.title }}</b>
          <a :href="downloadUrl(r.report_id)" target="_blank" class="btn btn-primary btn-sm">下载 {{ r.format === 'docx' ? 'Word' : 'Markdown' }}</a>
        </div>
        <p v-if="!(result.reports || []).length" class="hint">本次分析无报告产物。</p>
      </section>
    </template>
  </div>
</template>

<script>
export default {
  methods: {
    renderMd(t) {
      if (!t) return ''
      let h = t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      h = h.replace(/^#+\s*(.*)$/gm, '<h4>$1</h4>')
      h = h.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      h = h.replace(/\n/g, '<br>')
      return h
    }
  }
}
</script>

<style scoped>
.card-head { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.step-no { width: 36px; height: 36px; display: grid; place-items: center; border-radius: 50%; background: var(--primary); color: var(--gold); font-size: 13px; font-weight: 700; flex-shrink: 0; }
.card-head h2 { margin: 0; font-size: 16px; }
.card-head p { margin: 0; font-size: 12px; color: var(--ink-2); }
.action-bar { display: flex; gap: 10px; flex-wrap: wrap; }
.error-msg { color: var(--danger); font-size: 12px; margin-top: 8px; padding: 6px 10px; background: rgba(244,67,54,0.06); border-radius: var(--radius-sm); }
.history-list { display: flex; flex-wrap: wrap; gap: 6px; }
.history-item { padding: 6px 14px; border: 1px solid var(--line); border-radius: var(--radius-sm); background: var(--bg); cursor: pointer; font-size: 12px; color: var(--ink-2); transition: all 0.15s; }
.history-item:hover { background: var(--primary-tint); border-color: var(--primary); }
.history-item em { color: var(--primary); font-style: normal; font-weight: 600; }
.result-block { border-left: 3px solid var(--primary); }
.risk-grid { display: grid; gap: 10px; }
.risk { padding: 10px 14px; border-radius: var(--radius-sm); background: var(--bg); }
.risk.info { border-left: 3px solid var(--primary); }
.risk.watch { border-left: 3px solid var(--gold); }
.risk.high { border-left: 3px solid var(--danger); }
.risk.syn { border-left: 3px solid #9c27b0; }
.risk b { display: block; font-size: 13px; margin-bottom: 4px; }
.risk ul { margin: 0; padding-left: 18px; font-size: 12px; color: var(--ink-2); }
.chain-level { display: flex; align-items: flex-start; gap: 8px; padding: 6px 0; border-bottom: 1px dashed var(--line); }
.chain-tag { padding: 2px 8px; border-radius: 4px; background: var(--primary-tint); font-size: 11px; font-weight: 700; color: var(--primary-deep); white-space: nowrap; }
.chain-item { font-size: 12px; color: var(--ink-2); }
.formula-head { margin-bottom: 10px; }
.formula-head b { font-size: 15px; margin-right: 8px; }
.formula-head span { font-size: 12px; color: var(--ink-2); margin-right: 12px; }
.tbl { width: 100%; border-collapse: collapse; font-size: 13px; }
.tbl th { background: var(--primary-tint); text-align: left; padding: 6px 10px; font-size: 12px; font-weight: 700; }
.tbl td { padding: 5px 10px; border-bottom: 1px solid var(--line); }
.bio-grid { display: grid; gap: 10px; }
.bio-item { padding: 10px 14px; background: var(--bg); border-radius: var(--radius-sm); border: 1px solid var(--line); }
.gene { font-weight: 700; color: var(--primary-deep); margin-right: 6px; }
.variant { font-size: 12px; color: var(--ink-2); }
.bar { height: 6px; background: var(--line); border-radius: 999px; margin: 6px 0; overflow: hidden; }
.bar i { display: block; height: 100%; background: linear-gradient(90deg, var(--primary), var(--gold)); border-radius: inherit; }
.report-item { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--line); }
.report-item b { font-size: 14px; }
.btn-sm { padding: 6px 14px; font-size: 12px; }
.hint { font-size: 11.5px; color: var(--ink-3); margin: 4px 0; }
.interp-text { font-size: 13px; line-height: 1.7; color: var(--ink); }
.interp-text :deep(h4) { font-size: 14px; margin: 10px 0 4px; color: var(--primary-deep); }
.interp-text :deep(strong) { color: var(--primary-deep); }
</style>
