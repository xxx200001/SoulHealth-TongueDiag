<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const auth = useAuthStore()
const online = ref(null)
const dark = ref(false)

function toggleTheme() {
  dark.value = !dark.value
  const t = dark.value ? 'dark' : 'light'
  document.documentElement.dataset.theme = t
  localStorage.setItem('sh_theme', t)
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

onMounted(async () => {
  dark.value = document.documentElement.dataset.theme === 'dark'
  try {
    const r = await api.health()
    online.value = r.status === 'ok'
  } catch { online.value = false }
})
</script>

<template>
  <header class="hd">
    <router-link to="/" class="brand">
      <span class="seal serif">溯<br />源</span>
      <span class="names">
        <b class="en">SOULHEALTH</b>
        <b class="zh serif">AI 健康科研平台</b>
      </span>
    </router-link>

    <div class="hd-right">
      <!-- 用户信息 -->
      <div v-if="auth.isLoggedIn" class="user-badge" @click="showUserMenu = !showUserMenu">
        <span class="user-avatar">{{ auth.displayName.charAt(0) }}</span>
        <span class="user-name">{{ auth.displayName }}</span>
        <button class="logout-btn" @click.stop="handleLogout" title="退出登录">⏏</button>
      </div>
      <router-link v-else to="/login" class="login-link">🔐 登录</router-link>

      <span class="status" :class="{ ok: online === true, bad: online === false }">
        <i></i>{{ online === null ? '检测中' : online ? '服务在线' : '服务离线' }}
      </span>
      <button class="theme-btn" :aria-label="dark ? '切换浅色模式' : '切换深色模式'" @click="toggleTheme">
        <svg v-if="!dark" viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
          <circle cx="12" cy="12" r="4.2" /><path d="M12 2.5v2.6M12 18.9v2.6M2.5 12h2.6M18.9 12h2.6M5 5l1.8 1.8M17.2 17.2 19 19M19 5l-1.8 1.8M6.8 17.2 5 19" />
        </svg>
        <svg v-else viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11Z" />
        </svg>
      </button>
    </div>
  </header>
</template>

<style scoped>
.hd {
  position: sticky; top: 0; z-index: 20;
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px 10px;
  background: color-mix(in srgb, var(--bg) 82%, transparent);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--line);
}
.brand { display: flex; align-items: center; gap: 10px; }
.seal {
  width: 40px; height: 40px; border-radius: 8px;
  background: var(--seal); color: #F6EFE2;
  font-size: 13px; font-weight: 700; line-height: 1.15;
  display: flex; align-items: center; justify-content: center; text-align: center;
  box-shadow: inset 0 0 0 1.5px rgba(246, 239, 226, 0.55), 0 4px 10px -4px rgba(166, 64, 46, 0.6);
}
.names { display: flex; flex-direction: column; line-height: 1.2; }
.en { font-size: 9.5px; letter-spacing: 0.32em; color: var(--gold); font-weight: 700; }
.zh { font-size: 16px; }

.hd-right { display: flex; align-items: center; gap: 8px; }

/* 用户信息 */
.user-badge {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 10px 4px 4px; border-radius: 20px;
  background: var(--primary-tint); cursor: default;
}
.user-avatar {
  width: 26px; height: 26px; border-radius: 50%;
  background: var(--primary); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
}
.user-name {
  font-size: 12px; color: var(--primary-deep); font-weight: 600;
  max-width: 80px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.logout-btn {
  background: none; border: none; cursor: pointer;
  font-size: 14px; color: var(--ink-3); padding: 2px 4px;
  border-radius: 4px; transition: all 0.2s;
}
.logout-btn:hover { color: var(--danger); background: rgba(244,67,54,0.1); }

.login-link {
  font-size: 12px; color: var(--primary); font-weight: 600;
  padding: 4px 10px; border: 1px solid var(--primary); border-radius: 16px;
  text-decoration: none; transition: all 0.2s;
}
.login-link:hover { background: var(--primary); color: #fff; }

.status {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 11px; color: var(--ink-3);
  padding: 4px 10px; border: 1px solid var(--line); border-radius: 999px;
}
.status i { width: 6px; height: 6px; border-radius: 50%; background: var(--ink-3); }
.status.ok { color: var(--primary); }
.status.ok i { background: var(--ok); box-shadow: 0 0 6px var(--ok); }
.status.bad { color: var(--danger); }
.status.bad i { background: var(--danger); }

.theme-btn {
  width: 34px; height: 34px; border-radius: 50%;
  border: 1px solid var(--line); background: var(--card); color: var(--ink-2);
  display: grid; place-items: center; cursor: pointer;
  transition: transform 0.2s ease;
}
.theme-btn:active { transform: rotate(40deg) scale(0.92); }
</style>
