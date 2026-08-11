<template>
  <div class="login-page">
    <div class="login-card">
      <!-- Logo -->
      <div class="login-logo">
        <div class="logo-badge serif">溯源</div>
        <div class="logo-text">
          <div class="logo-title serif">SOULHEALTH</div>
          <div class="logo-subtitle">中医辨证溯源 · AI 全维度诊疗</div>
        </div>
      </div>

      <!-- 切换 Tab -->
      <div class="auth-tabs">
        <button class="auth-tab" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
        <button class="auth-tab" :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
      </div>

      <!-- 表单 -->
      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="form-group">
          <label>手机号 / 账号</label>
          <input v-model="phone" type="tel" placeholder="请输入手机号" maxlength="11" required autocomplete="tel" />
        </div>

        <div v-if="mode === 'register'" class="form-group">
          <label>昵称 (选填)</label>
          <input v-model="nickname" type="text" placeholder="给自己起个名字" maxlength="20" />
        </div>

        <div class="form-group">
          <label>密码</label>
          <div class="password-wrap">
            <input v-model="password" :type="showPw ? 'text' : 'password'" placeholder="请输入密码" minlength="4" required autocomplete="current-password" />
            <button type="button" class="eye-btn" @click="showPw = !showPw">{{ showPw ? '🙈' : '👁' }}</button>
          </div>
        </div>

        <div v-if="mode === 'register'" class="form-group">
          <label>确认密码</label>
          <input v-model="confirmPw" :type="showPw ? 'text' : 'password'" placeholder="再次输入密码" minlength="4" required />
        </div>

        <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

        <button type="submit" class="btn btn-primary btn-full" :disabled="loading">
          {{ loading ? '处理中...' : (mode === 'login' ? '🔐 登录' : '✨ 注册并登录') }}
        </button>
      </form>

      <div class="auth-footer">
        <span v-if="mode === 'login'">还没有账号？<a href="#" @click.prevent="mode = 'register'">立即注册</a></span>
        <span v-else>已有账号？<a href="#" @click.prevent="mode = 'login'">去登录</a></span>
      </div>

      <div class="login-disclaimer">
        <p>🔒 密码经 bcrypt 加密存储 · JWT 安全令牌 · 病历数据隔离</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const auth = useAuthStore()

const mode = ref('login')
const phone = ref('')
const password = ref('')
const confirmPw = ref('')
const nickname = ref('')
const showPw = ref(false)
const loading = ref(false)
const errorMsg = ref('')

async function handleSubmit() {
  errorMsg.value = ''
  if (!phone.value || !password.value) {
    errorMsg.value = '请填写手机号和密码'
    return
  }
  if (mode.value === 'register' && password.value !== confirmPw.value) {
    errorMsg.value = '两次密码输入不一致'
    return
  }

  loading.value = true
  try {
    if (mode.value === 'register') {
      await auth.register(phone.value, password.value, nickname.value)
    } else {
      await auth.login(phone.value, password.value)
    }
    // 登录成功，跳转首页
    router.push('/')
  } catch (err) {
    errorMsg.value = err.message || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--bg) 0%, var(--primary-tint) 50%, var(--gold-tint) 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: var(--card);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 36px 28px 28px;
}

.login-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  margin-bottom: 28px;
}
.logo-badge {
  width: 48px; height: 48px;
  background: var(--primary);
  color: var(--gold);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 700;
}
.logo-title {
  font-size: 20px;
  color: var(--primary-deep);
  font-weight: 800;
  letter-spacing: 2px;
}
.logo-subtitle {
  font-size: 11px;
  color: var(--ink-2);
}

.auth-tabs {
  display: flex;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--line);
  margin-bottom: 24px;
}
.auth-tab {
  flex: 1;
  padding: 10px;
  border: none;
  background: var(--bg);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  color: var(--ink-2);
  transition: all 0.25s;
}
.auth-tab.active {
  background: var(--primary);
  color: #fff;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-group label {
  font-size: 13px;
  color: var(--ink-2);
  font-weight: 600;
}
.form-group input {
  padding: 10px 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  font-size: 15px;
  background: var(--bg);
  color: var(--ink);
  outline: none;
  transition: border-color 0.2s;
}
.form-group input:focus {
  border-color: var(--primary);
}

.password-wrap {
  position: relative;
}
.password-wrap input {
  width: 100%;
  padding-right: 42px;
}
.eye-btn {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
}

.error-msg {
  color: var(--danger);
  font-size: 13px;
  background: rgba(244, 67, 54, 0.08);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid rgba(244, 67, 54, 0.2);
}

.btn-full {
  width: 100%;
  padding: 12px;
  font-size: 15px;
  font-weight: 700;
  margin-top: 4px;
}

.auth-footer {
  text-align: center;
  margin-top: 18px;
  font-size: 13px;
  color: var(--ink-2);
}
.auth-footer a {
  color: var(--primary);
  font-weight: 600;
  text-decoration: none;
}

.login-disclaimer {
  margin-top: 20px;
  text-align: center;
}
.login-disclaimer p {
  font-size: 11px;
  color: var(--ink-3);
}
</style>
