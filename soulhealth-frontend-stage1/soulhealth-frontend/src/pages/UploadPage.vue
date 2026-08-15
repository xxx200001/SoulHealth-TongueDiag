<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const pid = computed(() => route.query.pid)
const patient = ref(null)
const snapshot = ref(null)
const docList = ref([])
const uploadCount = ref(0)
const uploading = ref(false)
const errorMsg = ref('')

// 备注
const note = ref('')

const sexText = (s) => s === 'female' ? '女' : s === 'male' ? '男' : '—'

async function loadSnapshot() {
  if (!pid.value) return
  try {
    const s = await api.getPatient(auth.token, pid.value)
    snapshot.value = s
    patient.value = s.patient
  } catch (e) { errorMsg.value = e.message }
}

// ── 图片上传（视觉模型自动抽取）──
async function handleFiles(files) {
  if (!pid.value) return
  uploading.value = true
  for (const f of files) {
    try {
      const fd = new FormData()
      fd.append('file', f)
      fd.append('patient_id', pid.value)
      const r = await api.uploadDocument(auth.token, fd)
      r.source_filename = f.name
      docList.value.push(r)
      uploadCount.value++
    } catch (e) { errorMsg.value = `${f.name}: ${e.message}` }
  }
  uploading.value = false
  await loadSnapshot()
}

// ── 备注 ──
async function saveNote() {
  if (!note.value.trim()) return
  try {
    await api.addNote(auth.token, pid.value, note.value.trim())
    note.value = ''
    await loadSnapshot()
  } catch (e) { errorMsg.value = e.message }
}

function goAnalysis() { router.push(`/analysis?pid=${pid.value}`) }
function goLab() { router.push('/lab') }
function goProfile() { router.push('/profile') }

function onDrop(e) { e.preventDefault(); handleFiles([...e.dataTransfer.files]) }
function onDragover(e) { e.preventDefault() }

onMounted(() => {
  if (!pid.value) { router.push('/archive'); return }
  loadSnapshot()
})
</script>

<template>
  <div v-if="patient">
    <!-- 当前患者横幅 -->
    <div class="patient-banner">
      <b>{{ patient.name || patient.pseudonym }}</b>
      <span>{{ sexText(patient.sex) }} · {{ patient.age_years ?? '—' }} 岁 · {{ patient.pseudonym }}</span>
      <div class="banner-actions">
        <button class="btn btn-ghost btn-sm" @click="goProfile">补充个人信息</button>
        <button class="btn btn-primary btn-sm" @click="goAnalysis">→ AI 智能分析</button>
      </div>
    </div>

    <!-- 图片上传 -->
    <section class="card">
      <h3 class="serif">📄 上传报告图片</h3>
      <p class="desc">上传化验单 / 超声报告图片，AI 视觉模型自动提取指标入档。</p>
      <div class="dropzone" @drop="onDrop" @dragover="onDragover" @click="$refs.fileInput.click()">
        <input ref="fileInput" type="file" multiple accept=".jpg,.jpeg,.png,.webp,.pdf" hidden @change="e => handleFiles([...e.target.files])" />
        <b>点击或拖入</b> 检查报告图片（超声 / 化验单，jpg·png·pdf）
        <span class="sub">已上传 {{ uploadCount }} 张</span>
      </div>
      <div v-if="uploading" class="hint">上传中…</div>
      <div v-for="(doc, i) in docList" :key="i" class="doc-item">
        ✅ {{ doc.source_filename }} — {{ doc.extraction?.document_type || '已解析' }}
      </div>
      <p class="hint">💡 手动录入化验指标请前往 <a href="#" @click.prevent="goLab">体检上传</a> 页面。</p>
    </section>

    <!-- 备注 -->
    <section class="card">
      <h3 class="serif">📝 补充症状备注</h3>
      <textarea v-model="note" rows="2" placeholder="补充症状描述 / 主诉 / 病史…"></textarea>
      <button class="btn btn-ghost" @click="saveNote">保存备注</button>
    </section>

    <!-- 档案快照 -->
    <section v-if="snapshot" class="card snapshot">
      <h3 class="serif">📋 当前档案快照</h3>
      <div class="chip-row">
        <span v-for="(o, code) in (snapshot.observations_latest || {})" :key="code"
          class="chip" :class="{ hi: o.abnormal_flag === 'H' }">
          {{ o.code }} {{ o.value_num ?? o.value_text }} {{ o.unit || '' }}{{ o.abnormal_flag === 'H' ? '↑' : o.abnormal_flag === 'L' ? '↓' : '' }}
        </span>
        <span v-for="f in (snapshot.findings || [])" :key="f.id" class="chip">
          {{ f.organ }}：{{ (f.flags || []).join('、') || f.description }}
        </span>
        <span v-for="imp in (snapshot.impressions || [])" :key="imp.id" class="chip hi">
          提示：{{ imp.text }}
        </span>
        <span v-if="!Object.keys(snapshot.observations_latest || {}).length && !(snapshot.findings || []).length && !(snapshot.impressions || []).length" class="hint">
          尚无指标数据，请上传报告或前往「体检上传」页手动录入。
        </span>
      </div>
      <p class="hint">
        资料 {{ snapshot.documents?.length || 0 }} 份 · 指标 {{ snapshot.observations_timeline?.length || 0 }} 条 ·
        所见 {{ snapshot.findings?.length || 0 }} 项
      </p>
      <button class="btn btn-primary" @click="goAnalysis">开始 AI 智能分析 →</button>
    </section>

    <div v-if="errorMsg" class="error-toast" @click="errorMsg = ''">{{ errorMsg }}</div>
  </div>
  <div v-else class="hint" style="padding:40px;text-align:center">加载中…</div>
</template>

<style scoped>
.patient-banner { display: flex; align-items: center; gap: 12px; padding: 12px 0; flex-wrap: wrap; }
.patient-banner b { font-size: 16px; }
.patient-banner span { font-size: 13px; color: var(--ink-2); flex: 1; }
.banner-actions { display: flex; gap: 8px; }
.desc { font-size: 13px; color: var(--ink-2); margin: 0 0 10px; }
.dropzone { border: 2px dashed var(--line); border-radius: var(--radius-sm); padding: 24px; text-align: center; cursor: pointer; transition: border-color 0.2s; color: var(--ink-2); font-size: 14px; }
.dropzone:hover { border-color: var(--primary); }
.dropzone .sub { display: block; font-size: 12px; color: var(--ink-3); margin-top: 6px; }
.doc-item { padding: 6px 0; font-size: 13px; color: var(--ink-2); border-bottom: 1px solid var(--line); }
textarea { width: 100%; padding: 8px 10px; border: 1px solid var(--line); border-radius: var(--radius-sm); background: var(--bg); color: var(--ink); font-size: 13px; resize: vertical; margin-bottom: 8px; box-sizing: border-box; }
.chip-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.chip { padding: 3px 10px; border-radius: 999px; font-size: 12px; background: var(--primary-tint); color: var(--ink-2); }
.chip.hi { background: rgba(244,67,54,0.1); color: var(--danger); font-weight: 600; }
.snapshot { border-left: 3px solid var(--primary); }
.error-toast { position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%); background: var(--danger); color: #fff; padding: 8px 20px; border-radius: 8px; font-size: 13px; z-index: 100; cursor: pointer; }
.hint { font-size: 11.5px; color: var(--ink-3); margin: 4px 0; }
.hint a { color: var(--primary); font-weight: 600; text-decoration: none; }
.btn-sm { padding: 6px 14px; font-size: 12px; }
</style>
