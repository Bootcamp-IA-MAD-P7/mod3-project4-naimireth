<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api/client'
import EmptyState from '../components/EmptyState.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { formatDate, formatDuration, formatNumber } from '../utils/format'

const analyses = ref([])
const loading = ref(true)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    analyses.value = await api.analyses()
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
        <p class="eyebrow">Trazabilidad</p>
        <h1 class="page-title">Historial</h1>
        <p class="page-subtitle">
          Consulta todos los análisis guardados, su estado y el acceso a cada informe de exposición.
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

    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">Análisis guardados</div>
          <div class="card-subtitle">
            {{ analyses.length }} {{ analyses.length === 1 ? 'registro' : 'registros' }} ·
            Procesamiento secuencial
          </div>
        </div>
      </div>

      <div v-if="loading && !analyses.length" class="card-body">
        <div class="loading-line">
          <span class="spinner"></span>
          Cargando historial...
        </div>
      </div>

      <div v-else-if="analyses.length" class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th>Vídeo</th>
              <th>Fecha</th>
              <th>Duración</th>
              <th>Detecciones</th>
              <th>Estado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="analysis in analyses" :key="analysis.id">
              <td class="strong">{{ analysis.video_name }}</td>
              <td class="num">{{ formatDate(analysis.created_at) }}</td>
              <td class="num">{{ formatDuration(analysis.duration_seconds) }}</td>
              <td class="num">{{ formatNumber(analysis.total_detections) }}</td>
              <td><StatusBadge :status="analysis.status" /></td>
              <td class="num">
                <RouterLink :to="`/resultados/${analysis.id}`" class="card-link">
                  Ver detalle
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <EmptyState
        v-else
        title="El historial está vacío"
        text="Todavía no se ha analizado ningún vídeo. Crea un análisis para ver aquí sus resultados."
      >
        <RouterLink to="/nuevo" class="btn btn-primary">Crear análisis</RouterLink>
      </EmptyState>
    </div>

    <div class="alert info">
      Los análisis se ejecutan de uno en uno. Si envías varios vídeos, quedarán en cola hasta que
      termine el procesamiento anterior.
    </div>
  </section>
</template>
