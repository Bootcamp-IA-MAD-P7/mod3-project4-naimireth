# Modelo de detección

## Ficha

| Campo | Valor |
| --- | --- |
| Arquitectura | YOLOv8 Nano |
| Framework | Ultralytics 8.4.202 |
| Pesos principales | `models/football_brands/best.pt` |
| Respaldo | `models/football_brands/last.pt` |
| Entrenamiento | Google Colab, 30 épocas |
| Dispositivo de inferencia | CPU por defecto (`DEVICE=cpu`) |

## Clases

El orden se lee del propio checkpoint:

```text
0 -> Adidas
1 -> Emirates
2 -> Nike
3 -> Spotify
```

El backend usa `model.names`, por lo que no hay una lista de clases duplicada en configuración.

## Integración

1. FastAPI arranca y ejecuta el `lifespan`.
2. Se instancia `BrandDetector` una sola vez con `best.pt`.
3. Cada fotograma muestreado se pasa a `model.predict()` con los umbrales configurados.
4. Las cajas se agrupan por clase para calcular métricas.
5. El modelo no se recarga por fotograma ni por petición.

## Umbrales

| Variable | Por defecto | Uso |
| --- | --- | --- |
| `MODEL_CONFIDENCE_THRESHOLD` | 0.25 | Confianza mínima de detección. |
| `MODEL_IOU_THRESHOLD` | 0.45 | Umbral de Non-Maximum Suppression. |

Subir la confianza reduce falsos positivos, pero puede perder logotipos pequeños o poco nítidos.

## Limitaciones

- El modelo fue entrenado para cuatro marcas concretas; no detecta otras.
- Logotipos muy pequeños, borrosos, ocluidos o con fuerte perspectiva pueden no detectarse.
- No hay tracking entre fotogramas en el Nivel 1.
- Los pesos no se versionan en Git por tamaño; deben copiarse localmente.
