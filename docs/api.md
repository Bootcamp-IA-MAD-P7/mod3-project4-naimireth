# API REST

Base URL local: `http://127.0.0.1:8000/api`

## GET /health

Comprueba base de datos, modelo y clases.

```json
{
  "status": "ok",
  "app": "Brand Pulse API",
  "version": "0.1.0",
  "database": "ok",
  "model_loaded": true,
  "model_path": "C:\\...\\models\\football_brands\\best.pt",
  "classes": ["Adidas", "Emirates", "Nike", "Spotify"],
  "detail": null
}
```

Si el modelo no está disponible, `model_loaded` es `false` y `detail` explica el motivo.

## POST /analyses

Sube un vídeo MP4 y lo encola. Respuesta `202 Accepted`.

```bash
curl -X POST http://127.0.0.1:8000/api/analyses \
  -F "file=@partido.mp4;type=video/mp4"
```

Validaciones:

- Extensión `.mp4`.
- Tamaño máximo configurable (`VIDEO_MAX_UPLOAD_MB`, por defecto 2048 MB).
- Duración máxima configurable (`VIDEO_MAX_DURATION_SECONDS`, por defecto 1800 s).
- El archivo debe poder abrirse con OpenCV.
- El modelo debe estar cargado; si no, responde `503`.

La respuesta inicial incluye estado `queued` o `processing`, metadatos del vídeo y `brand_results`
vacío. El procesamiento continúa en segundo plano.

## GET /analyses

Devuelve el historial, ordenado del más reciente al más antiguo.

Parámetros: `limit` (1-500, por defecto 100) y `offset` (por defecto 0).

## GET /analyses/{id}

Devuelve el detalle completo. Incluye `brand_results` con una fila por cada clase del modelo, incluso
cuando el valor sea cero:

```json
{
  "id": 1,
  "video_name": "partido.mp4",
  "status": "completed",
  "duration_seconds": 120.0,
  "fps": 30.0,
  "total_frames": 3600,
  "processed_frames": 3600,
  "sampling_stride": 15,
  "effective_fps": 2.0,
  "total_detections": 240,
  "raw_detections": 310,
  "created_at": "2026-11-05T10:00:00Z",
  "completed_at": "2026-11-05T10:02:00Z",
  "brand_results": [
    {
      "brand_name": "Adidas",
      "frames_detected": 120,
      "box_count": 150,
      "time_seconds": 60.0,
      "percentage": 50.0
    }
  ]
}
```

- `total_detections`: suma de marcas detectadas por fotograma (deduplicadas).
- `raw_detections`: suma de cajas individuales devueltas por YOLO.
- `frames_detected`: fotogramas muestreados con al menos una caja de la marca.
- `box_count`: cajas individuales de la marca en los fotogramas muestreados.

## GET /analyses/{id}/progress

```json
{
  "id": 1,
  "status": "processing",
  "progress": 42.5,
  "processed_frames": 1530,
  "total_frames": 3600,
  "error_message": null
}
```

Estados: `queued`, `processing`, `completed`, `failed`.

## GET /dashboard

Métricas agregadas de los análisis completados.

```json
{
  "total_analyses": 3,
  "completed_analyses": 2,
  "total_detections": 420,
  "total_video_seconds": 240.0,
  "brand_summary": [
    {
      "brand_name": "Nike",
      "total_time_seconds": 80.0,
      "total_frames_detected": 160,
      "total_boxes": 210,
      "analyses_with_brand": 2,
      "average_percentage": 33.33
    }
  ],
  "recent_analyses": []
}
```

`average_percentage` es el tiempo acumulado de la marca dividido entre la duración total analizada,
ponderado por todos los análisis completados.

## Preparación para enlaces directos

El modelo de datos incluye `source_type`. En el Nivel 1 solo se admite `upload`. La interfaz muestra
la pestaña de enlace MP4 deshabilitada. No se implementa descarga externa, evasión de protecciones ni
procesamiento de URLs.

## GET /analyses/{id}/preview

Devuelve los fotogramas muestreados con recuadros de detección, para reproducirlos en cámara lenta.
Se generan durante el análisis y se guardan como JPEG en `backend/storage/outputs/{id}/`.

```json
{
  "analysis_id": 1,
  "slow_motion_fps": 1.0,
  "frames": [
    {
      "index": 0,
      "timestamp_seconds": 0.0,
      "url": "/analyses/1/preview/frames/frame_00000000.jpg"
    }
  ]
}
```

La lista puede estar vacía si el vídeo no produjo detecciones o si `PREVIEW_ENABLED=false`.

## GET /analyses/{id}/preview/frames/{filename}

Entrega un fotograma JPEG anotado. El nombre debe cumplir el patrón `frame_NNNNNNNN.jpg`.
La URL devuelta por el endpoint anterior es relativa a la base de la API.
