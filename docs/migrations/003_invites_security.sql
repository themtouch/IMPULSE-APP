-- ============================================================================
-- IMPULSE — Migración 003: invitaciones coach -> cliente + cierre de hueco RLS
-- 100% ADITIVA e idempotente. No borra datos.
--
-- Problema que corrige:
--   1) La policy tc_trainer_all deja que el entrenador escriba client_id y
--      status='active' en sus filas. Con eso podía apuntar a CUALQUIER usuario
--      y leer sus sesiones/perfil sin su permiso.
--   2) No existía forma de que el cliente invitado aceptara la invitación,
--      así que client_id quedaba NULL para siempre y el panel de coach no
--      podía ver ni asignar nada.
-- ============================================================================

-- 1) El entrenador NO puede fijar client_id ni activar la relación por su cuenta.
--    Solo el propio cliente la activa (vía respond_invite, abajo).
create or replace function public.tc_guard()
returns trigger language plpgsql as $$
begin
  if auth.uid() is not null and auth.uid() = new.trainer_id then
    if tg_op = 'INSERT' then
      new.client_id := null;
      if new.status = 'active' then new.status := 'invited'; end if;
    else
      new.client_id := old.client_id;
      if new.status = 'active' and old.status <> 'active' then new.status := old.status; end if;
    end if;
    new.client_email := lower(new.client_email);
  end if;
  return new;
end $$;

drop trigger if exists tc_guard on public.trainer_clients;
create trigger tc_guard before insert or update on public.trainer_clients
  for each row execute function public.tc_guard();

-- 2) El cliente ve sus invitaciones pendientes (por correo) con el nombre del coach.
create or replace function public.my_invites()
returns table (id uuid, trainer_name text, created_at timestamptz)
language sql security definer set search_path = public as $$
  select tc.id, coalesce(p.name, 'Coach'), tc.created_at
  from public.trainer_clients tc
  left join public.profiles p on p.id = tc.trainer_id
  where tc.status = 'invited'
    and tc.client_id is null
    and lower(tc.client_email) = lower(auth.jwt() ->> 'email')
    and tc.trainer_id <> auth.uid()
  order by tc.created_at desc;
$$;

-- 3) El cliente acepta o rechaza. Solo funciona si la invitación es para SU correo.
create or replace function public.respond_invite(p_id uuid, p_accept boolean)
returns boolean
language plpgsql security definer set search_path = public as $$
declare n int;
begin
  if auth.uid() is null then return false; end if;
  if p_accept then
    update public.trainer_clients
       set client_id = auth.uid(), status = 'active'
     where id = p_id and status = 'invited' and client_id is null
       and lower(client_email) = lower(auth.jwt() ->> 'email');
  else
    update public.trainer_clients
       set status = 'inactive'
     where id = p_id and status = 'invited' and client_id is null
       and lower(client_email) = lower(auth.jwt() ->> 'email');
  end if;
  get diagnostics n = row_count;
  return n > 0;
end $$;

revoke all on function public.my_invites() from public, anon;
revoke all on function public.respond_invite(uuid, boolean) from public, anon;
grant execute on function public.my_invites() to authenticated;
grant execute on function public.respond_invite(uuid, boolean) to authenticated;

-- 4) El cliente puede desvincularse de su coach en cualquier momento.
drop policy if exists tc_client_leave on public.trainer_clients;
create policy tc_client_leave on public.trainer_clients for update
  using (auth.uid() = client_id) with check (auth.uid() = client_id and status = 'inactive');

-- Fin de la migración 003.
