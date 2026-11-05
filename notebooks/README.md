# Notebooks

Cuadernos de Jupyter/Colab para **entrenar y evaluar** el detector de logos con YOLO11.

## Contenido previsto

| Cuaderno | Proposito |
| --- | --- |
| `01_preparacion_dataset` | Descarga/organizacion del dataset, extraccion de fotogramas, formato YOLO. |
| `02_entrenamiento_yolo11` | Entrenamiento con GPU de Colab, configuracion de hiperparametros, callbacks. |
| `03_evaluacion` | mAP50, mAP50-95, precision, recall, matriz de confusion, curvas PR. |
| `04_inferencia_ejemplo` | Pruebas del modelo sobre video de ejemplo y exportacion de los pesos. |

## Ejecucion en Google Colab

1. Importar el cuaderno en Colab.
2. Activar GPU: *Entorno de ejecucion > Acelerador > GPU*.
3. Montar Google Drive si se necesita persistir pesos o checkpoints.
4. Ejecutar las celdas en orden y exportar `best.pt` a la carpeta `models/` del repositorio.

## Buenas practicas

- Fijar semillas (`seed`) para que el entrenamiento sea reproducible.
- Registrar en cada cuaderno la version de Ultralytics, PyTorch y el hardware usado.
- No subir al repositorio checkpoints, pesos ni imagenes de entrenamiento: estan excluidos por
  `.gitignore`.
