import { defineStore } from 'pinia'
import { api } from '../api'

/** 纯净空状态（新注册用户默认） */
const EMPTY_DEFAULT = () => ({
  patient: {
    age: null,
    sex: 'M',
    weight_kg: null,
    height_cm: null,
    pregnant: false,
    allergies: [],
  },
  lab_raw: [],
  tongue: {},
  tongueImage: null,
  face: {},
  faceImage: null,
  symptoms: {},
  current_drugs: [],
  report: null,
  history: [],
})

/** 演示示例数据（供用户手动一键加载） */
export const DEMO_PRESET = {
  patient: {
    age: 34,
    sex: 'F',
    weight_kg: 52,
    height_cm: 162,
    pregnant: false,
    allergies: ['青霉素'],
  },
  lab_raw: [
    { name_raw: '谷丙转氨酶(ALT)', value: 68, unit: 'U/L' },
    { name_raw: '甘油三酯', value: 2.8, unit: 'mmol/L' },
    { name_raw: '血红蛋白', value: 95, unit: 'g/L' },
  ],
  tongue: {
    coat_thickness: 1,
    greasy_index: 0.2,
    color: '淡红',
    coating: '薄白',
  },
  face: {
    complexion: '红润',
  },
  symptoms: {
    怕冷: 3,
    疲劳: 5,
    情绪抑郁: 6,
    胀痛: 7,
  },
  current_drugs: ['华法林'],
}

function getStorageKey() {
  try {
    const userStr = localStorage.getItem('sh_user')
    if (userStr) {
      const u = JSON.parse(userStr)
      if (u?.id) return `sh_state_${u.id}`
    }
  } catch {}
  return 'sh_state_guest'
}

const saved = (() => {
  try {
    const k = getStorageKey()
    const d = localStorage.getItem(k)
    return d ? JSON.parse(d) : null
  } catch {
    return null
  }
})()

export const usePatientStore = defineStore('patient', {
  state: () => ({ ...EMPTY_DEFAULT(), ...(saved || {}) }),

  getters: {
    profileDone: (s) =>
      !!(s.patient.age && s.patient.weight_kg && s.patient.height_cm),
    labsDone: (s) => s.lab_raw.length > 0,
    tongueDone: (s) => Object.keys(s.tongue).length > 0 || !!s.tongueImage,
    symptomsDone: (s) => Object.keys(s.symptoms).length > 0,
    drugsDone: (s) => s.current_drugs.length > 0,

    /** 生成方案的最低条件：基础信息 + 症状问卷 */
    readyToGenerate() {
      return this.profileDone && this.symptomsDone
    },

    /** 组装 POST /api/v1/full_report 请求体 */
    payload: (s) => ({
      patient: s.patient,
      lab_raw: s.lab_raw,
      tongue: s.tongue,
      face: s.face,
      symptoms: s.symptoms,
      current_drugs: s.current_drugs,
    }),
  },

  actions: {
    persist() {
      try {
        const k = getStorageKey()
        localStorage.setItem(k, JSON.stringify(this.$state))
      } catch (e) {
        console.warn('LocalStorage save failed:', e)
      }
    },

    /** 切换/登录新账号时调用，加载对应账号的数据 */
    loadUserSession() {
      const k = getStorageKey()
      const saved = localStorage.getItem(k)
      if (saved) {
        try {
          Object.assign(this.$state, EMPTY_DEFAULT(), JSON.parse(saved))
        } catch {
          Object.assign(this.$state, EMPTY_DEFAULT())
        }
      } else {
        // 新账号：全新空白状态
        Object.assign(this.$state, EMPTY_DEFAULT())
      }
      this.syncFromServer()
    },

    /** 加载测试/演示数据（供调试试用） */
    loadDemoPreset() {
      Object.assign(this.patient, DEMO_PRESET.patient)
      this.lab_raw = [...DEMO_PRESET.lab_raw]
      this.tongue = { ...DEMO_PRESET.tongue }
      this.face = { ...DEMO_PRESET.face }
      this.symptoms = { ...DEMO_PRESET.symptoms }
      this.current_drugs = [...DEMO_PRESET.current_drugs]
      this.persist()
    },

    setPatient(info) {
      Object.assign(this.patient, info)
      this.persist()
    },

    setLabRaw(list) {
      this.lab_raw = list
      this.persist()
    },

    addLabItem(item) {
      const idx = this.lab_raw.findIndex((i) => i.name_raw === item.name_raw)
      if (idx >= 0) {
        this.lab_raw[idx] = item
      } else {
        this.lab_raw.push(item)
      }
      this.persist()
    },

    removeLabItem(index) {
      this.lab_raw.splice(index, 1)
      this.persist()
    },

    setTongue(tongueData) {
      this.tongue = tongueData
      this.persist()
    },

    setTongueImage(dataUrl) {
      this.tongueImage = dataUrl
      this.persist()
    },

    setFace(faceData) {
      this.face = faceData
      this.persist()
    },

    setFaceImage(dataUrl) {
      this.faceImage = dataUrl
      this.persist()
    },

    setSymptoms(symMap) {
      this.symptoms = symMap
      this.persist()
    },

    setSymptomScore(key, val) {
      if (val === 0 || val === null) {
        delete this.symptoms[key]
      } else {
        this.symptoms[key] = val
      }
      this.persist()
    },

    setCurrentDrugs(drugs) {
      this.current_drugs = drugs
      this.persist()
    },

    setReport(rep) {
      this.report = rep
      this.addHistory({
        type: 'report',
        summary: rep.dosage_result?.status === 'BLOCKED'
          ? `安全拦截: ${rep.dosage_result?.reason || '触发禁忌规则'}`
          : `处方方案: ${rep.dosage_result?.base_formula?.name || '定制组方'} (${rep.syndrome_result?.primary || '辩证组方'})`,
        data: rep,
      })
      this.persist()
    },

    /** 添加病历到本地 + 同步到服务器 */
    async addHistory(entry) {
      const record = {
        id: Date.now(),
        date: new Date().toISOString(),
        ...entry,
      }
      this.history.unshift(record)
      this.persist()

      try {
        const token = localStorage.getItem('sh_token')
        if (token) {
          await api.saveRecord(token, {
            type: entry.type,
            summary: entry.summary,
            data: entry.data,
          })
        }
      } catch (e) {
        console.warn('病历同步到服务器失败（本地已保存）:', e.message)
      }
    },

    /** 从服务器拉取该用户的病历，合并到本地 */
    async syncFromServer() {
      try {
        const token = localStorage.getItem('sh_token')
        if (!token) return
        const res = await api.getMyRecords(token)
        if (res.records?.length) {
          const serverIds = new Set(res.records.map(r => r.id))
          const localOnly = this.history.filter(h => !serverIds.has(String(h.id)))
          this.history = [...res.records, ...localOnly]
          this.persist()
        }
      } catch (e) {
        console.warn('从服务器同步病历失败:', e.message)
      }
    },

    resetAll() {
      Object.assign(this.$state, EMPTY_DEFAULT())
      this.persist()
    },
  },
})
