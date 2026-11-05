# Frontend

Interfaz web de Brand Pulse construida con **Vue 3**, **Vite** y **Vue Router**.

## Estructura

```text
frontend/
├── index.html
├── package.json
├── vite.config.js          # Proxy /api -> http://127.0.0.1:8000
└── src/
    ├── main.js
    ├── App.vue             # Layout, navegación y estado de conexión
    ├── api/client.js       # fetch y subida con progreso (XHR)
    ├── router/index.js
    ├── utils/format.js
    ├── components/
    │   ├── StatCard.vue
    │   ├── StatusBadge.vue
    │   ├── BrandBarChart.vue
    │   ├── ResultsTable.vue
    │   └── EmptyState.vue
    ├── views/
    │   ├── DashboardView.vue
    │   ├── NewAnalysisView.vue
    │   ├── ResultsView.vue
    │   └── HistoryView.vue
    └── assets/main.css
```

## Pantallas

1. **Dashboard**: vídeos analizados, detecciones totales, tiempo analizado, resumen de exposición por
   marca y últimos análisis.
2. **Nuevo análisis**: selección de MP4, metadatos locales del vídeo, subida con progreso, polling del
   estado y preparación visual para futuros enlaces directos autorizados.
3. **Resultados**: tiempos, porcentajes, gráfico comparativo, tabla y ficha técnica del procesamiento.
4. **Historial**: todos los análisis con fecha, duración, estado y acceso al detalle.

No se incluyen datos de demostración: los estados vacíos se muestran hasta que existan análisis reales.

## Arranque

```bash
cd frontend
npm install
npm run dev
```

La aplicación queda en `http://localhost:5173`. El proxy de Vite envía `/api` al backend en
`http://127.0.0.1:8000`.

Para cambiar la URL de la API se puede definir `VITE_API_URL` en un archivo `.env` local.

## Build

```bash
npm run build
```
