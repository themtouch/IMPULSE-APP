-- ============================================================================
-- IMPULSE — Migración 002: plataforma SaaS entrenador/atleta
-- 100% ADITIVA. No borra ni altera datos existentes. Idempotente (re-ejecutable).
-- Los usuarios actuales quedan como 'athlete' y funcionan exactamente igual.
-- Correr en: Supabase -> SQL Editor -> New query -> pegar todo -> Run.
-- Requiere haber corrido antes la migración inicial (profiles/sessions/subscriptions).
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1) ROL + campos opcionales para rankings futuros
-- ---------------------------------------------------------------------------
alter table public.profiles
  add column if not exists role text not null default 'athlete'
  check (role in ('athlete','trainer'));
alter table public.profiles
  add column if not exists age int check (age between 10 and 100);
alter table public.profiles
  add column if not exists bodyweight numeric check (bodyweight > 0 and bodyweight < 400);

-- ---------------------------------------------------------------------------
-- 2) SUSCRIPCIONES: planes de entrenador (estructura + límite; SIN pagos aún)
--    Límites de referencia: starter=10, growth=50, pro=200 clientes.
--    El client_limit real lo fija el webhook de pago (fase Stripe); nunca el cliente.
-- ---------------------------------------------------------------------------
alter table public.subscriptions drop constraint if exists subscriptions_plan_check;
alter table public.subscriptions
  add constraint subscriptions_plan_check
  check (plan in ('free','normal','premium','starter','growth','pro'));
alter table public.subscriptions
  add column if not exists client_limit int not null default 0;

-- ---------------------------------------------------------------------------
-- 3) RELACIÓN ENTRENADOR <-> CLIENTE
--    client_id es NULL hasta que la persona invitada crea/acepta su cuenta.
-- ---------------------------------------------------------------------------
create table if not exists public.trainer_clients (
  id uuid primary key default gen_random_uuid(),
  trainer_id uuid not null references auth.users(id) on delete cascade,
  client_id  uuid references auth.users(id) on delete set null,
  client_email text,
  client_name  text check (char_length(client_name) <= 80),
  status text not null default 'invited' check (status in ('invited','active','inactive')),
  created_at timestamptz default now(),
  unique(trainer_id, client_email)
);
create index if not exists tc_trainer_idx on public.trainer_clients(trainer_id);
create index if not exists tc_client_idx  on public.trainer_clients(client_id);

-- ---------------------------------------------------------------------------
-- 4) RUTINAS (plantillas reutilizables construidas con la biblioteca existente)
--    El registro de sesiones actual NO cambia; esto es una plantilla asignable.
-- ---------------------------------------------------------------------------
create table if not exists public.routines (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  name text not null check (char_length(name) <= 80),
  items jsonb not null default '[]'::jsonb,  -- [{exercise_id, sets, reps, notes}]
  created_at timestamptz default now()
);
create index if not exists routines_owner_idx on public.routines(owner_id);

-- ---------------------------------------------------------------------------
-- 5) DIETAS (plantillas reutilizables)
-- ---------------------------------------------------------------------------
create table if not exists public.diets (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  name text not null check (char_length(name) <= 80),
  items jsonb not null default '[]'::jsonb,  -- [{meal, items:[...], kcal, protein, carbs, fat}]
  created_at timestamptz default now()
);
create index if not exists diets_owner_idx on public.diets(owner_id);

-- ---------------------------------------------------------------------------
-- 6) ASIGNACIONES (rutina/dieta -> cliente)
-- ---------------------------------------------------------------------------
create table if not exists public.assignments (
  id uuid primary key default gen_random_uuid(),
  trainer_id uuid not null references auth.users(id) on delete cascade,
  client_id  uuid not null references auth.users(id) on delete cascade,
  kind   text not null check (kind in ('routine','diet')),
  ref_id uuid not null,  -- routines.id o diets.id segun kind
  assigned_at timestamptz default now()
);
create index if not exists assign_client_idx  on public.assignments(client_id);
create index if not exists assign_trainer_idx on public.assignments(trainer_id);

-- ---------------------------------------------------------------------------
-- 7) COMUNIDADES (solo estructura + modelos; sin interfaz todavia)
-- ---------------------------------------------------------------------------
create table if not exists public.communities (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  name text not null check (char_length(name) <= 80),
  description text check (char_length(description) <= 500),
  created_at timestamptz default now()
);
create table if not exists public.community_members (
  community_id uuid not null references public.communities(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null default 'member' check (role in ('owner','admin','member')),
  joined_at timestamptz default now(),
  primary key (community_id, user_id)
);

-- ============================================================================
-- RLS — todo aislado. El atleta actual NO se ve afectado (policies existentes
-- intactas; RLS combina policies con OR, asi que solo AGREGAMOS accesos).
-- ============================================================================
alter table public.trainer_clients   enable row level security;
alter table public.routines          enable row level security;
alter table public.diets             enable row level security;
alter table public.assignments       enable row level security;
alter table public.communities       enable row level security;
alter table public.community_members enable row level security;

-- trainer_clients: el entrenador gestiona sus filas; el cliente ve las suyas
drop policy if exists tc_trainer_all on public.trainer_clients;
create policy tc_trainer_all on public.trainer_clients for all
  using (auth.uid() = trainer_id) with check (auth.uid() = trainer_id);
drop policy if exists tc_client_read on public.trainer_clients;
create policy tc_client_read on public.trainer_clients for select
  using (auth.uid() = client_id);

-- routines / diets: cada dueño (entrenador) gestiona lo suyo
drop policy if exists routines_owner on public.routines;
create policy routines_owner on public.routines for all
  using (auth.uid() = owner_id) with check (auth.uid() = owner_id);
drop policy if exists diets_owner on public.diets;
create policy diets_owner on public.diets for all
  using (auth.uid() = owner_id) with check (auth.uid() = owner_id);

-- el cliente puede LEER las rutinas/dietas que le asignaron
drop policy if exists routines_assigned_read on public.routines;
create policy routines_assigned_read on public.routines for select
  using (exists (select 1 from public.assignments a
                 where a.kind = 'routine' and a.ref_id = routines.id
                   and a.client_id = auth.uid()));
drop policy if exists diets_assigned_read on public.diets;
create policy diets_assigned_read on public.diets for select
  using (exists (select 1 from public.assignments a
                 where a.kind = 'diet' and a.ref_id = diets.id
                   and a.client_id = auth.uid()));

-- assignments: entrenador gestiona; cliente lee lo suyo
drop policy if exists assign_trainer_all on public.assignments;
create policy assign_trainer_all on public.assignments for all
  using (auth.uid() = trainer_id) with check (auth.uid() = trainer_id);
drop policy if exists assign_client_read on public.assignments;
create policy assign_client_read on public.assignments for select
  using (auth.uid() = client_id);

-- communities
drop policy if exists comm_owner_all on public.communities;
create policy comm_owner_all on public.communities for all
  using (auth.uid() = owner_id) with check (auth.uid() = owner_id);
drop policy if exists comm_member_read on public.communities;
create policy comm_member_read on public.communities for select
  using (exists (select 1 from public.community_members m
                 where m.community_id = communities.id and m.user_id = auth.uid()));
drop policy if exists cm_self on public.community_members;
create policy cm_self on public.community_members for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- Acceso del ENTRENADOR a datos de sus clientes ACTIVOS (policies ADITIVAS).
-- No se toca la policy del atleta: sigue viendo SOLO lo suyo. Aqui se SUMA
-- una regla extra para que el entrenador lea (nunca escriba) lo de su cliente.
-- ---------------------------------------------------------------------------
drop policy if exists "trainer reads client sessions" on public.sessions;
create policy "trainer reads client sessions" on public.sessions for select
  using (exists (select 1 from public.trainer_clients tc
                 where tc.client_id = sessions.user_id
                   and tc.trainer_id = auth.uid()
                   and tc.status = 'active'));

drop policy if exists "trainer reads client profile" on public.profiles;
create policy "trainer reads client profile" on public.profiles for select
  using (exists (select 1 from public.trainer_clients tc
                 where tc.client_id = profiles.id
                   and tc.trainer_id = auth.uid()
                   and tc.status = 'active'));

-- Fin de la migración 002.
