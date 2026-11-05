# Métricas de exposición

## Muestreo

Procesar todos los fotogramas de un vídeo en CPU es costoso. El MVP muestrea a una frecuencia
configurable (`VIDEO_FPS_SAMPLING`, por defecto 2 FPS).

```text
stride       = round(FPS original / FPS objetivo)
FPS efectivo = FPS original / stride
```

Ejemplo: vídeo a 30 FPS y objetivo de 2 FPS.

```text
stride       = round(30 / 2) = 15
FPS efectivo = 30 / 15 = 2.0
```

Se procesan los fotogramas 0, 15, 30, 45... y cada uno representa 1 / 2 = 0,5 segundos.

## Deduplicación por marca

En un mismo fotograma pueden aparecer varias cajas de la misma clase. Para las métricas, **una marca
cuenta como máximo una vez por fotograma**. El número de cajas se conserva en `box_count` y
`raw_detections`.

## Tiempo acumulado

```text
tiempo = fotogramas_con_detección / FPS efectivo
```

El resultado se limita a la duración total del vídeo para evitar sobreestimar por redondeos.

## Porcentaje de presencia

```text
porcentaje = tiempo acumulado / duración total × 100
```

Se acota entre 0 y 100.

## Agregado del dashboard

Para cada marca:

```text
porcentaje_medio = suma(tiempo de la marca) / suma(duración de análisis completados) × 100
```

Como varias marcas pueden aparecer a la vez, la suma de porcentajes de todas las marcas puede superar
el 100 %. Cada porcentaje individual mide la presencia de esa marca respecto a la duración del vídeo.

## Limitaciones

- Es una **estimación por fotogramas muestreados**, no un tracking continuo del mismo logotipo.
- No se distinguen apariciones continuas o separadas.
- El FPS y la duración informados por OpenCV pueden ser aproximados en algunos contenedores.
- Los falsos positivos y falsos negativos del modelo afectan directamente a las métricas.
- El tiempo representa presencia en pantalla, no número de impresiones ni audiencia.
