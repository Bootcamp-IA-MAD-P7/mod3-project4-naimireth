<script setup>
import { formatNumber, formatPercent, formatSeconds } from '../utils/format'

defineProps({
  brands: { type: Array, default: () => [] },
})
</script>

<template>
  <div class="table-wrap">
    <table class="table">
      <thead>
        <tr>
          <th>Marca</th>
          <th>Fotogramas</th>
          <th>Cajas</th>
          <th>Tiempo acumulado</th>
          <th>Presencia</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="brand in brands" :key="brand.brand_name">
          <td class="strong">{{ brand.brand_name }}</td>
          <td class="num">{{ formatNumber(brand.frames_detected) }}</td>
          <td class="num">{{ formatNumber(brand.box_count) }}</td>
          <td class="num">{{ formatSeconds(brand.time_seconds) }}</td>
          <td class="num">{{ formatPercent(brand.percentage) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
