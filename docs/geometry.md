# Geometría de reconstrucción

Fuente compartida: imagen de **1402 × 1122 px** (frente a la izquierda, espalda a la derecha).
Cada SVG de músculo es un recorte enmascarado de esa imagen; su posición está en el `x`/`y`
del `<rect>` (offset = valor absoluto de ese `x`/`y`).

## Bounding boxes de figura

| Figura  | OX      | OY   | VW  | VH   |
|---------|---------|------|-----|------|
| Frente  | 91.5    | 31.5 | 561 | 1029 |
| Espalda | 694.492 | 34.5 | 605 | 1025 |

## Fórmula de posicionado (CSS %)

```
left   = (X − OX) / VW × 100
top    = (Y − OY) / VH × 100
width  =  W       / VW × 100
height =  H       / VH × 100
```

## Tabla completa

| Archivo | Cara | viewBox W | viewBox H | offset X | offset Y | key | grupo | tier | rezagado |
|---|---|---|---|---|---|---|---|---|---|
| Cuerpo completo front | frente | 561 | 1029 | 91.5 | 31.5 | (base) | base | — | — |
| traps & head | frente | 189 | 228 | 281.215 | 31.5 | trapecio | Espalda | C | no |
| Shoulders front | frente | 328 | 89 | 210.496 | 219.5 | hombros | Hombros | B | no |
| Chest front | frente | 219 | 106 | 266 | 232 | pecho | Pecho | A | no |
| Biceps front | frente | 366 | 113 | 191.995 | 287 | biceps | Brazos | B | no |
| Forearms front | frente | 475 | 170 | 136.328 | 364.99 | antebrazos | Brazos | D | sí |
| obliques front | frente | 190 | 261 | 279.5 | 316.96 | oblicuos | Core | C | no |
| Abs front | frente | 101 | 216 | 324 | 326.5 | abdomen | Core | B | no |
| legs front | frente | 255 | 283 | 246 | 470.693 | cuadriceps | Piernas | A | no |
| front calves | frente | 310 | 346 | 216.5 | 714.476 | pantorrillas | Piernas | E | sí |
| hands front | frente | 561 | 113 | 92 | 516.994 | manos | — | estático | no |
| Cuerpo completo back | espalda | 605 | 1025 | 694.492 | 34.5 | (base) | base | — | — |
| back head | espalda | 127 | 162 | 929.5 | 34.5 | cuello | — | estático | no |
| Back | espalda | 289 | 349 | 851.962 | 176 | espalda | Espalda | A | no |
| Arms from back | espalda | 605 | 207 | 695 | 99.5 | triceps | Brazos | C | sí |
| Glutes back | espalda | 223 | 136 | 882 | 469.5 | gluteos | Piernas | B | no |
| legs from back | espalda | 266 | 264 | 860.5 | 533.435 | isquios | Piernas | D | sí |
| back calves | espalda | 345 | 306 | 820.5 | 753.5 | pantorrillasb | Piernas | E | sí |

Los valores de `tier` y `rezagado` son datos de muestra del build actual (ver README).
