# Edge Function `coach` — chatbot de rutinas y dietas

Proxy server-side hacia NVIDIA (`google/gemma-3n-e4b-it`). La `NVIDIA_API_KEY`
vive **solo en el servidor** como secreto; jamás llega al cliente. Solo responde
a usuarios autenticados (JWT del magic link) y devuelve JSON estructurado listo
para guardar en `routines` / `diets`.

## Desplegar

### Opción A — Dashboard (sin instalar nada)
1. Supabase → **Edge Functions** → **Deploy a new function** → nombre: `coach`.
2. Pega el contenido de [`index.ts`](index.ts) → **Deploy**.
3. Supabase → **Edge Functions** → **Secrets** (o Project Settings → Edge Functions)
   → **Add secret**: `NVIDIA_API_KEY` = tu key de NVIDIA (`nvapi-...`). Guardar.
   > `SUPABASE_URL` y `SUPABASE_ANON_KEY` los inyecta Supabase automáticamente.

### Opción B — CLI
```bash
supabase login
supabase link --project-ref ktmtiekavogqwgridiyx
supabase secrets set NVIDIA_API_KEY=nvapi-xxxxxxxx
supabase functions deploy coach
```

## Probar (con un access_token de un usuario logueado)
```bash
curl -i -X POST \
  "https://ktmtiekavogqwgridiyx.supabase.co/functions/v1/coach" \
  -H "Authorization: Bearer <ACCESS_TOKEN_DEL_USUARIO>" \
  -H "apikey: <PUBLISHABLE_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"kind":"routine","message":"Rutina push/pull/legs 4 dias para hipertrofia, nivel intermedio"}'
```
Respuesta: `{ "kind":"routine", "content":"...", "parsed": { "name":..., "items":[...] } }`.

## Contrato (lo que la app enviará)
- `kind`: `"routine"` | `"diet"`
- `message`: petición en lenguaje natural (máx 2000 chars)
- `context`: opcional (objetivo/días/nivel del cliente)

## Endurecer (recomendado antes de lanzar)
- **Rate limiting** por `uid` (tabla `ai_usage` + conteo por ventana; responder `429`).
- Restringir `ALLOWED_ORIGINS` al dominio final de producción.
- Registrar consumo para control de costo.
