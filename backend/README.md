# Backend

API FastAPI de Brand Pulse. Procesa vídeos MP4 con OpenCV y el modelo YOLOv8 existente, calcula la
exposición por marca y persiste los resultados en SQLite.

## Estructura

```text
backend/
├── app/
│   ├── main.py                  # create_app(), CORS, rutas y carga única del modelo
│   ├── api/
│   │   ├── deps.py              # Dependencias compartidas
│   │   ├── health.py            # GET /api/health
│   │   ├── analyses.py          # Subida, historial, detalle y progreso
│   │   └── dashboard.py         # GET /api/dashboard
│   ├── core/config.py           # Settings desde .env y rutas del repositorio
│   ├── database/
│   │   ├── db.py                # Motor, sesiones y create_all
│   │   └── models.py            # analyses, brand_results, detections
│   ├── schemas/analysis.py      # Contratos Pydantic
│   └── services/
│       ├── detector.py          # Carga y ejecución de Ultralytics YOLO
│       ├── video_processor.py   # OpenCV: metadatos y muestreo de fotogramas
│       ├── metrics.py           # Tiempo y porcentaje por marca
│       └── analysis_service.py  # Cola de un trabajador y persistencia
└── requirements.txt
```

## Decisiones de implementación

- El modelo se carga **una sola vez** en el `lifespan` de FastAPI.
- El procesamiento usa un `ThreadPoolExecutor(max_workers=1)`: nunca hay dos análisis simultáneos.
- SQLite usa WAL y sesiones independientes por hilo.
- Cada marca se deduplica por fotograma para las métricas; se guarda también el número de cajas.
- El archivo subido se elimina en un bloque `finally` al terminar o fallar.
- Si el modelo no está disponible, la subida responde `503` y `/api/health` lo indica.

## Arranque

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Configuración

Los valores por defecto funcionan sin `.env`. Las claves disponibles están en
[`.env.example`](../.env.example). La ruta del modelo se resuelve desde la raíz del repositorio:
`models/football_brands/best.pt`.

## Pruebas

Desde la raíz:

```bash
backend\.venv\Scripts\python.exe -m pytest -q
```
