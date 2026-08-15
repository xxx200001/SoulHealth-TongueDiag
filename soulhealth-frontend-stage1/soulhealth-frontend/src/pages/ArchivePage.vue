<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { api } from '../api'

const router = useRouter()
const auth = useAuthStore()

const search = ref('')
const patients = ref([])
const loading = ref(false)
const creating = ref(false)
const errorMsg = ref('')

// 建档只需姓名 + 身份证后四位（详细信息去「个人信息」页填写）
const name = ref('')
const id4 = ref('')

const sexText = (s) => s === 'female' ? '女' : s === 'male' ? '男' : '—'
const fmtTime = (iso) => (iso || '').replace('T', ' ').replace('Z', '').slice(0, 16)

async function loadPatients() {
  loading.value = true
  try {
    const d = await api.listPatients(auth.token, search.value.trim())
    patients.value = d.patients || []
  } catch (e) { errorMsg.value = e.message }
  finally { loading.value = false }
}

async function createOrFind() {
  if (!name.value.trim()) { errorMsg.value = '请填写姓名'; return }
  creating.value = true; errorMsg.value = ''
  try {
    const d = await api.createPatient(auth.token, {
      name: name.value.trim(),
      id_last4: id4.value.trim() || null,
    })
    // 创建后进入上传页
    router.push(`/upload?pid=${d.patient_id}`)
  } catch (e) { errorMsg.value = e.message }
  finally { creating.value = false }
}

async function loadDemo() {
  name.value = '演示患者'; id4.value = '0000'
  await createOrFind()
}

function selectPatient(pid) {
  router.push(`/upload?pid=${pid}`)
}

let debounceTimer = null
function onSearch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => loadPatients(), 300)
}

onMounted(loadPatients)
</script>

<template>
  <div>
    <!-- 档案检索 -->
    <section class="card">
      <div class="card-head">
        <span class="step-no serif">档</span>
        <div><h2>健康档案</h2><p>按姓名或身份证后四位检索、建立或找回</p></div>
      </div>
      <div class="search-bar">
        <input v-model="search" type="search" placeholder="搜索姓名或身份证后四位…" @input="onSearch" />
        <button class="btn btn-ghost" @click="loadPatients">刷新</button>
      </div>
      <div class="patient-list">
        <div v-if="loading" class="hint">加载中…</div>
        <div v-else-if="!patients.length" class="hint">{{ search ? '未找到匹配档案。' : '尚无档案，请在下方建立。' }}</div>
        <div v-for="p in patients" :key="p.id" class="patient-row" @click="selectPatient(p.id)">
          <div class="pr-main">
            <b>{{ p.name || p.pseudonym }}</b>
            <span>{{ sexText(p.sex) }} · {{ p.age_years ?? '—' }} 岁{{ p.id_last4 ? ` · 尾号${p.id_last4}` : '' }}</span>
          </div>
          <div class="pr-meta">
            指标 {{ p.obs_count ?? 0 }} · 分析 {{ p.analysis_count }}
            <em>{{ fmtTime(p.last_seen_at) }}</em>
          </div>
        </div>
      </div>
    </section>

    <!-- 建档/找回（只需姓名 + 后四位，其他去个人信息页填）-->
    <section class="card">
      <div class="card-head">
        <span class="step-no serif">建</span>
        <div><h2>建立 / 找回档案</h2><p>姓名 + 身份证后四位精确匹配；不填后四位则新建</p></div>
      </div>
      <div class="create-row">
        <label>姓名 <input v-model="name" type="text" placeholder="必填" /></label>
        <label>身份证后四位 <input v-model="id4" type="text" maxlength="4" placeholder="如 1234（选填）" /></label>
      </div>
      <div class="form-actions">
        <button class="btn btn-primary" :disabled="creating" @click="createOrFind">
          {{ creating ? '创建中…' : '建立 / 找回档案' }}
        </button>
        <button class="btn btn-ghost" @click="loadDemo">载入演示患者</button>
      </div>
      <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
      <p class="hint">💡 建档后可在「个人信息」页补充性别、年龄、身高、体重等详细信息。</p>
    </section>
  </div>
</template>

<style scoped>
.search-bar { display: flex; gap: 8px; margin-bottom: 12px; }
.search-bar input { flex: 1; padding: 8px 12px; border: 1px solid var(--line); border-radius: var(--radius-sm); background: var(--bg); color: var(--ink); font-size: 14px; }
.patient-list { max-height: 340px; overflow-y: auto; }
.patient-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; border-bottom: 1px solid var(--line); cursor: pointer; transition: background 0.15s; border-radius: var(--radius-sm); }
.patient-row:hover { background: var(--primary-tint); }
.pr-main { display: flex; flex-direction: column; gap: 2px; }
.pr-main b { font-size: 14px; }
.pr-main span { font-size: 12px; color: var(--ink-2); }
.pr-meta { font-size: 11px; color: var(--ink-3); text-align: right; }
.pr-meta em { display: block; font-style: normal; }
.create-row { display: flex; gap: 14px; margin-bottom: 12px; }
.create-row label { flex: 1; display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--ink-2); font-weight: 600; }
.create-row input { padding: 8px 10px; border: 1px solid var(--line); border-radius: var(--radius-sm); background: var(--bg); color: var(--ink); font-size: 14px; }
.form-actions { display: flex; gap: 10px; margin-bottom: 10px; }
.error-msg { color: var(--danger); font-size: 12px; margin-bottom: 8px; padding: 6px 10px; background: rgba(244,67,54,0.06); border-radius: var(--radius-sm); }
.hint { font-size: 11.5px; color: var(--ink-3); margin: 0; }
.step-no { width: 36px; height: 36px; display: grid; place-items: center; border-radius: 50%; background: var(--primary); color: var(--gold); font-size: 15px; font-weight: 700; flex-shrink: 0; }
.card-head { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.card-head h2 { margin: 0; font-size: 16px; }
.card-head p { margin: 0; font-size: 12px; color: var(--ink-2); }
</style>
