# Impulse App

**Impulse** es una app de entrenamiento **funcional** cuyo eje es un **modelo corporal
interactivo** reconstruido a partir de SVG anatómicos reales. Registras tus series, y cada
músculo del modelo **sube de jerarquía** (Iniciado → Élite) según el volumen que acumulas.
El plan manda el volumen extra a lo que va rezagado.

> *"Tu entrenamiento se adapta a tu físico, no al revés."*

La app (`index.html`) es un **único archivo autocontenido (~256 KB)**: funciona offline, guarda
tus datos en el dispositivo (localStorage), sin backend ni dependencias externas.

---

## Tabla de contenido

- [Cómo usarla ya](#cómo-usarla-ya)
- [Funcionalidad](#funcionalidad)
- [Registro de datos y motor de jerarquías](#registro-de-datos-y-motor-de-jerarquías)
- [Qué hay en este repo](#qué-hay-en-este-repo)
- [El modelo corporal: cómo está reconstruido](#el-modelo-corporal-cómo-está-reconstruido)
- [Design system](#design-system)
- [Build](#build)
- [Desplegar en Vercel (URL + métricas)](#desplegar-en-vercel-url--métricas)
- [Build iOS (10x app / Xcode)](#build-ios-10x-app--xcode)
- [Camino a producción](#camino-a-producción)
- [Roadmap](#roadmap)

---

## Cómo usarla ya

Tres formas:

1. **Abrir el archivo:** abre `index.html` en cualquier navegador (o en el teléfono: descárgalo
   y ábrelo en Safari/Chrome → *Añadir a pantalla de inicio* para usarlo como app offline).
2. **Servir local:** `python3 -m http.server 8000` → `http://localhost:8000`.
3. **Vercel:** despliega el repo para tener una URL usable en el teléfono ([abajo](#desplegar-en-vercel-url--métricas)).

---

## Funcionalidad

App mobile-first con navegación por tabs. Pantallas:

| Pantalla | Qué hace |
|---|---|
| **Registro (onboarding)** | Nombre, edad, género, experiencia y objetivo → crea tu perfil y **calibra el modelo corporal inicial** (la experiencia siembra el volumen base por músculo). |
| **Inicio (dashboard)** | Saludo, **nivel**, racha, sesiones de la semana, volumen total, próxima sesión sugerida (según rezagados) y actividad reciente. Todo calculado de tus datos. |
| **Entrenar** | Rutina recomendada (prioriza rezagados) o empezar por grupo muscular. |
| **Sesión activa** | **Registro de series**: peso × reps por serie, añadir series/ejercicios, cronómetro, guardar. |
| **Físico (modelo corporal)** | Modelo interactivo frente/espalda pintado por jerarquía; toca un músculo para ver volumen, rango y progreso; lista de rezagados; barras de todos los músculos. |
| **Biblioteca** | 37 ejercicios mapeados a músculos primarios/secundarios, con buscador. |
| **Ascenso de jerarquía** | Celebración full-screen cuando un músculo sube de rango tras guardar una sesión. |
| **Perfil / Paywall** | Perfil, estado Pro, paywall Impulse Pro (demo), exportar datos (JSON) y reiniciar. |

---

## Registro de datos y motor de jerarquías

Todo persiste en `localStorage` bajo la clave `impulse.v1`:

```jsonc
{
  "profile": { "name": "...", "age": "...", "sex": "...", "exp": "1-3", "goal": "...", "days": 4 },
  "onboarded": true,
  "pro": false,
  "base":     { "pecho": 12000, "espalda": 9000, ... },   // baseline por experiencia
  "sessions": [
    { "date": "2026-07-25", "ts": 0, "durationSec": 0,
      "exercises": [ { "id": "press-banca", "sets": [ { "w": "60", "r": "10" } ] } ] }
  ]
}
```

**Motor determinista:**

- **Volumen por músculo** = `base` + Σ (peso × reps) de cada serie. El ejercicio suma al músculo
  primario y al 50 % a los secundarios.
- **Jerarquía (tier)** por umbrales de volumen acumulado:
  | Tier | Nombre | Umbral (kg) |
  |---|---|---|
  | E | Iniciado | 0 |
  | D | Bronce | 2 500 |
  | C | Plata | 8 000 |
  | B | Oro | 18 000 |
  | A | Élite | 36 000 |
- **Rezagados** = músculos por debajo de tu tier promedio, ordenados por menor volumen.
- **Racha**, **sesiones de la semana**, **nivel** (`1 + √(volumen/900)`) y **detección de
  ascenso** (comparación de tier antes/después de guardar) se derivan de las sesiones.

Cada sesión que registras recalcula el modelo y puede disparar un **ascenso de jerarquía**.

---

## Qué hay en este repo

```
impulse-app/
├── index.html                 # ← LA APP funcional (autocontenida, offline, ~256 KB)
├── vercel.json                # config de deploy estático
├── project.yml                # spec XcodeGen → proyecto iOS (10x app / Xcode)
├── ios/Impulse/               # contenedor iOS nativo (SwiftUI + WKWebView) que carga index.html
├── src/
│   ├── app-template.html      # plantilla de la app (fuente; se compila a index.html)
│   └── template.html          # plantilla de la landing/preview
├── scripts/
│   ├── build.py               # inyecta modelo (base compartida + stencils) en las plantillas
│   ├── shrink.py              # deduplica y comprime la imagen base compartida
│   └── test-app.cjs           # prueba funcional headless (Playwright)
├── assets/
│   ├── svg/                   # 18 SVG originales del usuario (VERBATIM)
│   ├── stencils/              # 16 stencils de máscara por músculo
│   └── svg-lite/body.jpg      # imagen base compartida, downscaled (una sola vez)
├── docs/
│   ├── geometry.md            # tabla de offsets y bounding boxes
│   ├── landing.html           # landing/preview de interfaz
│   └── screenshots/           # renders (app-* = app funcional)
└── README.md
```

---

## El modelo corporal: cómo está reconstruido

Los 18 SVG **no son dibujos independientes**: todos incrustan **el mismo render de cuerpo
completo** (1402 × 1122 px, figura de frente a la izquierda y de espalda a la derecha), y cada
archivo es un **recorte enmascarado** de esa imagen compartida. La posición del recorte está en
el `x`/`y` del `<rect>`.

**Reconstrucción (sin recrear nada):** cada músculo se posiciona por porcentaje relativo al
bounding box de su figura:

```
left = (X − OX)/VW·100 %   top = (Y − OY)/VH·100 %   width = W/VW·100 %   height = H/VH·100 %
```

| Figura  | OX      | OY   | VW  | VH   |
|---------|---------|------|-----|------|
| Frente  | 91.5    | 31.5 | 561 | 1029 |
| Espalda | 694.492 | 34.5 | 605 | 1025 |

Como los 18 SVG embeben la **misma** imagen, la app la incrusta **una sola vez** (`svg-lite/body.jpg`)
y muestra frente/espalda por recorte CSS, clipando a la silueta con la máscara de contorno. De
cada músculo se usa su contorno (`assets/stencils/`) como `mask-image` para pintar el color de
jerarquía. Tabla completa en [`docs/geometry.md`](docs/geometry.md). **Nada se redibujó.**

---

## Design system

| Token | Valor |
|---|---|
| Fondo / Superficie / Elevado | `#121212` / `#1E1E1E` / `#242424` |
| Texto / Acento (candy blue) | `#F5F5F5` / `#B2D5E5` |
| Radio | `16px` · Tipografía SF Pro (system stack), números tabulares |
| Tiers | A `#B2D5E5` · B `#E0BE63` · C `#A6B2BD` · D `#C08552` · E `#6B7280` |

---

## Build

```bash
python3 scripts/shrink.py    # genera assets/svg-lite/body.jpg (imagen base compartida)
python3 scripts/build.py     # compila src/app-template.html → index.html
python3 scripts/test-app.cjs # (opcional) prueba funcional headless
```

Solo requiere Python 3 (+ Pillow para `shrink.py`). El test usa Node + Playwright.

---

## Desplegar en Vercel (URL + métricas)

`index.html` es estático y autocontenido, así que el deploy es directo:

1. En Vercel → **Add New → Project → Import** el repo `themtouch/impulse-app`.
2. Framework preset: **Other** (sitio estático). Root directory: `/`. Sin build command.
3. **Deploy** → obtienes una URL usable en el teléfono.
4. Activa **Vercel Web Analytics** (o integra PostHog/Firebase) para métricas de uso reales.

Cada push a `main` redeploya automáticamente.

---

## Build iOS (10x app / Xcode)

Para iOS, el repo trae **`project.yml`** ([XcodeGen](https://github.com/yonaskolb/XcodeGen)) —
uno de los archivos que 10x app busca. La app iOS es un contenedor **SwiftUI + WKWebView**
(`ios/Impulse/`) que carga `index.html` desde el bundle (offline).

```bash
brew install xcodegen && xcodegen generate && open Impulse.xcodeproj   # ⌘R para correr
```

Target: `com.themtouch.impulse`, iOS 16+, vertical, tema oscuro.

> El WebView es el camino rápido para probar en dispositivo. Para tienda, valora una app
> nativa/Expo (ver abajo): Apple puede rechazar wrappers de web muy simples (guía 4.2).

---

## Camino a producción

Para lanzar con **métricas serias, control de versiones y control total** (recomendado):

- **Base de código propia** en este repo (ya está) → **Expo (React Native)** para iOS + Android
  con una sola base, o SwiftUI nativo si es solo iOS.
- **Métricas:** PostHog / Firebase / Amplitude (eventos, embudos, retención).
- **Suscripciones:** RevenueCat + Stripe para el paywall.
- **Versionado / releases:** EAS Build & Submit + OTA updates.

Esta app web funcional sirve de **prototipo jugable y spec viva** de todo el producto.

---

## Roadmap

- [ ] Portar el modelo corporal a **componente React/Expo** (`AnimatedBodyModel`).
- [ ] Conectar **analytics** y RevenueCat/Stripe.
- [ ] GIFs de ejecución y detalle de ejercicio en la biblioteca.
- [ ] Historial y progreso a largo plazo (gráficas de volumen por músculo).
- [ ] Sincronización en la nube (hoy los datos viven solo en el dispositivo).
