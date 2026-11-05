<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, uploadVideo } from '../api/client'
import StatusBadge from '../components/StatusBadge.vue'
import {
  formatDuration,
  formatFileSize,
  formatNumber,
  statusLabel,
} from '../utils/format'

const router = useRouter()

const fileInput = ref(null)
const file = ref(null)
const fileSize = ref(0)
const localDuration = ref(null)
const localResolution = ref('')
const videoUrl = ref('')
const uploadProgress = ref(0)
const submitting = ref(false)
const analysis = ref(null)
const progress = ref(null)
const error = ref('')
const health = ref(null)

let pollTimer = null

const progressPercent = computed(() => {
  const value = Number(progress.value?.progress || 0)
  return Math.max(0, Math.min(100, value))
})

const canStart = computed(
  () => Boolean(file.value) && !submitting.value && !analysis.value && health.value?.model_loaded !== false,
)

onMounted(async () => {
  try {
    health.value = await api.health()
  } catch {
    health.value = null
  }
})

onBeforeUnmount(() => {
  stopPolling()
  if (videoUrl.value) {
    URL.revokeObjectURL(videoUrl.value)
  }
})

function openFilePicker() {
  fileInput.value?.click()
}

function handleFile(event) {
  const selected = event.target.files?.[0]
  event.target.value = ''
  if (!selected) return

  error.value = ''
  resetAnalysis()
  clearFile()

  if (!selected.name.toLowerCase().endsWith('.mp4')) {
    error.value = 'Selecciona un archivo con extensión .mp4.'
    return
  }

  file.value = selected
  fileSize.value = selected.size
  videoUrl.value = URL.createObjectURL(selected)
  loadMetadata(videoUrl.value)
}

function clearFile() {
  file.value = null
  fileSize.value = 0
  localDuration.value = null
  localResolution.value = ''
  if (videoUrl.value) {
    URL.revokeObjectURL(videoUrl.value)
    videoUrl.value = ''
  }
}

function loadMetadata(url) {
  const video = document.createElement('video')
  video.preload = 'metadata'
  video.onloadedmetadata = () => {
    localDuration.value = Number.isFinite(video.duration) ? video.duration : null
    localResolution.value = video.videoWidth && video.videoHeight
      ? `${video.videoWidth} × ${video.videoHeight}`
      : ''
    video.removeAttribute('src')
    video.load()
  }
  video.src = url
}

async function startAnalysis() {
  if (!canStart.value) return

  submitting.value = true
  error.value = ''
  progress.value = null
  analysis.value = null
  uploadProgress.value = 0

  try {
    const created = await uploadVideo(file.value, (value) => {
      uploadProgress.value = value
    })
    analysis.value = created
    progress.value = {
      status: created.status,
      progress: created.progress,
      processed_frames: created.processed_frames,
      total_frames: created.total_frames,
      error_message: null,
    }
    startPolling(created.id)
  } catch (err) {
    error.value = err.message
  } finally {
    submitting.value = false
  }
}

function startPolling(id) {
  stopPolling()
  pollOnce(id)
  pollTimer = setInterval(() => pollOnce(id), 1000)
}

async function pollOnce(id) {
  try {
    const current = await api.progress(id)
    progress.value = current

    if (current.status === 'completed') {
      stopPolling()
      router.push(`/resultados/${id}`)
      return
    }

    if (current.status === 'failed') {
      stopPolling()
      error.value = current.error_message || 'El análisis ha fallado.'
    }
  } catch (err) {
    stopPolling()
    error.value = err.message
  }
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function resetAnalysis() {
  stopPolling()
  analysis.value = null
  progress.value = null
  uploadProgress.value = 0
  error.value = ''
}
</script>

<template>
  <section class="page">
    <div class="page-header">
      <div>
        <p class="eyebrow">Ingesta de vídeo</p>
        <h1 class="page-title">Nuevo análisis</h1>
        <p class="page-subtitle">
          Sube un vídeo MP4 y Brand Pulse detectará Adidas, Emirates, Nike y Spotify para calcular su
          tiempo de exposición.
        </p>
      </div>
    </div>

    <div class="tabs" role="tablist" aria-label="Origen del vídeo">
      <button type="button" class="tab active" role="tab" aria-selected="true">Archivo local</button>
      <button type="button" class="tab" role="tab" disabled>Enlace MP4 · próximamente</button>
    </div>
    <p class="results-note">
      Solo se procesan archivos MP4 locales. Los enlaces directos a vídeos autorizados se habilitarán
      en una próxima iteración.
    </p>

    <div v-if="error" class="alert error">{{ error }}</div>
    <div v-if="health && !health.model_loaded" class="alert warning">
      El modelo YOLO no está cargado en el backend. El análisis no podrá ejecutarse hasta que se
      corrija la ruta del modelo.
    </div>

    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">Vídeo de entrada</div>
          <div class="card-subtitle">Formato admitido: MP4</div>
        </div>
        <StatusBadge v-if="analysis || submitting" :status="progress?.status || (submitting ? 'processing' : 'queued')" />
      </div>

      <div class="card-body">
        <input
          ref="fileInput"
          class="file-input"
          type="file"
          accept="video/mp4,.mp4"
          @change="handleFile"
        />

        <div
          v-if="!file"
          class="dropzone"
          role="button"
          tabindex="0"
          @click="openFilePicker"
          @keydown.enter="openFilePicker"
        >
          <div class="empty-icon" aria-hidden="true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M5 15v3a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-3"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </div>
          <div class="dropzone-title">Selecciona un vídeo MP4</div>
          <p class="dropzone-text">
            El archivo se procesará en el servidor y se eliminará al terminar. Los resultados quedarán
            guardados en el historial.
          </p>
          <button type="button" class="btn" @click.stop="openFilePicker">Elegir archivo</button>
        </div>

        <div v-else class="file-summary">
          <div class="file-name">
            <span class="file-icon" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <rect x="3" y="5" width="13" height="14" rx="2" stroke="currentColor" stroke-width="1.7" />
                <path d="M16 10l5-3v10l-5-3" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" />
              </svg>
            </span>
            <span>{{ file.name }}</span>
          </div>

          <div v-if="videoUrl" class="video-preview">
            <video :src="videoUrl" controls playsinline preload="metadata"></video>
          </div>

          <div class="meta-grid">
            <div class="meta-item">
              <span>Tamaño</span>
              <strong>{{ formatFileSize(fileSize) }}</strong>
            </div>
            <div class="meta-item">
              <span>Duración</span>
              <strong>{{ localDuration ? formatDuration(localDuration) : '—' }}</strong>
            </div>
            <div class="meta-item">
              <span>Resolución</span>
              <strong>{{ localResolution || '—' }}</strong>
            </div>
            <div class="meta-item">
              <span>Formato</span>
              <strong>MP4</strong>
            </div>
          </div>

          <div class="actions">
            <button type="button" class="btn" :disabled="submitting" @click="openFilePicker">
              Cambiar vídeo
            </button>
            <button type="button" class="btn btn-primary" :disabled="!canStart" @click="startAnalysis">
              <span v-if="submitting" class="spinner" aria-hidden="true"></span>
              {{ submitting ? 'Subiendo...' : 'Iniciar análisis' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="submitting || analysis" class="card">
      <div class="card-header">
        <div>
          <div class="card-title">Estado del análisis</div>
          <div class="card-subtitle">El procesamiento se ejecuta de forma secuencial</div>
        </div>
        <StatusBadge :status="progress?.status || (submitting ? 'processing' : 'queued')" />
      </div>
      <div class="card-body">
        <div v-if="submitting && !analysis" class="progress-block">
          <div class="progress-head">
            <span>Subiendo vídeo al servidor</span>
            <strong>{{ uploadProgress }}%</strong>
          </div>
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: `${uploadProgress}%` }"></div>
          </div>
        </div>

        <div v-if="analysis" class="progress-block">
          <div class="progress-head">
            <span>{{ statusLabel(progress?.status || analysis.status) }}</span>
            <strong>{{ progressPercent.toFixed(0) }}%</strong>
          </div>
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: `${progressPercent}%` }"></div>
          </div>
          <p class="results-note">
            Fotogramas procesados:
            {{ formatNumber(progress?.processed_frames || 0) }}
            <template v-if="progress?.total_frames">
              de {{ formatNumber(progress.total_frames) }}
            </template>
          </p>
          <div v-if="progress?.status === 'failed'" class="actions">
            <button type="button" class="btn" @click="resetAnalysis">Reintentar</button>
          </div>
        </div>
      </div>
    </div>

    <div class="alert info">
      La medición es una estimación basada en fotogramas muestreados, no un seguimiento continuo del
      mismo logotipo. Una marca se contabiliza como máximo una vez por fotograma.
    </div>
  </section>
</template>
