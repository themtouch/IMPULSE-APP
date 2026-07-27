// Impulse — Edge Function "coach"
// Proxy server-side hacia NVIDIA. La NVIDIA_API_KEY vive SOLO aqui (secreto del
// servidor), nunca en el cliente. Solo responde a usuarios autenticados.
// Devuelve una rutina o dieta en JSON estructurado, listo para guardar en las
// tablas `routines` / `diets` (migracion 002).
//
// Deploy:  supabase functions deploy coach
// Secreto: supabase secrets set NVIDIA_API_KEY=nvapi-xxxxx
// (SUPABASE_URL y SUPABASE_ANON_KEY los inyecta Supabase automaticamente.)

import { serve } from "https://deno.land/std@0.224.0/http/server.ts";

const NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions";
const MODEL = "google/gemma-3n-e4b-it";

// Origenes permitidos para CORS (la app en Vercel). Ajusta si cambias de dominio.
const ALLOWED_ORIGINS = [
  "https://impulse-app-six.vercel.app",
  "http://localhost:3000",
];

function corsHeaders(origin: string | null) {
  const allow = origin && ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Vary": "Origin",
  };
}

function json(body: unknown, status: number, origin: string | null) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders(origin), "Content-Type": "application/json" },
  });
}

const SYS_ROUTINE =
  'Eres un coach de fuerza experto. Responde SOLO con JSON valido, sin markdown ni texto extra, ' +
  'con esta forma exacta: {"name": string, "items": [{"exercise": string, "sets": number, "reps": number, "notes": string}]}. ' +
  "Usa nombres de ejercicios comunes de gimnasio. Manten la rutina realista para el objetivo pedido.";

const SYS_DIET =
  'Eres un nutriologo experto. Responde SOLO con JSON valido, sin markdown ni texto extra, ' +
  'con esta forma exacta: {"name": string, "items": [{"meal": string, "foods": [string], "kcal": number, "protein": number, "carbs": number, "fat": number}]}. ' +
  "Ajusta las calorias y macros al objetivo pedido.";

serve(async (req) => {
  const origin = req.headers.get("Origin");

  if (req.method === "OPTIONS") return new Response("ok", { headers: corsHeaders(origin) });
  if (req.method !== "POST") return json({ error: "method_not_allowed" }, 405, origin);

  // 1) Requiere usuario autenticado (JWT del magic link).
  const auth = req.headers.get("Authorization") ?? "";
  if (!auth.startsWith("Bearer ")) return json({ error: "unauthorized" }, 401, origin);

  const SB_URL = Deno.env.get("SUPABASE_URL");
  const SB_ANON = Deno.env.get("SUPABASE_ANON_KEY");
  if (SB_URL && SB_ANON) {
    const who = await fetch(`${SB_URL}/auth/v1/user`, {
      headers: { Authorization: auth, apikey: SB_ANON },
    });
    if (!who.ok) return json({ error: "unauthorized" }, 401, origin);
  }

  // 2) Key del servidor.
  const key = Deno.env.get("NVIDIA_API_KEY");
  if (!key) return json({ error: "server_not_configured" }, 500, origin);

  // 3) Payload del cliente (acotado).
  let body: Record<string, unknown>;
  try { body = await req.json(); } catch { return json({ error: "bad_json" }, 400, origin); }

  const kind = body.kind === "diet" ? "diet" : "routine";
  const message = String(body.message ?? "").slice(0, 2000);
  const context = String(body.context ?? "").slice(0, 2000);
  if (!message) return json({ error: "empty_message" }, 400, origin);

  const system = kind === "routine" ? SYS_ROUTINE : SYS_DIET;
  const payload = {
    model: MODEL,
    messages: [
      { role: "system", content: system },
      { role: "user", content: context ? `${context}\n\n${message}` : message },
    ],
    temperature: 0.2,
    top_p: 0.7,
    max_tokens: 512,
    frequency_penalty: 0,
    presence_penalty: 0,
    stream: false,
  };

  // 4) Llamada a NVIDIA con la key secreta.
  let up: Response;
  try {
    up = await fetch(NVIDIA_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(payload),
    });
  } catch (_e) {
    return json({ error: "upstream_unreachable" }, 502, origin);
  }
  if (!up.ok) {
    const detail = (await up.text()).slice(0, 300);
    return json({ error: "upstream_error", status: up.status, detail }, 502, origin);
  }

  const data = await up.json();
  const content: string = data?.choices?.[0]?.message?.content ?? "";

  // 5) Intento de parseo a JSON estructurado (el cliente igual valida).
  let parsed: unknown = null;
  const m = content.match(/\{[\s\S]*\}/);
  if (m) { try { parsed = JSON.parse(m[0]); } catch { /* deja parsed=null */ } }

  return json({ kind, content, parsed }, 200, origin);
});
