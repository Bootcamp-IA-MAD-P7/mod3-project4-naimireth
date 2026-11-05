# Brand Pulse

Aplicación de visión artificial para detectar marcas patrocinadoras en vídeos de fútbol y medir su
exposición publicitaria. El usuario sube un vídeo MP4, el backend lo procesa con un modelo YOLOv8
ya entrenado y el dashboard muestra el tiempo y el porcentaje de presencia de cada marca.

Este repositorio implementa **únicamente el Nivel 1 (MVP esencial)**.

---

## 1. Funcionalidades del MVP

- Subida de vídeos MP4 desde el ordenador.
- Procesamiento secuencial (un único trabajador; los vídeos se encolan).
- Extracción de fotogramas con OpenCV.
- Detección con el modelo YOLOv8 existente en `models/football_brands/best.pt`.
- Clases del modelo: **Adidas, Emirates, Nike y Spotify**.
- Registro de detecciones por fotograma en SQLite.
- Cálculo del tiempo acumulado y del porcentaje de presencia por marca.
- Estado y progreso del análisis en tiempo real mediante polling.
- Dashboard, pantalla de nuevo análisis, resultados e historial.
- Eliminación automática del vídeo temporal al terminar el procesamiento.
- Persistencia de análisis y resultados para consultas posteriores.

### Fuera de alcance

No se implementan los Niveles 2 y 3: tracking, segmentación de apariciones, exportación PDF/Excel,
usuarios y roles, procesamiento simultáneo, directos ni integraciones externas.

---

## 2. Modelo

- Arquitectura: **YOLOv8 Nano**.
- Framework: **Ultralytics 8.4.202**.
- Pesos usados por la API: `models/football_brands/best.pt`.
- Respaldo: `models/football_brands/last.pt`.
- El modelo se entrena en Google Colab y **no se reentrena desde el backend**.
- El modelo se carga **una sola vez** al arrancar FastAPI y se reutiliza en todos los fotogramas.

Orden de clases confirmado en el checkpoint:

```text
0 -> Adidas
1 -> Emirates
2 -> Nike
3 -> Spotify
```

Los archivos `.pt` están excluidos de Git por tamaño. En un clon nuevo hay que copiarlos en
`models/football_brands/` antes de arrancar el backend.

---

## 3. Tecnologías

| Capa | Tecnología |
| --- | --- |
| Detección | Ultralytics YOLOv8 + PyTorch |
| Visión | OpenCV |
| Backend | FastAPI + Pydantic v2 |
| Persistencia | SQLite + SQLAlchemy |
| Frontend | Vue 3 + Vite + Vue Router |
| Pruebas | pytest + httpx |

No se añadieron librerías de gráficos ni de estado: el gráfico comparativo se renderiza con HTML/CSS
y la comunicación con la API usa `fetch` y `XMLHttpRequest`.

---

## 4. Estructura

```text
mod3-project4-naimireth/
├── backend/
│   ├── app/
│   │   ├── api/             # Routers: health, analyses, dashboard
│   │   ├── core/            # Configuración
│   │   ├── database/        # Motor, sesiones y modelos ORM
│   │   ├── schemas/         # Contratos Pydantic
│   │   ├── services/        # Detector, vídeo, métricas y orquestación
│   │   └── main.py          # Fábrica de la app y carga única del modelo
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── api/             # Cliente REST
│   │   ├── components/      # Tarjetas, gráfico, tabla, estados
│   │   ├── router/          # Rutas de la SPA
│   │   ├── views/           # Dashboard, nuevo análisis, resultados, historial
│   │   └── assets/          # Estilos
│   ├── package.json
│   └── vite.config.js
├── models/football_brands/  # best.pt y last.pt (ignorados por Git)
├── dataset/                 # Datos de entrenamiento (no incluidos)
├── notebooks/               # Cuadernos de Colab
├── tests/                   # Pruebas automatizadas
├── docs/                    # Documentación funcional y técnica
├── pytest.ini
├── .env.example
└── README.md
```

---

## 5. Puesta en marcha

### Requisitos

- Python 3.10+ (probado con Python 3.14.3).
- Node.js 18+ (probado con Node 22.13.0).
- El archivo `models/football_brands/best.pt` presente.

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

La API queda en `http://127.0.0.1:8000` y la documentación interactiva en
`http://127.0.0.1:8000/docs`.

La configuración es opcional: los valores por defecto funcionan sin crear `.env`. Para personalizar,
copia `.env.example` a `.env` en la raíz del repositorio.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

La interfaz queda en `http://localhost:5173`. Vite redirige `/api` al backend en el puerto 8000.

### Pruebas

Desde la raíz del repositorio:

```bash
backend\.venv\Scripts\python.exe -m pytest -q
```

En Linux/macOS:

```bash
backend/.venv/bin/python -m pytest -q
```

---

## 6. API REST

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/api/health` | Estado del backend, base de datos y modelo. |
| POST | `/api/analyses` | Sube un MP4 y encola su análisis. |
| GET | `/api/analyses` | Lista el historial de análisis. |
| GET | `/api/analyses/{id}` | Resultado completo de un análisis. |
| GET | `/api/analyses/{id}/progress` | Estado y progreso del procesamiento. |
| GET | `/api/dashboard` | Métricas agregadas para el dashboard. |

La documentación detallada está en [`docs/api.md`](docs/api.md).

---

## 7. Cálculo de exposición

Para cada fotograma muestreado:

- Una marca se contabiliza **como máximo una vez**, aunque haya varios logotipos de esa clase.
- `tiempo acumulado = fotogramas con detección / FPS efectivo`.
- `porcentaje = tiempo acumulado / duración total del vídeo × 100`.
- El FPS efectivo se ajusta al muestreo: `FPS original / stride`.
- El tiempo se limita a la duración total del vídeo.

La medición es una **estimación basada en fotogramas detectados**, no un seguimiento continuo del
mismo logotipo. Esta limitación se documenta también en [`docs/metricas.md`](docs/metricas.md).

---

## 8. Estado de validación

- Backend y frontend ejecutables.
- Modelo cargado correctamente: 4 clases detectadas.
- Flujo completo validado con un vídeo sintético y el modelo real: subida, procesamiento,
  persistencia, progreso, resultados, dashboard e historial.
- La validación de **detecciones reales de marcas** requiere un vídeo de fútbol con logotipos
  visibles. No se han inventado ni simulado resultados de detección.

---

## 9. Privacidad y almacenamiento

- El vídeo subido se guarda con un nombre aleatorio y se elimina al terminar el análisis.
- La base de datos y los archivos temporales están en `backend/data/` y `backend/storage/`, ambos
  ignorados por Git.
- No hay autenticación ni multiusuario: es un MVP local de un único operador.
