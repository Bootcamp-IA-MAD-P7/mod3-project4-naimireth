<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { api } from './api/client'

const apiOnline = ref(false)
const booting = ref(true)

onMounted(async () => {
  const started = Date.now()
  const healthRequest = api
    .health()
    .then((health) => {
      apiOnline.value = health.status === 'ok'
    })
    .catch(() => {
      apiOnline.value = false
    })

  await Promise.race([
    healthRequest,
    new Promise((resolve) => setTimeout(resolve, 4000)),
  ])

  const remaining = Math.max(0, 900 - (Date.now() - started))
  setTimeout(() => {
    booting.value = false
  }, remaining)
})
</script>

<template>
  <Transition name="splash-fade">
    <div v-if="booting" class="splash" role="status" aria-live="polite">
      <div class="splash-ball" aria-hidden="true">
        <svg viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="46"
            fill="#f8fafc"
            stroke="#0b2314"
            stroke-opacity="0.22"
            stroke-width="2"
          />
          <g fill="#0b2314">
            <path d="M50 32 62 41 57 55 43 55 38 41Z" />
            <path d="M50 5 61 13 57 26 43 26 39 13Z" />
            <path d="M88 27 86 42 73 46 65 36 71 23Z" />
            <path d="M79 79 65 72 66 58 80 53 91 64Z" />
            <path d="M21 79 9 64 20 53 35 58 35 72Z" />
            <path d="M12 27 29 23 35 36 27 46 14 42Z" />
            <path d="M50 87 61.4 78.7 57.1 65.3 42.9 65.3 38.6 78.7Z" />
          </g>
          <g fill="none" stroke="#0b2314" stroke-width="2" stroke-linecap="round" opacity="0.5">
            <path d="M50 32V26" />
            <path d="M62 41l9-5" />
            <path d="M57 55l9 3" />
            <path d="M43 55l-8 3" />
            <path d="M38 41l-11 5" />
            <path d="M43 55v10.3" />
            <path d="M57 55v10.3" />
          </g>
        </svg>
      </div>
      <div class="splash-title">
        Cargando
        <span class="splash-dots" aria-hidden="true">
          <i></i><i></i><i></i>
        </span>
      </div>
      <div class="splash-sub">Brand Pulse · Preparando el campo</div>
    </div>
  </Transition>

  <div class="app">
    <header class="topbar">
      <RouterLink to="/" class="brand" aria-label="Brand Pulse, ir al dashboard">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="27" fill="#e8f8ed" />
            <g fill="#0b2314">
              <path d="M32 7 39 12 37 19 27 19 25 12Z" />
              <path d="M54 19 53 28 44 31 39 24 43 16Z" />
              <path d="M48 49 39 45 40 36 49 33 56 40Z" />
              <path d="M16 49 9 40 16 33 25 36 26 45Z" />
              <path d="M10 19 22 16 26 24 21 31 12 28Z" />
            </g>
            <circle cx="32" cy="32" r="10" fill="#0b2314" opacity="0.92" />
            <circle cx="32" cy="32" r="8.2" fill="#e8f8ed" />
            <path
              d="M32 32V25.5M32 32l5.2 3.2"
              stroke="#0b2314"
              stroke-width="2.4"
              stroke-linecap="round"
            />
            <circle cx="32" cy="32" r="1.7" fill="#0b2314" />
          </svg>
        </span>
        <span class="brand-name">Brand<span>Pulse</span></span>
      </RouterLink>

      <nav class="nav" aria-label="Navegación principal">
        <RouterLink to="/" exact-active-class="active">Dashboard</RouterLink>
        <RouterLink to="/nuevo" active-class="active">Nuevo análisis</RouterLink>
        <RouterLink to="/historial" active-class="active">Historial</RouterLink>
      </nav>

      <div class="topbar-status">
        <span class="status-dot" :class="{ online: apiOnline }" aria-hidden="true"></span>
        <span>{{ apiOnline ? 'API conectada' : 'API sin conexión' }}</span>
      </div>
    </header>

    <main class="main">
      <RouterView />
    </main>

    <footer class="footer">
      Brand Pulse · Medición estimada de exposición publicitaria basada en fotogramas detectados
    </footer>
  </div>
</template>
