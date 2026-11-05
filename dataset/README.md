# Dataset

Datos de entrenamiento y validacion para el detector de logos.

## Contenido previsto

```text
dataset/
├── raw/            # Videos de origen (clipes publicitarios, SPL, etc.)
├── images/         # Fotogramas extraidos en formato YOLO (train/val/test)
├── labels/         # Archivos .txt con las cajas y clases (formato YOLO)
├── annotations/    # Anotaciones en otros formatos (COCO, Pascal VOC) si hacen falta
└── classes.txt     # Nombre de cada clase y su indice
```

## Formato esperado (YOLO)

- Cada imagen `.jpg` tiene su `.txt` homonimo con una linea por objeto:
  `class_id x_center y_center width height`, con valores normalizados entre 0 y 1.
- `classes.txt` lista los identificadores de clase en orden, p. ej. `0 coca_cola`.

## Como se poblara

Los videos de origen se descargaran de fuentes publicas y se repartiran de forma aleatoria y
reproducible en `train` / `val` / `test` (proporcion orientativa 70/20/10). La extraccion de
fotogramas se hara con OpenCV desde los cuadernos de `notebooks/`.

## Versionado

**Este directorio no se versiona con Git.** El contenido real (videos, imagenes, etiquetas) esta
excluido por `.gitignore` porque ocupa cientos de MB. El dataset se comparte como artefacto
externo (Drive, releases de GitHub o enlace de descarga) y solo se versiona su descripcion.
