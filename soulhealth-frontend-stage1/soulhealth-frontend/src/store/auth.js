// 认证状态管理 — JWT + 用户信息
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
    displayName: (state) => state.user?.nickname || state.user?.phone || '游客',
    authHeaders: (state) => state.token ? { Authorization: `Bearer ${state.token}` } : {},
  },

  actions: {
    async register(phone, password, nickname) {
      const res = await api.register({ phone, password, nickname })
      this._setAuth(res)
      return res
    },

    async login(phone, password) {
      const res = await api.login({ phone, password })
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
