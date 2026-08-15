<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const pid = computed(() => route.query.pid)

const question = ref('')
const messages = ref([])
const asking = ref(false)

const esc = (v) => String(v ?? '').replace(/[&<>"']/g,
  (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))

async function ask() {
  const q = question.value.trim()
  if (!q || !pid.value || asking.value) return
  messages.value.push({ type: 'q', text: q })
  question.value = ''
  asking.value = true
  messages.value.push({ type: 'a', text: '思考中…', pending: true })
  await nextTick()
  scrollToBottom()
  try {
    const d = await api.askQuestion(auth.token, pid.value, q)
    // 替换最后一条 pending 消息
    const last = messages.value[messages.value.length - 1]
    last.text = d.answer
    last.disclaimer = d.disclaimer
    last.pending = false
  } catch (e) {
    const last = messages.value[messages.value.length - 1]
    last.text = e.message
    last.pending = false
    last.error = true
  } finally {
    asking.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  const el = document.querySelector('.qa-log')
  if (el) el.scrollTop = el.scrollHeight
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask() }
}

onMounted(() => {
  if (!pid.value) { router.push('/archive'); return }
})
</script>

<template>
  <div>
    <section class="card">
      <div class="card-head">
        <span class="step-no serif">05</span>
        <div><h2>健康问答</h2><p>基于档案数据（含历次分析趋势）AI 真实作答</p></div>
      </div>

      <div class="qa-log" ref="logEl">
        <div v-if="!messages.length" class="qa-empty">
          <p>💬 问我任何关于您健康档案的问题，例如：</p>
          <ul>
            <li>我的肝功能这次和上次比是好转了吗？</li>
            <li>甘油三酯偏高日常饮食该注意什么？</li>
            <li>我的指标异常可能是什么原因导致的？</li>
          </ul>
        </div>
        <template v-for="(msg, i) in messages" :key="i">
          <div v-if="msg.type === 'q'" class="qa-q">{{ msg.text }}</div>
          <div v-else class="qa-a" :class="{ pending: msg.pending, err: msg.error }">
            <template v-if="msg.pending">思考中…</template>
            <template v-else>
              <span v-html="msg.text.replace(/\n/g, '<br>')"></span>
              <div v-if="msg.disclaimer" class="qa-dis">{{ msg.disclaimer }}</div>
            </template>
          </div>
        </template>
      </div>

      <div class="qa-bar">
        <input v-model="question" type="text" maxlength="200"
          placeholder="输入问题…" @keydown="onKeydown" />
        <button class="btn btn-primary" :disabled="asking" @click="ask">提问</button>
      </div>
      <p class="hint">健康科普与生活方式建议，不替代医疗诊断；异常指标请及时就医。</p>
    </section>

    <div class="nav-links">
      <button class="btn btn-ghost" @click="router.push(`/analysis?pid=${pid}`)">← 分析结果</button>
      <button class="btn btn-ghost" @click="router.push(`/upload?pid=${pid}`)">← 补充数据</button>
    </div>
  </div>
</template>

<style scoped>
.card-head { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.step-no { width: 36px; height: 36px; display: grid; place-items: center; border-radius: 50%; background: var(--primary); color: var(--gold); font-size: 13px; font-weight: 700; flex-shrink: 0; }
.card-head h2 { margin: 0; font-size: 16px; }
.card-head p { margin: 0; font-size: 12px; color: var(--ink-2); }
.qa-log { max-height: 420px; overflow-y: auto; padding: 10px; background: var(--bg); border-radius: var(--radius-sm); border: 1px solid var(--line); margin-bottom: 12px; min-height: 200px; }
.qa-empty { text-align: center; color: var(--ink-3); font-size: 13px; padding: 30px 10px; }
.qa-empty ul { list-style: none; padding: 0; margin: 12px 0 0; }
.qa-empty li { padding: 4px 0; color: var(--ink-2); }
.qa-empty li::before { content: '💡 '; }
.qa-q { background: var(--primary); color: #fff; padding: 8px 14px; border-radius: 14px 14px 4px 14px; margin: 6px 0 6px auto; max-width: 80%; width: fit-content; font-size: 13px; }
.qa-a { background: var(--card); border: 1px solid var(--line); padding: 8px 14px; border-radius: 14px 14px 14px 4px; margin: 6px auto 6px 0; max-width: 85%; font-size: 13px; line-height: 1.6; color: var(--ink); }
.qa-a.pending { color: var(--ink-3); font-style: italic; }
.qa-a.err { color: var(--danger); border-color: rgba(244,67,54,0.2); background: rgba(244,67,54,0.04); }
.qa-dis { margin-top: 6px; font-size: 11px; color: var(--ink-3); font-style: italic; border-top: 1px dashed var(--line); padding-top: 4px; }
.qa-bar { display: flex; gap: 8px; }
.qa-bar input { flex: 1; padding: 10px 14px; border: 1px solid var(--line); border-radius: var(--radius-sm); background: var(--bg); color: var(--ink); font-size: 14px; }
.qa-bar input:focus { border-color: var(--primary); outline: none; }
.hint { font-size: 11.5px; color: var(--ink-3); margin: 6px 0 0; }
.nav-links { display: flex; gap: 10px; margin-top: 12px; }
</style>
