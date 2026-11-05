<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api/client'
import BrandBarChart from '../components/BrandBarChart.vue'
import EmptyState from '../components/EmptyState.vue'
import StatCard from '../components/StatCard.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { formatDate, formatDuration, formatNumber } from '../utils/format'

const dashboard = ref(null)
const health = ref(null)
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [dashboardData, healthData] = await Promise.all([api.dashboard(), api.health()])
    dashboard.value = dashboardData
    health.value = healthData
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="page">
    <div class="page-header">
      <div>
        <p class="eyebrow">Control de exposición</p>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">
          Resumen de vídeos analizados, detecciones y presencia estimada de cada marca patrocinadora.
        </p>
      </div>
      <div class="actions">
        <button class="btn" :disabled="loading" @click="load">
          {{ loading ? 'Actualizando...' : 'Actualizar' }}
        </button>
        <RouterLink to="/nuevo" class="btn btn-primary">Nuevo análisis</RouterLink>
      </div>
    </div>

    <div v-if="error" class="alert error">{{ error }}</div>
    <div v-if="health && !health.model_loaded" class="alert warning">
      El modelo YOLO no está cargado. Comprueba que
      <strong>models/football_brands/best.pt</strong> existe y reinicia el backend.
      <span v-if="health.detail">Detalle: {{ health.detail }}</span>
    </div>

    <div v-if="loading && !dashboard" class="loading-line">
      <span class="spinner"></span>
      Cargando dashboard...
    </div>

    <template v-if="dashboard">
      <div class="stats-grid">
        <StatCard
          label="Vídeos analizados"
          :value="formatNumber(dashboard.total_analyses)"
          :hint="`${formatNumber(dashboard.completed_analyses)} completados`"
          accent="violet"
        />
        <StatCard
          label="Detecciones totales"
          :value="formatNumber(dashboard.total_detections)"
          hint="Presencias de marca por fotograma"
          accent="blue"
        />
        <StatCard
          label="Tiempo analizado"
          :value="formatDuration(dashboard.total_video_seconds)"
          hint="Duración acumulada de los vídeos completados"
          accent="green"
        />
        <StatCard
          label="Marcas monitorizadas"
          :value="health?.classes?.length || 4"
          :hint="health?.classes?.join(' · ') || 'Adidas · Emirates · Nike · Spotify'"
        />
      </div>

      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Exposición por marca</div>
              <div class="card-subtitle">Tiempo acumulado y porcentaje sobre la duración analizada</div>
            </div>
          </div>
          <div class="card-body">
            <BrandBarChart :brands="dashboard.brand_summary" />
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Últimos análisis</div>
              <div class="card-subtitle">Actividad reciente del sistema</div>
            </div>
            <RouterLink to="/historial" class="card-link">Ver todo</RouterLink>
          </div>

          <div v-if="dashboard.recent_analyses.length" class="table-wrap">
            <table class="table">
              <thead>
                <tr>
                  <th>Vídeo</th>
                  <th>Estado</th>
                  <th>Fecha</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="analysis in dashboard.recent_analyses" :key="analysis.id">
                  <td class="strong">{{ analysis.video_name }}</td>
                  <td><StatusBadge :status="analysis.status" /></td>
                  <td class="num">{{ formatDate(analysis.created_at) }}</td>
                  <td class="num">
                    <RouterLink :to="`/resultados/${analysis.id}`" class="card-link">Abrir</RouterLink>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <EmptyState
            v-else
            title="Todavía no hay análisis"
            text="Sube tu primer vídeo MP4 para empezar a medir la exposición de las marcas."
          >
            <RouterLink to="/nuevo" class="btn btn-primary">Crear análisis</RouterLink>
          </EmptyState>
        </div>
      </div>
    </template>
  </section>
</template>
