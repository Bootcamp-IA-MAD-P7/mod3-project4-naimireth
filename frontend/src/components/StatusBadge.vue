<script setup>
import { computed } from 'vue'
import { statusLabel } from '../utils/format'

const props = defineProps({
  status: { type: String, default: 'queued' },
})

const label = computed(() => statusLabel(props.status))
</script>

<template>
  <span class="badge" :class="status">{{ label }}</span>
</template>
