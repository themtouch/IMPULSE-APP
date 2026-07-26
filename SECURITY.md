# Auditoría de seguridad — Impulse

Auditoría ofensivo-defensiva del codebase actual (app estática client-side; backend planeado en
**Supabase**). Cada hallazgo lleva ubicación, severidad y riesgo real. Los fixes aplicables al
cliente ya están hechos; los que dependen del backend quedan documentados como **requisitos
Supabase** (ver [`docs/supabase.md`](docs/supabase.md)).

Estado del stack hoy: `index.html` (una sola página, HTML/CSS/JS inline) + `data/exercises.json`
(catálogo público) + `localStorage` por correo. **Aún no hay servidor**, así que la superficie de
inyección server-side todavía no existe — pero se dejan definidos los controles para cuando entre
Supabase.

---

## FASE 1 — Inyecciones

### SQL / ORM
- **Estado:** N/A (sin backend). No hay queries en el código.
- **Requisito Supabase (alta):** usar exclusivamente el cliente `supabase-js` (consultas
  parametrizadas). Nunca construir SQL por concatenación en `rpc()`/funciones. Habilitar **RLS**
  en todas las tablas. Evitar *second-order*: validar también datos que se guardan y luego se
  reutilizan (ej. `display_name`).

### Validación de inputs
- **Hallazgo (media)** — `index.html` (login/onboarding): la validación es solo de cliente
  (`validEmail`, `input required`). La validación de cliente **no cuenta** como control.
- **Requisito Supabase:** validar en servidor cada dato externo (Edge Functions con `zod`, y
  *constraints*/`check` en Postgres). Errores hacia el exterior **genéricos** (no revelar qué
  campo falló ni por qué).

### XSS y manipulación del DOM  — **CORREGIDO**
- **Hallazgo (alta)** — `src/app-template.html` (render de biblioteca, picker, sesión, inicio,
  entrenar): nombres/`equipment`/`target` provenientes del **dataset externo** se interpolaban en
  `innerHTML` **sin escapar**. Un registro con `name = "<img src=x onerror=…>"` ejecutaba JS
  (stored/DOM XSS).
- **Fix aplicado:**
  - `esc()` — escapa `& < > " ' \`` en toda cadena externa/usuario antes de `innerHTML`.
  - `safeURL()` — sanea URLs usadas en `src=""` (solo `http(s)`/relativas; bloquea `javascript:`,
    breakout de atributo).
  - Aplicado en **todos** los puntos de render con datos del dataset.
- **Verificación:** inyectado un ejercicio `name:"<img src=x onerror=window.__xss=1>"` →
  se renderiza como **texto** (`&lt;img …`), `window.__xss` queda `undefined`, 0 ejecución.
- **Nota:** el resto del texto de UI proviene del diccionario i18n y de `textContent` (seguros).

### Security headers  — **CORREGIDO**
- **Fix aplicado** en [`vercel.json`](vercel.json), en todas las respuestas:
  - `Content-Security-Policy` acotado al stack real (self; `img-src` limitado a `data:` +
    `raw.githubusercontent.com`/`cdn.jsdelivr.net`; `connect-src` self + raw; `object-src 'none'`;
    `frame-ancestors 'none'`; `base-uri 'self'`; `form-action 'self'`).
  - `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
    `Referrer-Policy: strict-origin-when-cross-origin`,
    `Permissions-Policy` (geolocation/camera/microphone/payment/usb deshabilitados),
    `Strict-Transport-Security` (HSTS con preload).
- **Deuda técnica (media):** el CSP incluye `'unsafe-inline'` en `script-src`/`style-src` porque la
  app es un único archivo inline. Endurecer moviendo JS/CSS a archivos externos con **nonce/hash**.
  Cuando entre Supabase, añadir su dominio a `connect-src`.

---

## FASE 2 — Secrets y variables de entorno

- **Escaneo:** sin secretos hardcodeados. No hay API keys, tokens, JWT secrets, connection strings
  ni webhook secrets en código, comentarios, config, tests ni CI. La constante `MEDIA` es una URL
  **pública**.
- **Logs:** la app no expone secretos ni stack traces al cliente (no hay `console.log` de datos
  sensibles).
- **Requisito Supabase:**
  - `SUPABASE_URL` y `SUPABASE_ANON_KEY` vía **variables de entorno** (la anon key es pública por
    diseño, pero se gestiona como env). Ver [`.env.example`](.env.example).
  - **`SUPABASE_SERVICE_ROLE_KEY` jamás en el cliente** — solo en Edge Functions/servidor.
  - `.env`, `.env.local` ya cubiertos por [`.gitignore`](.gitignore).
  - Estrategia de rotación: rotar `service_role` y secretos de webhooks (Stripe/RevenueCat) ante
    cualquier exposición; usar el gestor de secretos de Vercel/Supabase, no el repo.

---

## FASE 3 — Rate limiting

- **Estado:** N/A en cliente (no hay endpoints propios).
- **Requisito Supabase:**
  - Auth (login/magic-link/OTP/reset): límite **por IP** (no autenticados) y **por usuario**
    (autenticados). Supabase Auth trae límites base; reforzar en Edge Functions.
  - Endpoints/Edge Functions costosos: límite + degradación progresiva.
  - Respuesta al exceder: `429 Too Many Requests` + `Retry-After`, sin filtrar la lógica interna.
  - **Credential stuffing:** bloquear IP tras N intentos fallidos, no solo throttling.

---

## Hallazgos adicionales

1. **Entitlement enforcement en el cliente — CRÍTICA (negocio).**
   `index.html`: el plan (`normal`/`premium`) se otorga y guarda en `localStorage`. Cualquiera
   puede editar `localStorage` y activarse **Premium gratis**. El estado del plan **no debe vivir
   ni validarse en el cliente**.
   **Fix requerido:** entitlements en servidor — RevenueCat/Stripe → webhook → tabla
   `subscriptions` en Supabase con RLS; el cliente solo **lee** su estado, nunca lo escribe. El
   pago actual es demo y está etiquetado como tal.

2. **Autenticación débil — ALTA.**
   El "login" es solo un correo, sin verificación ni contraseña → suplantación trivial de otra
   cuenta y de sus métricas.
   **Fix requerido:** Supabase Auth con **magic link** o **OAuth (Google)** y verificación de
   correo. Hasta entonces, es identificación local por dispositivo (documentado en el README).

3. **IDOR / aislamiento de datos — ALTA (al añadir backend).**
   **Fix requerido:** RLS por `auth.uid()` en cada tabla; cada usuario solo lee/escribe sus filas.

4. **Datos en `localStorage` sin cifrar — MEDIA.**
   Accesibles con acceso físico al dispositivo o desde el mismo origen. Aceptable para métricas no
   sensibles; **no** guardar ahí datos sensibles ni tokens de sesión de larga vida.

5. **Dependencia de terceros (media) — GIF desde `raw.githubusercontent`.**
   Integridad/disponibilidad fuera de nuestro control. Recomendado: auto-hospedar o CDN propio.

6. **Clickjacking — mitigado** con `X-Frame-Options: DENY` + `frame-ancestors 'none'`.

---

## Checklist de verificación

- [x] XSS: payload `<img onerror>` en datos del dataset se renderiza como texto (verificado).
- [x] `safeURL()` bloquea `javascript:` / breakout en `src`.
- [x] Security headers presentes en todas las respuestas (`vercel.json`).
- [x] Sin secretos en el repo; `.env*` en `.gitignore`; `.env.example` documentado.
- [ ] (Backend) RLS activo en todas las tablas Supabase.
- [ ] (Backend) Validación server-side por endpoint (zod + constraints).
- [ ] (Backend) Entitlements de plan validados en servidor (webhook), no en cliente.
- [ ] (Backend) Auth real (magic link/OAuth) con verificación de correo.
- [ ] (Backend) Rate limiting en auth + Edge Functions (429 + Retry-After).
- [ ] (Prod) CSP sin `'unsafe-inline'` (JS/CSS externos con nonce/hash).

Plan de implementación del backend: [`docs/supabase.md`](docs/supabase.md).
