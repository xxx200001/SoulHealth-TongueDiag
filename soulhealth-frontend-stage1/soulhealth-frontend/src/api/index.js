// 统一 API 层 —— 融合中医辨证溯源 + 生物计算全部接口
const BASE = import.meta.env.VITE_API_BASE ?? ''

async function request(path, options = {}) {
  let res
  try {
    res = await fetch(BASE + path, {
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      ...options,
    })
  } catch {
    throw new Error('无法连接后端服务，请确认 server.py 已在 9000 端口启动')
  }
  if (res.status === 401) {
    // 登录失效，清除本地凭证
    localStorage.removeItem('sh_token')
    localStorage.removeItem('sh_user')
    let detail = ''
    try { const body = await res.json(); detail = body.detail ?? '' } catch {}
    throw new Error(detail || '登录已失效，请重新登录')
  }
  if (!res.ok) {
    let detail = ''
    try { const body = await res.json(); detail = body.detail ?? '' } catch {}
    throw new Error(detail || `请求失败 HTTP ${res.status}`)
  }
  return res.json()
}

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function authRequest(path, token, options = {}) {
  return request(path, {
    ...options,
    headers: { ...authHeaders(token), ...(options.headers || {}) },
  })
}

export const api = {
  // ===== 统一健康检查 =====
  health: () => request('/api/health'),

  // ===== 认证（bio 体系：username/password + RBAC）=====
  login: ({ username, password }) =>
    request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  register: ({ username, password, display_name }) =>
    request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, display_name }),
    }),

  getMe: (token) =>
    authRequest('/api/auth/me', token),

  changePassword: (token, { old_password, new_password }) =>
    authRequest('/api/auth/change_password', token, {
      method: 'POST',
      body: JSON.stringify({ old_password, new_password }),
    }),

  // ===== 管理员 =====
  adminListUsers: (token) =>
    authRequest('/api/admin/users', token),

  adminCreateUser: (token, { username, password, role }) =>
    authRequest('/api/admin/users', token, {
      method: 'POST',
      body: JSON.stringify({ username, password, role }),
    }),

  adminToggleUser: (token, uid, disabled) =>
    authRequest(`/api/admin/users/${uid}`, token, {
      method: 'PATCH',
      body: JSON.stringify({ disabled }),
    }),

  adminDeleteUser: (token, uid) =>
    authRequest(`/api/admin/users/${uid}`, token, { method: 'DELETE' }),

  // ===== 档案管理 =====
  listPatients: (token, query = '') =>
    authRequest(`/api/patients${query ? `?query=${encodeURIComponent(query)}` : ''}`, token),

  createPatient: (token, payload) =>
    authRequest('/api/patients', token, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getPatient: (token, pid) =>
    authRequest(`/api/patients/${pid}`, token),

  updatePatient: (token, pid, payload) =>
    authRequest(`/api/patients/${pid}`, token, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  deletePatient: (token, pid) =>
    authRequest(`/api/patients/${pid}`, token, { method: 'DELETE' }),

  getTimeline: (token, pid, code = null) =>
    authRequest(`/api/patients/${pid}/timeline${code ? `?code=${code}` : ''}`, token),

  addNote: (token, pid, text) =>
    authRequest(`/api/patients/${pid}/notes`, token, {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),

  // ===== 数据录入 =====
  addObservation: (token, pid, data) =>
    authRequest(`/api/patients/${pid}/observations`, token, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  addFinding: (token, pid, data) =>
    authRequest(`/api/patients/${pid}/findings`, token, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  addImpression: (token, pid, data) =>
    authRequest(`/api/patients/${pid}/impressions`, token, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // ===== 文档上传 =====
  uploadDocument: (token, formData) =>
    fetch(BASE + '/api/documents/upload', {
      method: 'POST',
      headers: authHeaders(token),
      body: formData,  // FormData，不设 Content-Type
    }).then(async (res) => {
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `上传失败 HTTP ${res.status}`)
      }
      return res.json()
    }),

  selftestVision: (token) =>
    authRequest('/api/selftest/vision', token),

  // ===== AI 分析 =====
  runAnalysis: (token, patientId) =>
    authRequest('/api/analyze', token, {
      method: 'POST',
      body: JSON.stringify({ patient_id: patientId }),
    }),

  listAnalyses: (token, pid) =>
    authRequest(`/api/patients/${pid}/analyses`, token),

  getAnalysis: (token, aid) =>
    authRequest(`/api/analyses/${aid}`, token),

  // ===== 报告 =====
  listReports: (token, pid) =>
    authRequest(`/api/patients/${pid}/reports`, token),

  // ===== 健康问答 =====
  askQuestion: (token, pid, question) =>
    authRequest(`/api/patients/${pid}/ask`, token, {
      method: 'POST',
      body: JSON.stringify({ question }),
    }),

  // ===== 中医辨证溯源 API (tongue /api/v1/*) =====
  questionnaire: (sex = 'M') =>
    request(`/api/v1/questionnaire?sex=${encodeURIComponent(sex)}`),

  fullReport: (payload) =>
    request('/api/v1/full_report', { method: 'POST', body: JSON.stringify(payload) }),

  analyzeTongue: (base64Image) =>
    request('/api/v1/analyze_tongue', {
      method: 'POST',
      body: JSON.stringify({ image: base64Image }),
    }),

  analyzeFace: (base64Image) =>
    request('/api/v1/analyze_face', {
      method: 'POST',
      body: JSON.stringify({ image: base64Image }),
    }),

  ocrLab: (base64Image) =>
    request('/api/v1/ocr_lab', {
      method: 'POST',
      body: JSON.stringify({ image: base64Image }),
    }),

  // ===== 病历存储（tongue 旧接口，保留兼容）=====
  saveRecord: (token, { type, summary, data }) =>
    authRequest('/api/v1/save_record', token, {
      method: 'POST',
      body: JSON.stringify({ type, summary, data }),
    }),

  getMyRecords: (token) =>
    authRequest('/api/v1/my_records', token),

  deleteRecord: (token, recordId) =>
    authRequest(`/api/v1/record/${recordId}`, token, { method: 'DELETE' }),
}
