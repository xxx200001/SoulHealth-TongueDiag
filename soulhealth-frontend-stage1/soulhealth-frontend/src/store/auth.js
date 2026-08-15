// 认证状态管理 — 统一使用 bio 认证体系（username + password + RBAC）
import { defineStore } from 'pinia'
import { api } from '../api'
import { usePatientStore } from './patient'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('sh_token') || '',
    user: JSON.parse(localStorage.getItem('sh_user') || 'null'),
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    displayName: (state) =>
      state.user?.display_name || state.user?.username || '游客',
    isAdmin: (state) => state.user?.role === 'admin',
    authHeaders: (state) =>
      state.token ? { Authorization: `Bearer ${state.token}` } : {},
  },

  actions: {
    async register(username, password, displayName) {
      const res = await api.register({ username, password, display_name: displayName })
      this._setAuth(res)
      return res
    },

    async login(username, password) {
      const res = await api.login({ username, password })
      this._setAuth(res)
      return res
    },

    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('sh_token')
      localStorage.removeItem('sh_user')
      const patientStore = usePatientStore()
      patientStore.resetAll()
    },

    async fetchMe() {
      if (!this.token) return null
      try {
        const res = await api.getMe(this.token)
        this.user = res.user
        localStorage.setItem('sh_user', JSON.stringify(res.user))
        return res.user
      } catch {
        this.logout()
        return null
      }
    },

    _setAuth(res) {
      this.token = res.token
      this.user = res.user
      localStorage.setItem('sh_token', res.token)
      localStorage.setItem('sh_user', JSON.stringify(res.user))

      const patientStore = usePatientStore()
      patientStore.loadUserSession()
    },
  },
})
