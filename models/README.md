# Models

Pesos del detector de marcas de Brand Pulse.

## Contenido

| Archivo | Descripción |
| --- | --- |
| `football_brands/best.pt` | Mejor checkpoint YOLOv8 Nano. Es el que usa la API. |
| `football_brands/last.pt` | Último checkpoint del entrenamiento. |

## Modelo

- Arquitectura: YOLOv8 Nano.
- Framework: Ultralytics 8.4.202.
- Entrenamiento: 30 épocas en Google Colab.
- Clases, en el orden del checkpoint:
  - `0` Adidas
  - `1` Emirates
  - `2` Nike
  - `3` Spotify

El backend lee los nombres y el orden directamente de `model.names`; no se duplican en variables de
entorno.

## Notas

- Los archivos `.pt` están excluidos por `.gitignore` por tamaño.
- Un clon nuevo debe incorporar `best.pt` y `last.pt` manualmente antes de arrancar el backend.
- El modelo se carga una sola vez al arrancar FastAPI y se reutiliza en todos los fotogramas.
- La ruta usada por defecto es `models/football_brands/best.pt`.
