// 统一 API 层
const BASE = import.meta.env.VITE_API_BASE ?? ''

async function request(path, options = {}) {
  let res
  try {
    res = await fetch(BASE + path, {
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      ...options,
    })
  } catch {
    throw new Error('无法连接后端服务，请确认 uvicorn 已在 8000 端口启动')
  }
  if (!res.ok) {
    let detail = ''
    try {
      const body = await res.json()
      detail = body.detail ?? ''
    } catch { /* 忽略 */ }
    throw new Error(detail || `请求失败 HTTP ${res.status}`)
  }
  return res.json()
}

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const api = {
  // ===== 公开接口 =====
  health: () => request('/health'),

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

  // ===== 认证接口 =====
  register: ({ phone, password, nickname }) =>
    request('/api/v1/register', {
      method: 'POST',
      body: JSON.stringify({ phone, password, nickname }),
    }),

  login: ({ phone, password }) =>
    request('/api/v1/login', {
      method: 'POST',
      body: JSON.stringify({ phone, password }),
    }),

  getMe: (token) =>
    request('/api/v1/me', { headers: authHeaders(token) }),

  // ===== 病历存储（需登录） =====
  saveRecord: (token, { type, summary, data }) =>
    request('/api/v1/save_record', {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify({ type, summary, data }),
    }),

  getMyRecords: (token) =>
    request('/api/v1/my_records', { headers: authHeaders(token) }),

  deleteRecord: (token, recordId) =>
    request(`/api/v1/record/${recordId}`, {
      method: 'DELETE',
      headers: authHeaders(token),
    }),
}
