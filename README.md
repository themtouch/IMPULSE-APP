# Impulse App

**Impulse** es una app de entrenamiento **funcional** cuyo eje es un **modelo corporal
interactivo** reconstruido a partir de SVG anatómicos reales. Entras con tu correo, registras
tus series, y cada músculo del modelo **se ilumina y sube de jerarquía** (Iniciado → Élite)
según los kilos × repeticiones que acumulas. El modelo **arranca en blanco**: nada se ilumina
hasta que registras datos.

> *"Tu entrenamiento se adapta a tu físico, no al revés."*

- **App:** `index.html` (~290 KB) + biblioteca de **1,324 ejercicios con video** (`data/exercises.json`).
- **Bilingüe** español / inglés, con selector al inicio.
- **Datos por correo**, guardados en el dispositivo (localStorage), sin backend.

---

## Tabla de contenido

- [Cómo usarla](#cómo-usarla)
- [Login y datos por correo](#login-y-datos-por-correo)
- [Funcionalidad](#funcionalidad)
- [Motor de jerarquías (empieza en blanco)](#motor-de-jerarquías-empieza-en-blanco)
- [Biblioteca de ejercicios (dataset)](#biblioteca-de-ejercicios-dataset)
- [Planes y pagos](#planes-y-pagos)
- [Idiomas](#idiomas)
- [Qué hay en este repo](#qué-hay-en-este-repo)
- [El modelo corporal](#el-modelo-corporal)
- [Design system](#design-system)
- [Build](#build)
- [Desplegar en Vercel](#desplegar-en-vercel)
- [Build iOS (10x app / Xcode)](#build-ios-10x-app--xcode)
- [Camino a producción](#camino-a-producción)
- [Roadmap](#roadmap)

---

## Cómo usarla

La biblioteca completa (1,324 ejercicios) se carga desde `data/exercises.json`, así que la app
**debe servirse por HTTP** para verla completa:

- **Recomendado — Vercel:** despliega el repo ([abajo](#desplegar-en-vercel)) y ábrela en el teléfono.
- **Local:** `python3 -m http.server 8000` en la raíz del repo → `http://localhost:8000`.
- **Archivo suelto (`file://`):** funciona con un set de respaldo de 13 ejercicios embebido
  (sin el catálogo completo, porque `file://` no puede hacer `fetch` del JSON).

---

## Login y datos por correo

Para entrar **se pide un correo** (Gmail o cualquiera). Cada correo tiene su **espacio de datos
propio** (`localStorage: impulse.user.<correo>`): perfil, sesiones, plan y métricas se trackean
por usuario. Cambiar de correo carga otra cuenta; *Cerrar sesión* vuelve al login.

> Es identificación local por correo (sin servidor). Para **auth real multi-dispositivo** se
> necesita backend + OAuth (Google) — ver [Camino a producción](#camino-a-producción).

---

## Funcionalidad

| Pantalla | Qué hace |
|---|---|
| **Login** | Correo + selector de idioma (ES/EN). Crea o carga tu cuenta. |
| **Onboarding** | Nombre, objetivo y días/semana. **No siembra el modelo** (arranca en blanco). |
| **Inicio** | Saludo, nivel, racha, sesiones de la semana, volumen total, próxima sesión (rezagados) y actividad reciente. |
| **Entrenar** | Rutina recomendada (prioriza rezagados), sesión en blanco, o empezar por grupo muscular. |
| **Sesión activa** | Registro de series (peso × reps), añadir series/ejercicios desde el catálogo, cronómetro, guardar. |
| **Físico** | Modelo frente/espalda; músculos **apagados** hasta tener datos, luego pintados por rango; toca uno para ver volumen, rango y progreso; rezagados; barras de todos. |
| **Biblioteca** | **1,324 ejercicios** con GIF, filtro por músculo y buscador; detalle con video + instrucciones (idioma elegido); añadir a la sesión. |
| **Ascenso** | Celebración full-screen cuando un músculo sube de rango. |
| **Perfil / Planes** | Cuenta, idioma, plan; paywall Normal $500 / Premium $1000; exportar datos; cerrar sesión; borrar datos. |

---

## Motor de jerarquías (empieza en blanco)

Todo persiste en `localStorage` bajo `impulse.user.<correo>`:

```jsonc
{
  "email": "tucorreo@gmail.com",
  "profile": { "name": "...", "goal": "...", "days": 4 },
  "onboarded": true,
  "plan": "free",           // free | normal | premium
  "sessions": [
    { "date": "2026-07-25", "durationSec": 0,
      "exercises": [ { "id": "0025", "muscle": "pecho", "muscle_sec": ["triceps"],
                       "sets": [ { "w": "60", "r": "10" } ] } ] }
  ]
}
```

**Reglas:**

- **Sin datos = sin iluminar.** Un músculo con volumen 0 se muestra apagado (`—`), no se le
  asigna rango. El modelo se enciende solo con lo que registras.
- **Volumen por músculo** = Σ (peso × reps). El ejercicio suma 100 % al músculo primario y
  50 % a los secundarios (mapeados desde el dataset).
- **Rango (tier)** por umbrales de volumen acumulado:
  | Tier | Nombre | Umbral (kg) |
  |---|---|---|
  | — | Sin datos | 0 |
  | E | Iniciado | ≥ 1 |
  | D | Bronce | 2 500 |
  | C | Plata | 8 000 |
  | B | Oro | 18 000 |
  | A | Élite | 36 000 |
- **Rezagados**, **racha**, **semana**, **nivel** y **detección de ascenso** se derivan de las sesiones.

---

## Biblioteca de ejercicios (dataset)

Los ejercicios vienen del dataset público
[`hasaneyldrm/exercises-dataset`](https://github.com/hasaneyldrm/exercises-dataset)
(© Gym visual), procesado a `data/exercises.json`:

- **1,324 ejercicios**, todos los campos originales.
- Instrucciones reducidas a **español + inglés** (el dataset trae 10 idiomas).
- Cada ejercicio lleva un campo `muscle` (mapeado a los 13 músculos del modelo) y `muscle_sec`.
- **GIF e imagen** se cargan desde el repo fuente vía
  `raw.githubusercontent.com/...` (constante `MEDIA` en el código; para tráfico alto, cambiar a
  un CDN como jsDelivr o auto-hospedar).

Son **usables tal como vienen**: agregables a la rutina y al registro de métricas; al loguear
una serie, el volumen se atribuye al músculo del ejercicio y actualiza el modelo.

---

## Planes y pagos

- **Normal — $500 MXN/mes** · **Premium — $1000 MXN/mes.**
- Al elegir un plan se pide **confirmar el correo** (re-login): los beneficios se otorgan a esa
  cuenta (`plan` en el usuario). Es un flujo **demo** — no cobra; integrar **RevenueCat/Stripe**
  para producción.

---

## Idiomas

Español e inglés, con selector en el **login** y en **Perfil**. Toda la interfaz se traduce en
caliente (diccionario `T` + `data-i18n`); las instrucciones de cada ejercicio se muestran en el
idioma elegido (con respaldo al inglés).

---

## Qué hay en este repo

```
impulse-app/
├── index.html                 # ← LA APP funcional (mobile-first, ~290 KB)
├── data/exercises.json         # 1,324 ejercicios (es+en) — la biblioteca
├── vercel.json                 # config de deploy estático
├── project.yml + ios/          # contenedor iOS (SwiftUI + WKWebView) para 10x app / Xcode
├── src/
│   ├── app-template.html       # fuente de la app (se compila a index.html)
│   └── template.html           # fuente de la landing
├── scripts/
│   ├── build.py                # inyecta modelo + fallback en las plantillas
│   ├── shrink.py               # deduplica/comprime la imagen base
│   ├── fallback.json           # 13 ejercicios de respaldo (uso file://)
│   └── test-app.cjs            # prueba funcional headless
├── assets/
│   ├── svg/ · stencils/        # 18 SVG originales (verbatim) + 16 stencils
│   └── svg-lite/body.jpg       # imagen base compartida, comprimida
├── docs/ (geometry.md · landing.html · screenshots/)
└── README.md
```

---

## El modelo corporal

Los 18 SVG **no son dibujos independientes**: todos incrustan el **mismo render de cuerpo
completo** (1402 × 1122 px). Cada archivo es un recorte enmascarado; su posición está en el
`x`/`y` del `<rect>`. Se reconstruye posicionando cada músculo por porcentaje relativo al
bounding box de su figura (frente/espalda). La app incrusta la imagen **una sola vez** y muestra
frente/espalda por recorte + silueta CSS; cada músculo usa su contorno (`stencils/`) como
`mask-image` para pintar el rango. **Nada se redibujó.** Detalle en [`docs/geometry.md`](docs/geometry.md).

Los músculos iluminados llevan un borde oscuro (drop-shadow) para separar cada sección, y la
paleta de rangos es de colores **vivos e intensos**.

---

## Design system

| Token | Valor |
|---|---|
| Fondo / Superficie / Elevado | `#0E0F12` / `#181A1F` / `#20242B` |
| Texto / Acento | `#F6F8FA` / `#37C6F4` (+ `#22E3B0`) |
| Radio | `16px` · SF Pro (system stack), números tabulares |
| Tiers (vivos) | A `#3ED0FF` · B `#FFCA3A` · C `#B8C6D6` · D `#FF8A3D` · E `#8A97A6` · apagado `#2A313A` |

---

## Build

```bash
python3 scripts/shrink.py    # genera assets/svg-lite/body.jpg
python3 scripts/build.py     # compila src/app-template.html → index.html
```

Requiere Python 3 (+ Pillow para `shrink.py`). *(build.py espera los assets junto a él; en el
repo están separados por claridad — el `index.html` ya viene compilado.)*

---

## Desplegar en Vercel

`index.html` + `data/exercises.json` son estáticos:

1. Vercel → **Add New → Project → Import** el repo `themtouch/impulse-app`.
2. Framework: **Other** · Root: `/` · sin build command.
3. **Deploy** → URL usable en el teléfono. Activa **Vercel Web Analytics** para métricas de uso.

Cada push a `main` redeploya. *(La biblioteca completa necesita este deploy — o un servidor
local — porque carga `data/exercises.json` por `fetch`.)*

---

## Build iOS (10x app / Xcode)

`project.yml` ([XcodeGen](https://github.com/yonaskolb/XcodeGen)) genera el proyecto; la app iOS
es un contenedor **SwiftUI + WKWebView** (`ios/Impulse/`) que carga `index.html`.

```bash
brew install xcodegen && xcodegen generate && open Impulse.xcodeproj
```

Sin red, iOS muestra el set de respaldo; para el catálogo completo, empaquetar `data/` o
apuntar a la URL de Vercel.

---

## Camino a producción

Para lanzar con **métricas serias, control de versiones y control total**:

- **Auth real:** backend + OAuth (Google) para cuentas multi-dispositivo (hoy es por correo local).
- **Base de código:** este repo → **Expo (React Native)** iOS + Android, o SwiftUI nativo.
- **Métricas:** PostHog / Firebase / Amplitude. **Pagos:** RevenueCat + Stripe.
- **Media:** auto-hospedar los GIF o servirlos por CDN (jsDelivr) en vez de `raw.githubusercontent`.

---

## Roadmap

- [ ] Auth real (OAuth) y sincronización en la nube.
- [ ] Portar el modelo a componente React/Expo.
- [ ] Conectar analytics + RevenueCat/Stripe.
- [ ] Gráficas de volumen por músculo en el tiempo.
- [ ] Nombres de ejercicios en español (el dataset trae nombre solo en inglés).

---

*Ejercicios: © Gym visual — https://gymvisual.com/ (vía hasaneyldrm/exercises-dataset).*
