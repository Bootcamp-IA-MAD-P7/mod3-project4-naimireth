<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api, apiAssetUrl } from '../api/client'
import BrandBarChart from '../components/BrandBarChart.vue'
import ResultsTable from '../components/ResultsTable.vue'
import StatCard from '../components/StatCard.vue'
import StatusBadge from '../components/StatusBadge.vue'
import {
  formatDate,
  formatDuration,
  formatNumber,
  formatSeconds,
  statusLabel,
} from '../utils/format'

const props = defineProps({
  id: { type: String, required: true },
})

const analysis = ref(null)
const loading = ref(true)
const error = ref('')
const preview = ref(null)
const previewIndex = ref(0)
const previewPlaying = ref(false)
let pollTimer = null
let previewTimer = null
let previewLoaded = false

const brands = computed(() => analysis.value?.brand_results || [])
const brandsDetected = computed(
  () => brands.value.filter((brand) => Number(brand.frames_detected) > 0).length,
)
const previewFrames = computed(() => preview.value?.frames || [])
const currentPreviewFrame = computed(
  () => previewFrames.value[previewIndex.value] || null,
)
const isProcessing = computed(() =>
  ['queued', 'processing'].includes(analysis.value?.status),
)
const progressPercent = computed(() => {
  const value = Number(analysis.value?.progress || 0)
  return Math.max(0, Math.min(100, value))
})

async function load(silent = false) {
  if (!silent) loading.value = true
  error.value = ''

  try {
    const data = await api.analysis(props.id)
    analysis.value = data

    if (['queued', 'processing'].includes(data.status)) {
      startPolling()
    } else {
      stopPolling()
      if (data.status === 'completed' && !previewLoaded) {
        loadPreview()
      }
    }
  } catch (err) {
    error.value = err.message
    stopPolling()
  } finally {
    loading.value = false
  }
}

function startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(() => load(true), 1500)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function loadPreview() {
  try {
    const data = await api.preview(props.id)
    preview.value = data
    previewLoaded = true
    previewIndex.value = 0
    if (data.frames?.length) startPreview()
  } catch {
    preview.value = null
  }
}

function startPreview() {
  if (!previewFrames.value.length) return
  previewPlaying.value = true
  if (previewTimer) clearInterval(previewTimer)

  const fps = Math.max(0.25, Number(preview.value?.slow_motion_fps) || 1)
  previewTimer = setInterval(() => {
    if (!previewFrames.value.length) return
    previewIndex.value = (previewIndex.value + 1) % previewFrames.value.length
  }, 1000 / fps)
}

function pausePreview() {
  previewPlaying.value = false
  if (previewTimer) {
    clearInterval(previewTimer)
    previewTimer = null
  }
}

function togglePreview() {
  if (previewPlaying.value) {
    pausePreview()
  } else {
    startPreview()
  }
}

onMounted(() => load())
onBeforeUnmount(() => {
  stopPolling()
  pausePreview()
})
</script>

<template>
  <section class="page">
    <div class="page-header">
      <div>
        <p class="eyebrow">Informe de exposición</p>
        <h1 class="page-title">{{ analysis?.video_name || 'Resultados' }}</h1>
        <p v-if="analysis" class="page-subtitle">
          {{ formatDate(analysis.created_at) }} · Duración {{ formatDuration(analysis.duration_seconds) }}
          · <StatusBadge :status="analysis.status" />
        </p>
        <p v-else class="page-subtitle">Detalle de detecciones y tiempo estimado de presencia por marca.</p>
      </div>
      <div class="actions">
        <button class="btn" :disabled="loading" @click="load()">
          {{ loading ? 'Actualizando...' : 'Actualizar' }}
        </button>
        <RouterLink to="/historial" class="btn">Historial</RouterLink>
        <RouterLink to="/nuevo" class="btn btn-primary">Nuevo análisis</RouterLink>
      </div>
    </div>

    <div v-if="error" class="alert error">{{ error }}</div>

    <div v-if="loading && !analysis" class="loading-line">
      <span class="spinner"></span>
      Cargando resultados...
    </div>

    <template v-if="analysis">
      <div v-if="isProcessing" class="card">
        <div class="card-header">
          <div>
            <div class="card-title">Procesando vídeo</div>
            <div class="card-subtitle">
              Estado: {{ statusLabel(analysis.status) }} · Esta pantalla se actualiza automáticamente
            </div>
          </div>
          <StatusBadge :status="analysis.status" />
        </div>
        <div class="card-body">
          <div class="progress-block">
            <div class="progress-head">
              <span>Progreso del análisis</span>
              <strong>{{ progressPercent.toFixed(0) }}%</strong>
            </div>
            <div class="progress-track">
              <div class="progress-fill" :style="{ width: `${progressPercent}%` }"></div>
            </div>
            <p class="results-note">
              Fotogramas procesados: {{ formatNumber(analysis.processed_frames || 0) }}
              <template v-if="analysis.total_frames">
                de {{ formatNumber(analysis.total_frames) }}
              </template>
            </p>
          </div>
        </div>
      </div>

      <div v-else-if="analysis.status === 'failed'" class="alert error">
        <div>
          <strong>El análisis no se pudo completar.</strong>
          <p>{{ analysis.error_message || 'Error desconocido durante el procesamiento.' }}</p>
        </div>
      </div>

      <template v-else>
        <div class="stats-grid">
          <StatCard
            label="Detecciones totales"
            :value="formatNumber(analysis.total_detections)"
            hint="Presencias de marca por fotograma"
            accent="violet"
          />
          <StatCard
            label="Cajas detectadas"
            :value="formatNumber(analysis.raw_detections)"
            hint="Detecciones individuales de YOLO"
            accent="blue"
          />
          <StatCard
            label="Marcas con presencia"
            :value="`${brandsDetected} / ${brands.length}`"
            hint="Clases del modelo con al menos una detección"
            accent="green"
          />
          <StatCard
            label="Duración del vídeo"
            :value="formatDuration(analysis.duration_seconds)"
            :hint="`${formatNumber(analysis.processed_frames)} fotogramas procesados`"
          />
        </div>

        <div v-if="previewFrames.length" class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Movimiento de logos en cámara lenta</div>
              <div class="card-subtitle">
                Fotogramas muestreados con recuadros de detección · {{ previewFrames.length }} fotogramas
              </div>
            </div>
            <span class="badge processing">Cámara lenta</span>
          </div>
          <div class="card-body">
            <div class="preview-player">
              <div class="preview-stage">
                <img
                  v-if="currentPreviewFrame"
                  :src="apiAssetUrl(currentPreviewFrame.url)"
                  :alt="`Fotograma ${previewIndex + 1}`"
                />
              </div>
              <div class="preview-controls">
                <button type="button" class="btn" @click="togglePreview">
                  {{ previewPlaying ? 'Pausar' : 'Reproducir' }}
                </button>
                <input
                  v-model.number="previewIndex"
                  class="preview-range"
                  type="range"
                  min="0"
                  :max="previewFrames.length - 1"
                  @input="pausePreview"
                />
                <span class="preview-meta">
                  {{ previewIndex + 1 }} / {{ previewFrames.length }}
                  <template v-if="currentPreviewFrame">
                    · {{ formatSeconds(currentPreviewFrame.timestamp_seconds) }}
                  </template>
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="grid-2">
          <div class="card">
            <div class="card-header">
              <div>
                <div class="card-title">Comparativa por marca</div>
                <div class="card-subtitle">Porcentaje de presencia sobre la duración total</div>
              </div>
            </div>
            <div class="card-body">
              <BrandBarChart :brands="brands" />
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <div>
                <div class="card-title">Ficha técnica</div>
                <div class="card-subtitle">Parámetros usados en el procesamiento</div>
              </div>
            </div>
            <div class="card-body">
              <div class="metric-list">
                <div class="metric-item">
                  <span>FPS original</span>
                  <strong>{{ analysis.fps ? analysis.fps.toFixed(2) : '—' }}</strong>
                </div>
                <div class="metric-item">
                  <span>Muestreo cada</span>
                  <strong>{{ analysis.sampling_stride ? `${analysis.sampling_stride} fotogramas` : '—' }}</strong>
                </div>
                <div class="metric-item">
                  <span>FPS efectivo</span>
                  <strong>{{ analysis.effective_fps ? analysis.effective_fps.toFixed(2) : '—' }}</strong>
                </div>
                <div class="metric-item">
                  <span>Resolución</span>
                  <strong>
                    {{ analysis.width && analysis.height ? `${analysis.width} × ${analysis.height}` : '—' }}
                  </strong>
                </div>
                <div class="metric-item">
                  <span>Fotogramas de origen</span>
                  <strong>{{ analysis.total_frames ? formatNumber(analysis.total_frames) : '—' }}</strong>
                </div>
                <div class="metric-item">
                  <span>Finalizado</span>
                  <strong>{{ analysis.completed_at ? formatDate(analysis.completed_at) : '—' }}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Detalle por marca</div>
              <div class="card-subtitle">Tiempo acumulado y porcentaje estimado de presencia</div>
            </div>
          </div>
          <ResultsTable :brands="brands" />
        </div>

        <div class="alert info">
          La medición es una estimación basada en fotogramas muestreados, no un seguimiento continuo
          del mismo logotipo. Una marca se contabiliza como máximo una vez por fotograma.
        </div>
      </template>
    </template>
  </section>
</template>
