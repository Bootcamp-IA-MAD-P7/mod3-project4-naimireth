# Tests

Pruebas automatizadas del backend.

## Contenido

| Archivo | Cobertura |
| --- | --- |
| `test_health.py` | Arranque de la API, base de datos y ausencia del modelo. |
| `test_metrics.py` | FPS efectivo, límite por duración, orden y porcentajes por marca. |
| `test_api_analyses.py` | Flujo completo con detector simulado, historial, progreso, dashboard y limpieza del archivo. |

Los tests usan una base de datos temporal y un detector falso para no depender de GPU. El flujo con el
modelo real se valida aparte con un vídeo sintético.

## Ejecución

Desde la raíz del repositorio:

```bash
backend\.venv\Scripts\python.exe -m pytest -q
```

En Linux/macOS:

```bash
backend/.venv/bin/python -m pytest -q
```

El archivo `pytest.ini` añade `backend/` al `PYTHONPATH`.
