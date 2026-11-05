<script setup>
import { computed } from 'vue'
import { brandColor, formatPercent, formatSeconds } from '../utils/format'

const props = defineProps({
  brands: { type: Array, default: () => [] },
})

function percentageFor(brand) {
  const value = brand.percentage ?? brand.average_percentage ?? 0
  return Math.max(0, Math.min(100, Number(value || 0)))
}

const hasData = computed(() =>
  props.brands.some(
    (brand) =>
      percentageFor(brand) > 0 ||
      Number(brand.frames_detected ?? brand.total_frames_detected ?? 0) > 0,
  ),
)

function barWidth(brand) {
  return `${percentageFor(brand)}%`
}

function secondsFor(brand) {
  return brand.time_seconds ?? brand.total_time_seconds ?? 0
}
</script>

<template>
  <div v-if="hasData" class="brand-chart">
    <div v-for="brand in brands" :key="brand.brand_name" class="brand-row">
      <div class="brand-label">
        {{ brand.brand_name }}
        <div class="brand-time">{{ formatSeconds(secondsFor(brand)) }}</div>
      </div>
      <div class="bar-track" role="presentation">
        <div
          class="bar-fill"
          :style="{ width: barWidth(brand), '--bar-color': brandColor(brand.brand_name) }"
        ></div>
      </div>
      <div class="brand-value">{{ formatPercent(percentageFor(brand)) }}</div>
    </div>
  </div>
  <div v-else class="empty-state">
    <div class="empty-title">Sin datos de exposición</div>
    <p class="empty-text">Cuando se complete un análisis con detecciones, aquí aparecerá la comparativa por marca.</p>
  </div>
</template>
