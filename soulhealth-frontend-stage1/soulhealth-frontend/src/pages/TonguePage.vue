<template>
  <div class="page-container">
    <div class="page-header">
      <div class="serif page-title">👅 舌诊与面诊智能拍摄</div>
      <div class="page-desc">
        AI 视觉算法实时解析舌象苔质与面色色调。拍摄后自动进行光线/清晰度/过曝质量校验 + 8 维舌象量化分析。
      </div>
    </div>

    <!-- ========== 1. 舌诊拍摄区域 ========== -->
    <div class="card photo-section">
      <div class="section-title margin-top-0">
        👅 1. 舌象采集与特征量化
        <small>摄像头实时拍摄 · 质量校验 · AI量化分析</small>
      </div>

      <!-- 摄像头取景 / 已拍照预览 -->
      <div class="camera-frame">
        <video v-if="cameraActive && !tongueSnapshot" ref="tongueVideoRef" autoplay playsinline class="camera-video"></video>
        <img v-else-if="tongueSnapshot" :src="tongueSnapshot" class="snapshot-img" alt="舌象拍照" />
        <div v-else class="camera-placeholder">
          <span class="cam-icon">📷</span>
          <span>点击下方按钮启动摄像头</span>
        </div>
        <!-- 引导框 -->
        <div v-if="cameraActive && !tongueSnapshot" class="camera-overlay">
          <div class="guide-oval"></div>
          <div class="guide-tip">请将舌头自然伸出并置于框内</div>
        </div>
      </div>

      <!-- 摄像头控制按钮 -->
      <div class="cam-controls">
        <button v-if="!cameraActive && !tongueSnapshot" class="btn btn-primary" @click="startCamera('tongue')">
          📷 启动摄像头拍摄舌象
        </button>
        <button v-if="cameraActive && !tongueSnapshot" class="btn btn-primary" @click="capturePhoto('tongue')">
          📸 拍摄
        </button>
        <button v-if="cameraActive && !tongueSnapshot" class="btn" @click="stopCamera">
          ✕ 关闭摄像头
        </button>
        <button v-if="tongueSnapshot" class="btn" @click="retakeTongue">
          🔄 重新拍摄
        </button>
        <button v-if="tongueSnapshot && !tongueAnalyzing" class="btn btn-primary" @click="analyzeTongueImage">
          🔬 AI 分析舌象
        </button>
        <span v-if="tongueAnalyzing" class="analyzing-tag">⏳ 正在分析中...</span>

        <!-- 或上传图片 -->
        <label class="btn upload-btn">
          📁 上传舌象照片
          <input type="file" accept="image/*" hidden @change="onTongueUpload" />
        </label>
      </div>

      <!-- 质量校验结果 -->
      <div v-if="tongueQuality" class="quality-result" :class="{ pass: tongueQuality.pass, fail: !tongueQuality.pass }">
        <div class="quality-title">{{ tongueQuality.pass ? '✅ 图片质量校验通过' : '❌ 图片质量不合格' }}</div>
        <div v-if="!tongueQuality.pass" class="quality-reasons">
          <div v-for="r in tongueQuality.reasons" :key="r">⚠ {{ r }}</div>
        </div>
        <div v-if="tongueQuality.metrics" class="quality-metrics">
          亮度: {{ tongueQuality.metrics.brightness }} ｜
          清晰度: {{ tongueQuality.metrics.blur_var }} ｜
          过曝率: {{ (tongueQuality.metrics.overexposed_ratio * 100).toFixed(1) }}% ｜
          饱和度: {{ tongueQuality.metrics.saturation }}
        </div>
      </div>

      <!-- 舌象AI分析结果 -->
      <div v-if="tongueResult" class="quant-result-box">
        <div class="quant-title">🔬 舌诊 AI 量化分析结果 (8维特征)</div>
        <div class="quant-grid">
          <div class="quant-item">
            <span class="quant-label">舌质颜色 (Body Color)</span>
            <span class="quant-value">{{ tongueResult.body_color?.class || tongueResult.body_color || '—' }}</span>
          </div>
          <div class="quant-item">
            <span class="quant-label">苔厚薄度 (Thickness)</span>
            <span class="quant-value">{{ formatVal(tongueResult.coat_thickness) }}</span>
          </div>
          <div class="quant-item">
            <span class="quant-label">苔色黄白度 (Yellow Index)</span>
            <span class="quant-value">{{ tongueResult.coat_yellow?.class || formatVal(tongueResult.coat_yellow?.yellow_index) }}</span>
          </div>
          <div class="quant-item">
            <span class="quant-label">腻苔指数 (Greasy)</span>
            <span class="quant-value">{{ formatVal(tongueResult.greasy_dry?.greasy_score) }}</span>
          </div>
          <div class="quant-item">
            <span class="quant-label">齿痕等级 (Tooth Mark)</span>
            <span class="quant-value">{{ tongueResult.tooth_mark?.grade ?? '—' }} 级</span>
          </div>
          <div class="quant-item">
            <span class="quant-label">裂纹等级 (Crack)</span>
            <span class="quant-value">{{ tongueResult.crack?.grade ?? '—' }} 级</span>
          </div>
          <div class="quant-item">
            <span class="quant-label">津液数值 (Moisture)</span>
            <span class="quant-value">{{ formatVal(tongueResult.moisture) }}</span>
          </div>
          <div class="quant-item">
            <span class="quant-label">瘀点数量 (Petechiae)</span>
            <span class="quant-value">{{ tongueResult.petechiae ?? '—' }} 个</span>
          </div>
        </div>
        <button class="btn btn-primary btn-sm" @click="applyTongueToStore" style="margin-top:12px">
          ✓ 采用此分析结果并写入辩证数据
        </button>
      </div>

      <!-- 分析错误 -->
      <div v-if="tongueError" class="error-box">❌ {{ tongueError }}</div>
    </div>

    <!-- ========== 2. 面诊区域 ========== -->
    <div class="card photo-section">
      <div class="section-title margin-top-0">
        👤 2. 面诊气色采集
        <small>拍摄面部照片 · AI自动分析面色</small>
      </div>

      <div class="camera-frame face-frame">
        <video v-if="faceCameraActive && !faceSnapshot" ref="faceVideoRef" autoplay playsinline class="camera-video"></video>
        <img v-else-if="faceSnapshot" :src="faceSnapshot" class="snapshot-img" alt="面部拍照" />
        <div v-else class="camera-placeholder">
          <span class="cam-icon">🤳</span>
          <span>点击按钮启动摄像头拍摄面部</span>
        </div>
      </div>

      <div class="cam-controls">
        <button v-if="!faceCameraActive && !faceSnapshot" class="btn btn-primary" @click="startFaceCamera">
          📷 启动摄像头拍摄面部
        </button>
        <button v-if="faceCameraActive && !faceSnapshot" class="btn btn-primary" @click="capturePhoto('face')">
          📸 拍摄
        </button>
        <button v-if="faceCameraActive && !faceSnapshot" class="btn" @click="stopFaceCamera">
          ✕ 关闭
        </button>
        <button v-if="faceSnapshot" class="btn" @click="retakeFace">🔄 重拍面部</button>
        <button v-if="faceSnapshot && !faceAnalyzing" class="btn btn-primary" @click="analyzeFaceImage">
          🔬 AI 面诊分析
        </button>
        <span v-if="faceAnalyzing" class="analyzing-tag">⏳ 面诊分析中...</span>
        <label class="btn upload-btn">
          📁 上传面部照片
          <input type="file" accept="image/*" hidden @change="onFaceUpload" />
        </label>
      </div>

      <!-- 面诊AI分析结果 -->
      <div v-if="faceResult" class="quant-result-box">
        <div class="quant-title">🔬 面诊 AI 分析结果</div>
        <div class="quant-grid">
          <div class="quant-item">
            <span class="quant-label">面色亮度</span>
            <span class="quant-value">{{ faceResult.brightness ?? '—' }}</span>
          </div>
          <div class="quant-item">
            <span class="quant-label">萎黄指数</span>
            <span class="quant-value">{{ faceResult.sallow_index ?? '—' }}</span>
          </div>
          <div class="quant-item">
            <span class="quant-label">面色判定</span>
            <span class="quant-value">{{ faceResult.complexion || faceResult.lip_color?.class || '—' }}</span>
          </div>
          <div class="quant-item">
            <span class="quant-label">分析方法</span>
            <span class="quant-value">{{ faceResult.method === 'mediapipe_478' ? 'MediaPipe 478点' : '颜色分析' }}</span>
          </div>
        </div>
        <button class="btn btn-primary btn-sm" @click="applyFaceToStore" style="margin-top:12px">
          ✓ 采用面诊结果
        </button>
      </div>
      <div v-if="faceError" class="error-box">❌ {{ faceError }}</div>
    </div>

    <!-- 跨页步骤引导 -->
    <StepGuide />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { usePatientStore } from '../store/patient'
import { api } from '../api'
import StepGuide from '../components/StepGuide.vue'

const store = usePatientStore()

// --- 舌诊 ---
const tongueVideoRef = ref(null)
const cameraActive = ref(false)
const tongueSnapshot = ref(null)
const tongueAnalyzing = ref(false)
const tongueResult = ref(null)
const tongueQuality = ref(null)
const tongueError = ref('')
let tongueStream = null

// --- 面诊 ---
const faceVideoRef = ref(null)
const faceCameraActive = ref(false)
const faceSnapshot = ref(null)
const faceAnalyzing = ref(false)
const faceResult = ref(null)
const faceError = ref('')
let faceStream = null

// --- 页面加载时恢复之前的拍照 ---
onMounted(() => {
  if (store.tongueImage) {
    tongueSnapshot.value = store.tongueImage
  }
  if (store.faceImage) {
    faceSnapshot.value = store.faceImage
  }
  // 恢复之前的分析结果
  if (store.tongue && Object.keys(store.tongue).length > 0) {
    tongueResult.value = store.tongue
    tongueQuality.value = { pass: true }
  }
  if (store.face && Object.keys(store.face).length > 0) {
    faceResult.value = store.face
  }
})

// 启动摄像头
async function startCamera(type) {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: type === 'face' ? 'user' : 'environment', width: 640, height: 480 }
    })
    if (type === 'tongue') {
      tongueStream = stream
      cameraActive.value = true
      setTimeout(() => {
        if (tongueVideoRef.value) tongueVideoRef.value.srcObject = stream
      }, 100)
    }
  } catch (e) {
    tongueError.value = '无法启动摄像头: ' + e.message
  }
}

async function startFaceCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: 640, height: 480 }
    })
    faceStream = stream
    faceCameraActive.value = true
    setTimeout(() => {
      if (faceVideoRef.value) faceVideoRef.value.srcObject = stream
    }, 100)
  } catch (e) {
    faceError.value = '无法启动摄像头: ' + e.message
  }
}

function capturePhoto(type) {
  const video = type === 'tongue' ? tongueVideoRef.value : faceVideoRef.value
  if (!video) return
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth || 640
  canvas.height = video.videoHeight || 480
  const ctx = canvas.getContext('2d')
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  const dataUrl = canvas.toDataURL('image/jpeg', 0.9)
  if (type === 'tongue') {
    tongueSnapshot.value = dataUrl
    store.setTongueImage(dataUrl)
    stopCamera()
  } else {
    faceSnapshot.value = dataUrl
    store.setFaceImage(dataUrl)
    stopFaceCamera()
  }
}

function stopCamera() {
  if (tongueStream) {
    tongueStream.getTracks().forEach(t => t.stop())
    tongueStream = null
  }
  cameraActive.value = false
}

function stopFaceCamera() {
  if (faceStream) {
    faceStream.getTracks().forEach(t => t.stop())
    faceStream = null
  }
  faceCameraActive.value = false
}

function retakeTongue() {
  tongueSnapshot.value = null
  tongueResult.value = null
  tongueQuality.value = null
  tongueError.value = ''
  store.setTongueImage(null)
}

function retakeFace() {
  faceSnapshot.value = null
  faceResult.value = null
  faceError.value = ''
  store.setFaceImage(null)
}

function onTongueUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    tongueSnapshot.value = reader.result
    store.setTongueImage(reader.result)
    tongueResult.value = null
    tongueQuality.value = null
    tongueError.value = ''
  }
  reader.readAsDataURL(file)
}

function onFaceUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    faceSnapshot.value = reader.result
    store.setFaceImage(reader.result)
    faceResult.value = null
    faceError.value = ''
  }
  reader.readAsDataURL(file)
}

async function analyzeTongueImage() {
  if (!tongueSnapshot.value) return
  tongueAnalyzing.value = true
  tongueError.value = ''
  tongueResult.value = null
  tongueQuality.value = null
  try {
    const res = await api.analyzeTongue(tongueSnapshot.value)
    if (res.code === 300) {
      tongueQuality.value = { pass: false, reasons: res.reasons, metrics: res.metrics }
    } else if (res.code === 301) {
      tongueError.value = res.error
      tongueQuality.value = { pass: true }
    } else {
      tongueQuality.value = { pass: true, metrics: res.quality_metrics }
      tongueResult.value = res
      applyTongueToStore()
    }
  } catch (e) {
    tongueError.value = '分析请求失败: ' + e.message
  } finally {
    tongueAnalyzing.value = false
  }
}

async function analyzeFaceImage() {
  if (!faceSnapshot.value) return
  faceAnalyzing.value = true
  faceError.value = ''
  faceResult.value = null
  try {
    const res = await api.analyzeFace(faceSnapshot.value)
    if (res.code === 0) {
      faceResult.value = res
      applyFaceToStore()
    } else {
      faceError.value = res.error || '面诊分析失败'
    }
  } catch (e) {
    faceError.value = '分析请求失败: ' + e.message
  } finally {
    faceAnalyzing.value = false
  }
}

function applyTongueToStore() {
  if (!tongueResult.value) return
  const r = tongueResult.value
  store.setTongue({
    coat_thickness: typeof r.coat_thickness === 'number' ? r.coat_thickness : r.coat_thickness?.value ?? 0,
    greasy_index: r.greasy_dry?.greasy_score ?? 0,
    color: r.body_color?.class || String(r.body_color || ''),
    coating: r.coat_yellow?.class || '',
    tooth_mark_grade: r.tooth_mark?.grade ?? 0,
    crack_grade: r.crack?.grade ?? 0,
    moisture: typeof r.moisture === 'number' ? r.moisture : 0,
    petechiae_count: r.petechiae ?? 0,
  })
}

function applyFaceToStore() {
  if (!faceResult.value) return
  const r = faceResult.value
  store.setFace({
    complexion: r.complexion || r.lip_color?.class || '红润',
    brightness: r.brightness,
    sallow_index: r.sallow_index,
    method: r.method,
  })
}

function formatVal(v) {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'number') return v.toFixed(1)
  return String(v)
}

onUnmounted(() => {
  stopCamera()
  stopFaceCamera()
})
</script>

<style scoped>
.page-container { max-width: 800px; margin: 0 auto; padding: 20px 16px 80px; }
.page-title { font-size: 22px; color: var(--primary-deep); margin-bottom: 6px; }
.page-desc { font-size: 14px; color: var(--ink-2); margin-bottom: 20px; }
.photo-section { margin-bottom: 20px; }
.margin-top-0 { margin-top: 0; }

.camera-frame {
  position: relative; height: 300px; border-radius: var(--radius-sm);
  overflow: hidden; margin-bottom: 12px; border: 1px solid var(--line);
  background: #111;
}
.camera-video { width: 100%; height: 100%; object-fit: cover; }
.snapshot-img { width: 100%; height: 100%; object-fit: contain; background: #000; }
.camera-placeholder {
  width: 100%; height: 100%; display: flex; flex-direction: column;
  align-items: center; justify-content: center; color: var(--ink-3); gap: 8px;
}
.cam-icon { font-size: 36px; }

.camera-overlay {
  position: absolute; inset: 0; z-index: 2;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  pointer-events: none;
}
.guide-oval { width: 160px; height: 110px; border: 2px dashed var(--gold); border-radius: 50%; }
.guide-tip {
  margin-top: 8px; font-size: 12px; color: #fff;
  background: rgba(0,0,0,0.6); padding: 2px 10px; border-radius: 10px;
}

.cam-controls { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; align-items: center; }
.upload-btn { cursor: pointer; }
.analyzing-tag { font-size: 13px; color: var(--gold); font-weight: 600; animation: pulse 1s infinite; }
@keyframes pulse { 50% { opacity: 0.5; } }

.quality-result {
  padding: 10px 14px; border-radius: var(--radius-sm); margin-bottom: 12px;
  font-size: 13px;
}
.quality-result.pass { background: rgba(76,175,80,0.1); border: 1px solid var(--ok); }
.quality-result.fail { background: rgba(244,67,54,0.1); border: 1px solid var(--danger); }
.quality-title { font-weight: 700; margin-bottom: 4px; }
.quality-reasons { color: var(--danger); }
.quality-metrics { margin-top: 6px; font-size: 11px; color: var(--ink-2); }

.quant-result-box {
  background: var(--bg); border: 1px solid var(--line); padding: 12px 16px;
  border-radius: var(--radius-sm); margin-top: 8px;
}
.quant-title { font-size: 13px; color: var(--primary-deep); font-weight: 700; margin-bottom: 10px; }
.quant-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px; }
.quant-item { display: flex; flex-direction: column; }
.quant-label { font-size: 11px; color: var(--ink-3); }
.quant-value { font-size: 15px; font-weight: 700; color: var(--primary); }

.error-box {
  background: rgba(244,67,54,0.1); border: 1px solid var(--danger);
  padding: 10px 14px; border-radius: var(--radius-sm); font-size: 13px;
  color: var(--danger); margin-top: 8px;
}

</style>
