# Impulse App

**Impulse** es una app de entrenamiento cuyo eje es un **modelo corporal interactivo**
reconstruido —**sin recrear nada**— a partir de SVG anatómicos reales. Cada músculo se
coloca en su posición exacta dentro del cuerpo completo (frente y espalda) y sirve como
capa interactiva para representar la **jerarquía** de desarrollo por grupo muscular.

> *"Tu entrenamiento se adapta a tu físico, no al revés."*

---

## Tabla de contenido

- [Demo / cómo abrirla](#demo--cómo-abrirla)
- [Qué hay en este repo](#qué-hay-en-este-repo)
- [El modelo corporal: cómo está reconstruido](#el-modelo-corporal-cómo-está-reconstruido)
- [Geometría de cada músculo](#geometría-de-cada-músculo)
- [Design system](#design-system)
- [Journey de 8 pantallas](#journey-de-8-pantallas)
- [Sistema de jerarquías (tiers)](#sistema-de-jerarquías-tiers)
- [Build: cómo se genera `index.html`](#build-cómo-se-genera-indexhtml)
- [Build iOS (10x app / Xcode)](#build-ios-10x-app--xcode)
- [Assets fuente (Google Drive)](#assets-fuente-google-drive)
- [Verificación visual](#verificación-visual)
- [Roadmap](#roadmap)

---

## Demo / cómo abrirla

`index.html` es un **único archivo autocontenido** (~604 KB): todos los assets van embebidos
como data-URI, usa fuentes del sistema y no depende de ningún host externo. Se abre con doble
clic en cualquier navegador.

```bash
# opcional: servirlo localmente
python3 -m http.server 8000
# → http://localhost:8000/index.html
```

---

## Qué hay en este repo

```
impulse-app/
├── index.html                 # ← LA APP (build final, autocontenida, lista para abrir)
├── project.yml                # spec XcodeGen → genera el proyecto iOS (para 10x app / Xcode)
├── ios/
│   └── Impulse/               # contenedor iOS nativo (SwiftUI + WKWebView) que carga index.html
│       ├── ImpulseApp.swift
│       ├── ImpulseWebView.swift
│       ├── Info.plist
│       └── Assets.xcassets/   # AppIcon + color de launch (#121212)
├── src/
│   └── template.html          # plantilla de la app con placeholders (fuente editable)
├── assets/
│   ├── svg/                   # 18 SVG originales del usuario (VERBATIM, sin modificar)
│   └── stencils/              # 16 stencils de máscara extraídos de cada músculo
├── scripts/
│   ├── build.py               # genera index.html desde template.html + assets
│   ├── shot.cjs / shot.mjs    # captura del estudio de físico (Playwright)
│   ├── phones.cjs             # captura de las 8 pantallas del journey
│   ├── rail.cjs / mont.cjs    # montajes de verificación
├── docs/
│   ├── geometry.md            # tabla completa de offsets y bounding boxes
│   └── screenshots/           # renders de verificación (frente, espalda, selección, 8 phones)
└── README.md
```

---

## El modelo corporal: cómo está reconstruido

El hallazgo clave: **los 18 SVG no son dibujos independientes**. Todos incrustan **el mismo
render de cuerpo completo** (una imagen de 1402×1122 px, con la figura de frente a la izquierda
y la de espalda a la derecha), y cada archivo es un **recorte enmascarado** de esa imagen
compartida. La posición del recorte está codificada en el atributo `x`/`y` del `<rect>` que
lleva el patrón de imagen.

Estructura de cada SVG de músculo:

```xml
<svg viewBox="0 0 W H">
  <mask id="m"> … paths del contorno del músculo, fill="#D9D9D9" … </mask>
  <g mask="url(#m)">
    <rect x="-OFFSET_X" y="-OFFSET_Y" width="1402" height="1122" fill="url(#pattern)"/>
  </g>
</svg>
```

**Reconstrucción (sin recrear):** para cada músculo se toma su offset `(X, Y)` y su tamaño
`(W, H)` en el espacio de la imagen fuente, y se posiciona por porcentaje **relativo al
bounding box de la figura** (frente o espalda):

```
left  = (X − OX) / VW × 100 %
top   = (Y − OY) / VH × 100 %
width =  W       / VW × 100 %
height=  H       / VH × 100 %
```

Bounding boxes de referencia (dentro de la fuente 1402×1122):

| Figura  | OX      | OY   | VW  | VH   |
|---------|---------|------|-----|------|
| Frente  | 91.5    | 31.5 | 561 | 1029 |
| Espalda | 694.492 | 34.5 | 605 | 1025 |

De cada SVG se extrae además el **contorno** (paths `fill="#D9D9D9"`) como *stencil*
(`assets/stencils/`), que se usa como `mask-image` en CSS para pintar el color de jerarquía
sobre la silueta exacta del músculo. Los músculos bilaterales (bíceps, antebrazos, manos,
tríceps) conservan sus **2 paths**.

**Nada se redibujó.** Las siluetas, los contornos y la foto base son los que entregó el usuario.

---

## Geometría de cada músculo

Ver [`docs/geometry.md`](docs/geometry.md) para la tabla completa (viewBox y offset de los 18
archivos). Resumen:

| Archivo | viewBox (W×H) | offset (X, Y) | grupo | tier |
|---|---|---|---|---|
| **Frente** | | | | |
| traps & head | 189×228 | 281.215, 31.5 | Espalda | C |
| Shoulders front | 328×89 | 210.496, 219.5 | Hombros | B |
| Chest front | 219×106 | 266, 232 | Pecho | A |
| Biceps front | 366×113 | 191.995, 287 | Brazos | B |
| Forearms front | 475×170 | 136.328, 364.99 | Brazos | D · rezagado |
| obliques front | 190×261 | 279.5, 316.96 | Core | C |
| Abs front | 101×216 | 324, 326.5 | Core | B |
| legs front | 255×283 | 246, 470.693 | Piernas | A |
| front calves | 310×346 | 216.5, 714.476 | Piernas | E · rezagado |
| hands front | 561×113 | 92, 516.994 | — | estático |
| Cuerpo completo front | 561×1029 | 91.5, 31.5 | base | — |
| **Espalda** | | | | |
| back head | 127×162 | 929.5, 34.5 | — | estático |
| Back | 289×349 | 851.962, 176 | Espalda | A |
| Arms from back | 605×207 | 695, 99.5 | Brazos | C · rezagado |
| Glutes back | 223×136 | 882, 469.5 | Piernas | B |
| legs from back | 266×264 | 860.5, 533.435 | Piernas | D · rezagado |
| back calves | 345×306 | 820.5, 753.5 | Piernas | E · rezagado |
| Cuerpo completo back | 605×1025 | 694.492, 34.5 | base | — |

---

## Design system

| Token | Valor |
|---|---|
| Fondo | `#121212` |
| Superficie | `#1E1E1E` |
| Superficie elevada | `#242424` |
| Texto | `#F5F5F5` |
| Acento (candy blue) | `#B2D5E5` |
| Radio | `16px` |
| Tipografía | SF Pro Display/Text (system font stack), números tabulares redondeados |
| Tema | dark-only (deliberado) |

---

## Journey de 8 pantallas

En la app se muestran como mockups de teléfono en un riel horizontal:

1. **Registro**
2. **Modelo corporal** (estudio de físico — frente)
3. **Dashboard**
4. **Entrenamiento**
5. **Biblioteca**
6. **Mapa / físico** (estudio de físico — espalda + selección)
7. **Ascenso de jerarquía**
8. **Paywall**

---

## Sistema de jerarquías (tiers)

Cada grupo muscular se pinta según su nivel de desarrollo. Colores:

| Tier | Nombre | Color |
|---|---|---|
| A | Élite | `#B2D5E5` |
| B | Oro | `#E0BE63` |
| C | Plata | `#A6B2BD` |
| D | Bronce | `#C08552` |
| E | Iniciado | `#6B7280` |

> **Nota:** las asignaciones de tier y la lista de *rezagados* que trae el build son **datos de
> muestra** para que el modelo se vea vivo. La lógica real (cómo se calcula el tier de cada
> músculo a partir de la evaluación/entrenamiento del usuario) está pendiente de conectar.

---

## Build: cómo se genera `index.html`

```bash
python3 scripts/build.py
# lee src/template.html + assets/svg + assets/stencils
# → escribe index.html (autocontenido)
```

`build.py` embebe las fotos base (frente/espalda) y los stencils como data-URI, calcula las
posiciones por porcentaje con las fórmulas de arriba, y rellena los placeholders del template
(`/*FRONT_BASE*/`, `/*BACK_BASE*/`, `<!--FRONT_LAYERS-->`, `<!--BACK_LAYERS-->`,
`/*FRONT_ASPECT*/`, `/*BACK_ASPECT*/`, `/*META_JSON*/`).

**Dependencias:** solo Python 3 (stdlib). Los scripts de captura usan Node + Playwright/Chromium.

---

## Build iOS (10x app / Xcode)

10x app (y Xcode) necesitan un proyecto iOS. Este repo lo trae vía **`project.yml`**
([XcodeGen](https://github.com/yonaskolb/XcodeGen)), uno de los archivos que 10x app busca
(`.xcodeproj`, `.xcworkspace` o `project.yml`).

La app iOS es un **contenedor nativo SwiftUI + WKWebView** (`ios/Impulse/`) que carga
`index.html` desde el bundle. Como el HTML es autocontenido (assets embebidos, sin red),
se sirve como archivo local — no requiere servidor ni conexión.

- **En 10x app:** sube el repo; al detectar `project.yml` genera el proyecto y compila.
- **Local con Xcode:**

  ```bash
  brew install xcodegen     # una sola vez
  xcodegen generate         # crea Impulse.xcodeproj desde project.yml
  open Impulse.xcodeproj     # ⌘R para correr en simulador/dispositivo
  ```

Config del target: bundle id `com.themtouch.impulse`, iOS 16+, orientación vertical, tema
oscuro. El ícono (`AppIcon`) está como placeholder — reemplázalo en `Assets.xcassets`.

> **Nota de UX:** hoy `index.html` está maquetado como preview/landing (riel horizontal de
> mockups + ancho máx. 1120). Dentro del WebView en un teléfono se ve, pero para una
> experiencia 100% nativa de una sola pantalla conviene desarrollar las vistas en SwiftUI o
> re-maquetar el HTML a layout mobile-first. Ver [Roadmap](#roadmap).

---

## Assets fuente (Google Drive)

Los 18 SVG originales viven en la carpeta **"Impulse training"** del Drive del usuario. IDs:

**Frente:** Cuerpo completo front `1mL3HcB1aWuYwOwjzYXH3VlBMGQJDUy6u` · traps & head
`1Pr94sa8RC7VtE6vvCLdKXAZkCbdFE3fl` · Shoulders front `1GK5le8NB5KS3t4dU3XECsEzqWp84fKnC` ·
Chest front `1icAVAXC3fPeGZ5rXVvIBPmcGuDnlOPSw` · Biceps front `1yEAhNlB_S4IBEesNU-dZJusDfMS4Dzcp` ·
Forearms front `1lzr14EVDtKAbvbaH3lsAWEx9zY9Vc2DV` · Abs front `1DiAl8cbSbaeUwEPvZP2mWdgR6mOB_iVj` ·
obliques front `1UFtfkyvkOmhpVEA0FvlKoIyAcZuaSrCs` · legs front `1U6xURMFD7gB8UrrE1FpCkFSShVUT4qQT` ·
front calves `1Lgc252I11DE0UJ08_6bZ-eNR7DC6GlyZ` · hands front `1cPUB6bnng48R07pqWeYz2M9YJ8klxAO2`

**Espalda:** Cuerpo completo back `1870Pe2uPFLyAtIuJAwxCM5dQWD4nZkHu` · back head
`16znF66ghBOdJkLytO468zhVC65bJyE4V` · Back `1db2SQsZhPcPNtI3gzilK8OTfTdXZLtQ7` ·
Arms from back `1ahyp-2kngVqcTM3u53B1My4s3G6V8wNx` · Glutes back `1sdDvMlNfMV129omDifYAN0796GGuVnh8` ·
legs from back `12O9OrmFCaSbFL8NlMbXG5oD_DkC0BVth` · back calves `1-qG-cM0mF1uXE_jboSdwamSbKAWXY-G7`

Copias verbatim en [`assets/svg/`](assets/svg/).

---

## Verificación visual

Alineación validada pixel-perfect con Playwright/Chromium headless. Renders en
[`docs/screenshots/`](docs/screenshots/): `shot-front.png`, `shot-back.png`, `shot-sel.png`
(estudio de físico) y `phone-1..8.png` (las 8 pantallas del journey).

---

## Roadmap

- [ ] Conectar la **lógica real de jerarquías/rezagados** (hoy datos de muestra).
- [ ] Exportar el estudio de físico como **componente React** (`AnimatedBodyModel`).
- [ ] Desarrollar a fondo las pantallas funcionales (registro, dashboard, entrenamiento…).
- [ ] Optimizar peso: deduplicar la imagen base embebida repetida entre músculos.
