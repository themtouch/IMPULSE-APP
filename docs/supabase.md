# Backend Impulse en Supabase — plan de implementación

Migra la app de "datos por correo en `localStorage`" a **cuentas reales, seguras y
multi-dispositivo**, cerrando los hallazgos de [`../SECURITY.md`](../SECURITY.md).

## 1. Auth (cierra "autenticación débil")

- **Supabase Auth** con **Magic Link** y/o **OAuth Google** (el correo queda verificado).
- El cliente reemplaza el gate de correo por `supabase.auth.signInWithOtp()` /
  `signInWithOAuth({ provider: 'google' })`.
- La identidad pasa a ser `auth.uid()` (no el correo escrito a mano).

## 2. Esquema (con RLS en todas las tablas)

```sql
-- Perfil (1:1 con auth.users)
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text check (char_length(name) <= 60),
  goal text check (goal in ('Hipertrofia','Fuerza','Recomposición')),
  days int check (days between 1 and 7),
  lang text check (lang in ('es','en')) default 'es',
  created_at timestamptz default now()
);

-- Sesiones de entrenamiento
create table public.sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  date date not null,
  duration_sec int check (duration_sec >= 0) default 0,
  exercises jsonb not null,            -- [{id, muscle, muscle_sec, sets:[{w,r}]}]
  created_at timestamptz default now()
);
create index on public.sessions(user_id, date);

-- Suscripción (la ESCRIBE solo el servidor vía webhook; el cliente solo lee)
create table public.subscriptions (
  user_id uuid primary key references auth.users(id) on delete cascade,
  plan text not null check (plan in ('free','normal','premium')) default 'free',
  status text not null default 'inactive',
  current_period_end timestamptz,
  updated_at timestamptz default now()
);

alter table public.profiles      enable row level security;
alter table public.sessions      enable row level security;
alter table public.subscriptions enable row level security;
```

## 3. RLS (cierra IDOR / aislamiento de datos)

```sql
-- profiles: cada quien solo su fila
create policy "own profile read"   on public.profiles for select using (auth.uid() = id);
create policy "own profile write"  on public.profiles for insert with check (auth.uid() = id);
create policy "own profile update" on public.profiles for update using (auth.uid() = id);

-- sessions: CRUD solo de lo propio
create policy "own sessions read"   on public.sessions for select using (auth.uid() = user_id);
create policy "own sessions insert" on public.sessions for insert with check (auth.uid() = user_id);
create policy "own sessions update" on public.sessions for update using (auth.uid() = user_id);
create policy "own sessions delete" on public.sessions for delete using (auth.uid() = user_id);

-- subscriptions: el cliente SOLO lee; escribe únicamente el service_role (webhook)
create policy "own sub read" on public.subscriptions for select using (auth.uid() = user_id);
-- (sin políticas de insert/update para 'authenticated' => el cliente no puede modificar el plan)
```

## 4. Entitlements de plan (cierra "entitlement en cliente" — CRÍTICO)

- Pago con **Stripe** (web) / **RevenueCat** (móvil).
- El **webhook** (Edge Function con `SUPABASE_SERVICE_ROLE_KEY`) valida la firma
  (`STRIPE_WEBHOOK_SECRET`) y hace `upsert` en `subscriptions`.
- El cliente **nunca** escribe el plan: solo lee `subscriptions` (RLS). Se elimina el flujo actual
  que guarda `plan` en `localStorage`.

## 5. Validación server-side (Fase 1) y rate limiting (Fase 3)

- **Edge Functions** validan cada payload con `zod` antes de tocar la BD; errores genéricos.
- **Rate limiting** en auth y funciones costosas: por IP (anónimo) y por `uid` (autenticado);
  `429` + `Retry-After`. Bloqueo por N intentos fallidos (anti credential-stuffing).

## 6. Cambios en el cliente

- Sustituir `impulse.user.<correo>` (localStorage) por lecturas/escrituras a Supabase
  (`profiles`, `sessions`) filtradas por `auth.uid()` (RLS hace el resto).
- `localStorage` queda solo como caché offline opcional (no como fuente de verdad de entitlements).
- Añadir `SUPABASE_URL` de la app a `connect-src` del CSP en [`../vercel.json`](../vercel.json).

## 7. Orden sugerido

1. Auth (magic link/Google) + tabla `profiles` + RLS.
2. `sessions` + RLS; migrar el registro de series a Supabase.
3. `subscriptions` + webhook Stripe/RevenueCat (entitlements en servidor).
4. Edge Functions con validación `zod` + rate limiting.
5. Endurecer CSP (sin `'unsafe-inline'`) y añadir dominio Supabase a `connect-src`.
