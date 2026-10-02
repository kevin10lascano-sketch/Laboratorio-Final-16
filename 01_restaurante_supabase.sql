-- ============================================================
-- PROYECTO: Sistema de Gestion de Restaurante
-- FASE 1: Base de datos PostgreSQL para Supabase
-- Archivo: restaurante_supabase.sql
-- ============================================================
--
-- Resumen tecnico corto
-- ------------------------------------------------------------
-- Tablas creadas:
--   perfiles, empleados, clientes, mesas, categorias, productos,
--   movimientos_inventario, pedidos, detalle_pedido, pagos.
--
-- Proposito:
--   perfiles enlaza Supabase Auth con el rol de la aplicacion.
--   empleados guarda informacion laboral y puede apuntar a un perfil.
--   clientes incluye un unico registro semilla de Consumidor Final.
--   mesas controla disponibilidad fisica del restaurante.
--   categorias y productos organizan el menu vendible.
--   pedidos y detalle_pedido registran la cuenta y precios historicos.
--   pagos registra el pago principal de un pedido.
--   movimientos_inventario audita entradas, ventas y ajustes.
--
-- Relaciones principales:
--   perfiles.id -> auth.users.id
--   empleados.perfil_id -> perfiles.id
--   productos.categoria_id -> categorias.id
--   pedidos.cliente_id -> clientes.id
--   pedidos.mesa_id -> mesas.id
--   pedidos.mesero_id -> perfiles.id
--   detalle_pedido.pedido_id -> pedidos.id
--   detalle_pedido.producto_id -> productos.id
--   pagos.pedido_id -> pedidos.id
--   pagos.cajero_id -> perfiles.id
--   movimientos_inventario.producto_id -> productos.id
--   movimientos_inventario.usuario_id -> perfiles.id
--   movimientos_inventario.pedido_id -> pedidos.id
--
-- Reglas criticas protegidas:
--   una mesa no puede tener mas de un pedido activo;
--   al abrir un pedido la mesa pasa a OCUPADA;
--   al pagar o cancelar un pedido la mesa vuelve a LIBRE;
--   no se agregan productos inactivos;
--   el stock nunca queda negativo al confirmar un pedido;
--   confirmar pedido descuenta inventario y genera SALIDA_VENTA;
--   el precio_unitario se conserva historicamente en detalle_pedido;
--   pedidos PAGADOS o CANCELADOS quedan bloqueados contra cambios normales.
--
-- Estrategia RLS:
--   RLS queda activo en tablas publicas. Las politicas consultan el rol
--   del usuario autenticado mediante funciones SECURITY DEFINER simples,
--   evitando politicas recursivas sobre perfiles.
--
-- Funciones/triggers:
--   actualizar_updated_at(), generar_numero_pedido(),
--   validar_pedido(), ocupar_mesa_al_abrir_pedido(),
--   liberar_mesa_al_cerrar_pedido(), validar_detalle_pedido(),
--   confirmar_pedido(), registrar_pago_pedido().

-- ============================================================
-- 00. Seccion opcional de reinicio para desarrollo
-- ============================================================
-- NO ejecutar en produccion. Si se necesita reconstruir la base durante
-- pruebas academicas, ejecutar manualmente estas instrucciones primero.
--
-- drop table if exists public.pagos cascade;
-- drop table if exists public.movimientos_inventario cascade;
-- drop table if exists public.detalle_pedido cascade;
-- drop table if exists public.pedidos cascade;
-- drop table if exists public.productos cascade;
-- drop table if exists public.categorias cascade;
-- drop table if exists public.mesas cascade;
-- drop table if exists public.clientes cascade;
-- drop table if exists public.empleados cascade;
-- drop table if exists public.perfiles cascade;
-- drop sequence if exists public.pedido_numero_seq;
-- drop type if exists public.rol_sistema cascade;
-- drop type if exists public.estado_mesa cascade;
-- drop type if exists public.tipo_movimiento_inventario cascade;
-- drop type if exists public.estado_pedido cascade;
-- drop type if exists public.metodo_pago cascade;

-- ============================================================
-- 01. Extensiones necesarias
-- ============================================================
create extension if not exists pgcrypto;

-- ============================================================
-- 02. Tipos ENUM
-- ============================================================
do $$
begin
    if not exists (select 1 from pg_type where typname = 'rol_sistema') then
        create type public.rol_sistema as enum ('ADMINISTRADOR', 'MESERO', 'CAJERO');
    end if;

    if not exists (select 1 from pg_type where typname = 'estado_mesa') then
        create type public.estado_mesa as enum ('LIBRE', 'OCUPADA');
    end if;

    if not exists (select 1 from pg_type where typname = 'tipo_movimiento_inventario') then
        create type public.tipo_movimiento_inventario as enum ('ENTRADA', 'SALIDA_VENTA', 'AJUSTE');
    end if;

    if not exists (select 1 from pg_type where typname = 'estado_pedido') then
        create type public.estado_pedido as enum ('ABIERTO', 'CONFIRMADO', 'PAGADO', 'CANCELADO');
    end if;

    if not exists (select 1 from pg_type where typname = 'metodo_pago') then
        create type public.metodo_pago as enum ('EFECTIVO', 'TARJETA', 'TRANSFERENCIA');
    end if;
end
$$;

-- ============================================================
-- 03. Tablas
-- ============================================================
create table if not exists public.perfiles (
    id uuid primary key references auth.users(id) on delete cascade,
    nombres text not null,
    apellidos text not null,
    rol public.rol_sistema not null,
    activo boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint perfiles_nombres_no_vacios check (btrim(nombres) <> ''),
    constraint perfiles_apellidos_no_vacios check (btrim(apellidos) <> '')
);

create table if not exists public.empleados (
    id uuid primary key default gen_random_uuid(),
    perfil_id uuid unique references public.perfiles(id) on delete set null,
    cedula text not null unique,
    nombres text not null,
    apellidos text not null,
    telefono text,
    cargo public.rol_sistema not null,
    activo boolean not null default true,
    fecha_contratacion date not null default current_date,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint empleados_cedula_no_vacia check (btrim(cedula) <> ''),
    constraint empleados_nombres_no_vacios check (btrim(nombres) <> ''),
    constraint empleados_apellidos_no_vacios check (btrim(apellidos) <> '')
);

create table if not exists public.clientes (
    id uuid primary key default gen_random_uuid(),
    identificacion text unique,
    nombres text not null,
    apellidos text,
    telefono text,
    correo text,
    activo boolean not null default true,
    es_consumidor_final boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint clientes_nombres_no_vacios check (btrim(nombres) <> ''),
    constraint clientes_identificacion_no_vacia check (
        identificacion is null or btrim(identificacion) <> ''
    ),
    constraint clientes_consumidor_final_sin_identificacion check (
        not es_consumidor_final or identificacion is null
    )
);

create table if not exists public.mesas (
    id uuid primary key default gen_random_uuid(),
    numero integer not null unique,
    capacidad integer not null,
    estado public.estado_mesa not null default 'LIBRE',
    activo boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint mesas_numero_positivo check (numero > 0),
    constraint mesas_capacidad_positiva check (capacidad > 0)
);

create table if not exists public.categorias (
    id uuid primary key default gen_random_uuid(),
    nombre text not null unique,
    descripcion text,
    activo boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint categorias_nombre_no_vacio check (btrim(nombre) <> '')
);

create table if not exists public.productos (
    id uuid primary key default gen_random_uuid(),
    categoria_id uuid not null references public.categorias(id) on delete restrict,
    codigo text not null unique,
    nombre text not null,
    descripcion text,
    precio numeric(10,2) not null,
    stock integer not null default 0,
    stock_minimo integer not null default 0,
    activo boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint productos_codigo_no_vacio check (btrim(codigo) <> ''),
    constraint productos_nombre_no_vacio check (btrim(nombre) <> ''),
    constraint productos_precio_no_negativo check (precio >= 0),
    constraint productos_stock_no_negativo check (stock >= 0),
    constraint productos_stock_minimo_no_negativo check (stock_minimo >= 0)
);

create sequence if not exists public.pedido_numero_seq
    as bigint
    start with 1
    increment by 1
    no minvalue
    no maxvalue
    cache 1;

create table if not exists public.pedidos (
    id uuid primary key default gen_random_uuid(),
    numero_pedido text not null unique,
    cliente_id uuid not null references public.clientes(id) on delete restrict,
    mesa_id uuid not null references public.mesas(id) on delete restrict,
    mesero_id uuid references public.perfiles(id) on delete set null,
    estado public.estado_pedido not null default 'ABIERTO',
    subtotal numeric(10,2) not null default 0,
    impuesto numeric(10,2) not null default 0,
    total numeric(10,2) not null default 0,
    observaciones text,
    fecha_apertura timestamptz not null default now(),
    fecha_cierre timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint pedidos_montos_no_negativos check (subtotal >= 0 and impuesto >= 0 and total >= 0),
    constraint pedidos_cierre_con_estado_final check (
        fecha_cierre is null or estado in ('PAGADO', 'CANCELADO')
    )
);

create table if not exists public.detalle_pedido (
    id uuid primary key default gen_random_uuid(),
    pedido_id uuid not null references public.pedidos(id) on delete cascade,
    producto_id uuid not null references public.productos(id) on delete restrict,
    cantidad integer not null,
    precio_unitario numeric(10,2) not null,
    subtotal numeric(10,2) not null,
    observaciones text,
    created_at timestamptz not null default now(),
    constraint detalle_pedido_cantidad_positiva check (cantidad > 0),
    constraint detalle_pedido_precio_no_negativo check (precio_unitario >= 0),
    constraint detalle_pedido_subtotal_no_negativo check (subtotal >= 0)
);

create table if not exists public.movimientos_inventario (
    id uuid primary key default gen_random_uuid(),
    producto_id uuid not null references public.productos(id) on delete restrict,
    tipo public.tipo_movimiento_inventario not null,
    cantidad integer not null,
    stock_anterior integer not null,
    stock_nuevo integer not null,
    usuario_id uuid references public.perfiles(id) on delete set null,
    pedido_id uuid references public.pedidos(id) on delete set null,
    observacion text,
    created_at timestamptz not null default now(),
    constraint movimientos_cantidad_positiva check (cantidad > 0),
    constraint movimientos_stock_no_negativo check (stock_anterior >= 0 and stock_nuevo >= 0)
);

create table if not exists public.pagos (
    id uuid primary key default gen_random_uuid(),
    pedido_id uuid not null unique references public.pedidos(id) on delete restrict,
    cajero_id uuid references public.perfiles(id) on delete set null,
    metodo_pago public.metodo_pago not null,
    monto numeric(10,2) not null,
    referencia text,
    created_at timestamptz not null default now(),
    constraint pagos_monto_positivo check (monto > 0)
);

-- ============================================================
-- 04. Restricciones adicionales
-- ============================================================
-- Un solo registro puede representar a Consumidor Final.
create unique index if not exists clientes_unico_consumidor_final_idx
    on public.clientes (es_consumidor_final)
    where es_consumidor_final;

-- Una mesa fisica no puede tener dos pedidos activos simultaneos.
create unique index if not exists pedidos_un_pedido_activo_por_mesa_idx
    on public.pedidos (mesa_id)
    where estado in ('ABIERTO', 'CONFIRMADO');

-- ============================================================
-- 05. Indices
-- ============================================================
create index if not exists empleados_perfil_id_idx on public.empleados (perfil_id);
create index if not exists productos_categoria_id_idx on public.productos (categoria_id);
create index if not exists productos_codigo_idx on public.productos (codigo);
create index if not exists mesas_numero_idx on public.mesas (numero);
create index if not exists clientes_identificacion_idx on public.clientes (identificacion);
create index if not exists pedidos_cliente_id_idx on public.pedidos (cliente_id);
create index if not exists pedidos_mesa_id_idx on public.pedidos (mesa_id);
create index if not exists pedidos_mesero_id_idx on public.pedidos (mesero_id);
create index if not exists pedidos_estado_idx on public.pedidos (estado);
create index if not exists pedidos_numero_pedido_idx on public.pedidos (numero_pedido);
create index if not exists pedidos_fecha_apertura_idx on public.pedidos (fecha_apertura);
create index if not exists detalle_pedido_pedido_id_idx on public.detalle_pedido (pedido_id);
create index if not exists detalle_pedido_producto_id_idx on public.detalle_pedido (producto_id);
create index if not exists movimientos_producto_id_idx on public.movimientos_inventario (producto_id);
create index if not exists movimientos_pedido_id_idx on public.movimientos_inventario (pedido_id);
create index if not exists movimientos_created_at_idx on public.movimientos_inventario (created_at);
create index if not exists pagos_pedido_id_idx on public.pagos (pedido_id);

-- ============================================================
-- 06. Funciones
-- ============================================================
create or replace function public.actualizar_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create or replace function public.obtener_rol_actual()
returns public.rol_sistema
language sql
stable
security definer
set search_path = public
as $$
    select p.rol
    from public.perfiles p
    where p.id = auth.uid()
      and p.activo = true
    limit 1;
$$;

create or replace function public.es_administrador()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select public.obtener_rol_actual() = 'ADMINISTRADOR'::public.rol_sistema;
$$;

create or replace function public.generar_numero_pedido()
returns trigger
language plpgsql
as $$
begin
    if new.numero_pedido is null or btrim(new.numero_pedido) = '' then
        new.numero_pedido = 'PED-' || lpad(nextval('public.pedido_numero_seq')::text, 6, '0');
    end if;
    return new;
end;
$$;

create or replace function public.validar_pedido()
returns trigger
language plpgsql
as $$
declare
    v_mesa_estado public.estado_mesa;
    v_mesa_activa boolean;
    v_cliente_activo boolean;
begin
    if tg_op = 'UPDATE' and old.estado in ('PAGADO', 'CANCELADO') and new is distinct from old then
        raise exception 'No se puede modificar un pedido en estado %.', old.estado;
    end if;

    select m.estado, m.activo
      into v_mesa_estado, v_mesa_activa
    from public.mesas m
    where m.id = new.mesa_id;

    if v_mesa_estado is null then
        raise exception 'La mesa indicada no existe.';
    end if;

    if not v_mesa_activa then
        raise exception 'La mesa indicada esta inactiva.';
    end if;

    select c.activo
      into v_cliente_activo
    from public.clientes c
    where c.id = new.cliente_id;

    if v_cliente_activo is null then
        raise exception 'El cliente indicado no existe.';
    end if;

    if not v_cliente_activo then
        raise exception 'El cliente indicado esta inactivo.';
    end if;

    if tg_op = 'INSERT' and new.estado = 'ABIERTO' and v_mesa_estado <> 'LIBRE' then
        raise exception 'La mesa debe estar LIBRE para abrir un pedido.';
    end if;

    if tg_op = 'UPDATE' and old.mesa_id is distinct from new.mesa_id then
        raise exception 'No se permite cambiar la mesa de un pedido existente.';
    end if;

    if tg_op = 'UPDATE' and old.estado = 'CONFIRMADO' and new.estado = 'CANCELADO' then
        raise exception 'No se puede cancelar un pedido confirmado sin una rutina de devolucion de inventario.';
    end if;

    return new;
end;
$$;

create or replace function public.ocupar_mesa_al_abrir_pedido()
returns trigger
language plpgsql
as $$
begin
    if new.estado = 'ABIERTO' then
        update public.mesas
           set estado = 'OCUPADA',
               updated_at = now()
         where id = new.mesa_id;
    end if;

    return new;
end;
$$;

create or replace function public.liberar_mesa_al_cerrar_pedido()
returns trigger
language plpgsql
as $$
begin
    if new.estado in ('PAGADO', 'CANCELADO')
       and old.estado is distinct from new.estado then
        update public.mesas
           set estado = 'LIBRE',
               updated_at = now()
         where id = new.mesa_id;
    end if;

    return new;
end;
$$;

create or replace function public.validar_detalle_pedido()
returns trigger
language plpgsql
as $$
declare
    v_estado_pedido public.estado_pedido;
    v_producto_activo boolean;
    v_precio_actual numeric(10,2);
    v_stock_actual integer;
begin
    select p.estado
      into v_estado_pedido
    from public.pedidos p
    where p.id = new.pedido_id;

    if v_estado_pedido is null then
        raise exception 'El pedido indicado no existe.';
    end if;

    if v_estado_pedido <> 'ABIERTO' then
        raise exception 'Solo se puede modificar el detalle de pedidos ABIERTOS.';
    end if;

    select pr.activo, pr.precio, pr.stock
      into v_producto_activo, v_precio_actual, v_stock_actual
    from public.productos pr
    where pr.id = new.producto_id;

    if v_producto_activo is null then
        raise exception 'El producto indicado no existe.';
    end if;

    if not v_producto_activo then
        raise exception 'Solo pueden agregarse productos activos.';
    end if;

    if new.cantidad > v_stock_actual then
        raise exception 'Stock insuficiente para el producto solicitado.';
    end if;

    if tg_op = 'INSERT' or new.precio_unitario is null then
        new.precio_unitario = v_precio_actual;
    end if;

    new.subtotal = round(new.cantidad * new.precio_unitario, 2);
    return new;
end;
$$;

create or replace function public.actualizar_totales_pedido(p_pedido_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
    v_subtotal numeric(10,2);
    v_impuesto numeric(10,2);
begin
    select coalesce(sum(dp.subtotal), 0)::numeric(10,2)
      into v_subtotal
    from public.detalle_pedido dp
    where dp.pedido_id = p_pedido_id;

    select impuesto
      into v_impuesto
    from public.pedidos
    where id = p_pedido_id;

    update public.pedidos
       set subtotal = v_subtotal,
           total = round(v_subtotal + coalesce(v_impuesto, 0), 2),
           updated_at = now()
     where id = p_pedido_id;
end;
$$;

create or replace function public.recalcular_totales_pedido_desde_detalle()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    if tg_op = 'DELETE' then
        perform public.actualizar_totales_pedido(old.pedido_id);
        return old;
    end if;

    perform public.actualizar_totales_pedido(new.pedido_id);

    if tg_op = 'UPDATE' and old.pedido_id is distinct from new.pedido_id then
        perform public.actualizar_totales_pedido(old.pedido_id);
    end if;

    return new;
end;
$$;

create or replace function public.confirmar_pedido(p_pedido_id uuid)
returns public.pedidos
language plpgsql
security definer
set search_path = public
as $$
declare
    v_pedido public.pedidos%rowtype;
    v_item record;
    v_stock_anterior integer;
    v_stock_nuevo integer;
begin
    if public.obtener_rol_actual() not in ('ADMINISTRADOR', 'MESERO') then
        raise exception 'No tiene permisos para confirmar pedidos.';
    end if;

    select *
      into v_pedido
    from public.pedidos
    where id = p_pedido_id
    for update;

    if not found then
        raise exception 'El pedido indicado no existe.';
    end if;

    if v_pedido.estado <> 'ABIERTO' then
        raise exception 'Solo se pueden confirmar pedidos ABIERTOS.';
    end if;

    if not exists (select 1 from public.detalle_pedido where pedido_id = p_pedido_id) then
        raise exception 'No se puede confirmar un pedido sin detalle.';
    end if;

    perform public.actualizar_totales_pedido(p_pedido_id);

    for v_item in
        select producto_id, sum(cantidad)::integer as cantidad
        from public.detalle_pedido
        where pedido_id = p_pedido_id
        group by producto_id
        order by producto_id
    loop
        select stock
          into v_stock_anterior
        from public.productos
        where id = v_item.producto_id
          and activo = true
        for update;

        if v_stock_anterior is null then
            raise exception 'El producto % no existe o esta inactivo.', v_item.producto_id;
        end if;

        if v_stock_anterior < v_item.cantidad then
            raise exception 'Stock insuficiente para confirmar el pedido.';
        end if;

        v_stock_nuevo := v_stock_anterior - v_item.cantidad;

        update public.productos
           set stock = v_stock_nuevo,
               updated_at = now()
         where id = v_item.producto_id;

        insert into public.movimientos_inventario (
            producto_id,
            tipo,
            cantidad,
            stock_anterior,
            stock_nuevo,
            usuario_id,
            pedido_id,
            observacion
        )
        values (
            v_item.producto_id,
            'SALIDA_VENTA',
            v_item.cantidad,
            v_stock_anterior,
            v_stock_nuevo,
            auth.uid(),
            p_pedido_id,
            'Salida generada al confirmar pedido'
        );
    end loop;

    update public.pedidos
       set estado = 'CONFIRMADO',
           updated_at = now()
     where id = p_pedido_id
     returning * into v_pedido;

    return v_pedido;
end;
$$;

create or replace function public.registrar_pago_pedido(
    p_pedido_id uuid,
    p_metodo_pago public.metodo_pago,
    p_monto numeric,
    p_referencia text default null
)
returns public.pagos
language plpgsql
security definer
set search_path = public
as $$
declare
    v_pedido public.pedidos%rowtype;
    v_pago public.pagos%rowtype;
begin
    if public.obtener_rol_actual() not in ('ADMINISTRADOR', 'CAJERO') then
        raise exception 'No tiene permisos para registrar pagos.';
    end if;

    select *
      into v_pedido
    from public.pedidos
    where id = p_pedido_id
    for update;

    if not found then
        raise exception 'El pedido indicado no existe.';
    end if;

    if v_pedido.estado <> 'CONFIRMADO' then
        raise exception 'Solo se pueden pagar pedidos CONFIRMADOS.';
    end if;

    if p_monto <= 0 then
        raise exception 'El monto del pago debe ser mayor que cero.';
    end if;

    if round(p_monto, 2) <> v_pedido.total then
        raise exception 'El pago principal debe coincidir con el total del pedido.';
    end if;

    insert into public.pagos (
        pedido_id,
        cajero_id,
        metodo_pago,
        monto,
        referencia
    )
    values (
        p_pedido_id,
        auth.uid(),
        p_metodo_pago,
        round(p_monto, 2),
        p_referencia
    )
    returning * into v_pago;

    update public.pedidos
       set estado = 'PAGADO',
           fecha_cierre = now(),
           updated_at = now()
     where id = p_pedido_id;

    return v_pago;
end;
$$;

-- ============================================================
-- 07. Triggers
-- ============================================================
drop trigger if exists trg_perfiles_updated_at on public.perfiles;
create trigger trg_perfiles_updated_at
before update on public.perfiles
for each row execute function public.actualizar_updated_at();

drop trigger if exists trg_empleados_updated_at on public.empleados;
create trigger trg_empleados_updated_at
before update on public.empleados
for each row execute function public.actualizar_updated_at();

drop trigger if exists trg_clientes_updated_at on public.clientes;
create trigger trg_clientes_updated_at
before update on public.clientes
for each row execute function public.actualizar_updated_at();

drop trigger if exists trg_mesas_updated_at on public.mesas;
create trigger trg_mesas_updated_at
before update on public.mesas
for each row execute function public.actualizar_updated_at();

drop trigger if exists trg_categorias_updated_at on public.categorias;
create trigger trg_categorias_updated_at
before update on public.categorias
for each row execute function public.actualizar_updated_at();

drop trigger if exists trg_productos_updated_at on public.productos;
create trigger trg_productos_updated_at
before update on public.productos
for each row execute function public.actualizar_updated_at();

drop trigger if exists trg_pedidos_generar_numero on public.pedidos;
create trigger trg_pedidos_generar_numero
before insert on public.pedidos
for each row execute function public.generar_numero_pedido();

drop trigger if exists trg_pedidos_validar on public.pedidos;
create trigger trg_pedidos_validar
before insert or update on public.pedidos
for each row execute function public.validar_pedido();

drop trigger if exists trg_pedidos_ocupar_mesa on public.pedidos;
create trigger trg_pedidos_ocupar_mesa
after insert on public.pedidos
for each row execute function public.ocupar_mesa_al_abrir_pedido();

drop trigger if exists trg_pedidos_liberar_mesa on public.pedidos;
create trigger trg_pedidos_liberar_mesa
after update of estado on public.pedidos
for each row execute function public.liberar_mesa_al_cerrar_pedido();

drop trigger if exists trg_pedidos_updated_at on public.pedidos;
create trigger trg_pedidos_updated_at
before update on public.pedidos
for each row execute function public.actualizar_updated_at();

drop trigger if exists trg_detalle_pedido_validar on public.detalle_pedido;
create trigger trg_detalle_pedido_validar
before insert or update on public.detalle_pedido
for each row execute function public.validar_detalle_pedido();

drop trigger if exists trg_detalle_pedido_recalcular_totales on public.detalle_pedido;
create trigger trg_detalle_pedido_recalcular_totales
after insert or update or delete on public.detalle_pedido
for each row execute function public.recalcular_totales_pedido_desde_detalle();

-- ============================================================
-- 08. Row Level Security
-- ============================================================
alter table public.perfiles enable row level security;
alter table public.empleados enable row level security;
alter table public.clientes enable row level security;
alter table public.mesas enable row level security;
alter table public.categorias enable row level security;
alter table public.productos enable row level security;
alter table public.pedidos enable row level security;
alter table public.detalle_pedido enable row level security;
alter table public.movimientos_inventario enable row level security;
alter table public.pagos enable row level security;

-- ============================================================
-- 09. Politicas RLS
-- ============================================================
do $$
begin
    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'perfiles' and policyname = 'perfiles_select_propios_o_admin') then
        create policy perfiles_select_propios_o_admin
        on public.perfiles for select
        to authenticated
        using (id = auth.uid() or public.es_administrador());
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'perfiles' and policyname = 'perfiles_admin_todo') then
        create policy perfiles_admin_todo
        on public.perfiles for all
        to authenticated
        using (public.es_administrador())
        with check (public.es_administrador());
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'empleados' and policyname = 'empleados_admin_todo') then
        create policy empleados_admin_todo
        on public.empleados for all
        to authenticated
        using (public.es_administrador())
        with check (public.es_administrador());
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'empleados' and policyname = 'empleados_select_cuenta_propia') then
        create policy empleados_select_cuenta_propia
        on public.empleados for select
        to authenticated
        using (perfil_id = auth.uid());
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'clientes' and policyname = 'clientes_roles_operativos_select') then
        create policy clientes_roles_operativos_select
        on public.clientes for select
        to authenticated
        using (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO', 'CAJERO'));
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'clientes' and policyname = 'clientes_admin_mesero_insert_update') then
        create policy clientes_admin_mesero_insert_update
        on public.clientes for insert
        to authenticated
        with check (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO'));
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'clientes' and policyname = 'clientes_admin_mesero_update') then
        create policy clientes_admin_mesero_update
        on public.clientes for update
        to authenticated
        using (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO'))
        with check (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO'));
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'clientes' and policyname = 'clientes_admin_delete') then
        create policy clientes_admin_delete
        on public.clientes for delete
        to authenticated
        using (public.es_administrador());
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'mesas' and policyname = 'mesas_roles_operativos_select') then
        create policy mesas_roles_operativos_select
        on public.mesas for select
        to authenticated
        using (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO', 'CAJERO'));
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'mesas' and policyname = 'mesas_admin_insert_delete') then
        create policy mesas_admin_insert_delete
        on public.mesas for all
        to authenticated
        using (public.es_administrador())
        with check (public.es_administrador());
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'mesas' and policyname = 'mesas_admin_mesero_update') then
        create policy mesas_admin_mesero_update
        on public.mesas for update
        to authenticated
        using (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO'))
        with check (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO'));
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'categorias' and policyname = 'categorias_roles_operativos_select') then
        create policy categorias_roles_operativos_select
        on public.categorias for select
        to authenticated
        using (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO', 'CAJERO'));
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'categorias' and policyname = 'categorias_admin_todo') then
        create policy categorias_admin_todo
        on public.categorias for all
        to authenticated
        using (public.es_administrador())
        with check (public.es_administrador());
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'productos' and policyname = 'productos_roles_operativos_select') then
        create policy productos_roles_operativos_select
        on public.productos for select
        to authenticated
        using (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO', 'CAJERO'));
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'productos' and policyname = 'productos_admin_todo') then
        create policy productos_admin_todo
        on public.productos for all
        to authenticated
        using (public.es_administrador())
        with check (public.es_administrador());
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'pedidos' and policyname = 'pedidos_roles_operativos_select') then
        create policy pedidos_roles_operativos_select
        on public.pedidos for select
        to authenticated
        using (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO', 'CAJERO'));
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'pedidos' and policyname = 'pedidos_admin_mesero_insert') then
        create policy pedidos_admin_mesero_insert
        on public.pedidos for insert
        to authenticated
        with check (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO'));
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'pedidos' and policyname = 'pedidos_roles_operativos_update') then
        create policy pedidos_roles_operativos_update
        on public.pedidos for update
        to authenticated
        using (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO', 'CAJERO'))
        with check (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO', 'CAJERO'));
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'pedidos' and policyname = 'pedidos_admin_delete') then
        create policy pedidos_admin_delete
        on public.pedidos for delete
        to authenticated
        using (public.es_administrador());
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'detalle_pedido' and policyname = 'detalle_roles_operativos_select') then
        create policy detalle_roles_operativos_select
        on public.detalle_pedido for select
        to authenticated
        using (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO', 'CAJERO'));
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'detalle_pedido' and policyname = 'detalle_admin_mesero_insert_update_delete') then
        create policy detalle_admin_mesero_insert_update_delete
        on public.detalle_pedido for all
        to authenticated
        using (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO'))
        with check (public.obtener_rol_actual() in ('ADMINISTRADOR', 'MESERO'));
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'pagos' and policyname = 'pagos_admin_cajero_select') then
        create policy pagos_admin_cajero_select
        on public.pagos for select
        to authenticated
        using (public.obtener_rol_actual() in ('ADMINISTRADOR', 'CAJERO'));
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'pagos' and policyname = 'pagos_admin_cajero_insert') then
        create policy pagos_admin_cajero_insert
        on public.pagos for insert
        to authenticated
        with check (public.obtener_rol_actual() in ('ADMINISTRADOR', 'CAJERO'));
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'pagos' and policyname = 'pagos_admin_update_delete') then
        create policy pagos_admin_update_delete
        on public.pagos for all
        to authenticated
        using (public.es_administrador())
        with check (public.es_administrador());
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'movimientos_inventario' and policyname = 'movimientos_admin_select') then
        create policy movimientos_admin_select
        on public.movimientos_inventario for select
        to authenticated
        using (public.es_administrador());
    end if;

    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = 'movimientos_inventario' and policyname = 'movimientos_admin_insert') then
        create policy movimientos_admin_insert
        on public.movimientos_inventario for insert
        to authenticated
        with check (public.es_administrador());
    end if;
end
$$;

revoke execute on function public.actualizar_totales_pedido(uuid) from public;
revoke execute on function public.actualizar_totales_pedido(uuid) from authenticated;
grant execute on function public.confirmar_pedido(uuid) to authenticated;
grant execute on function public.registrar_pago_pedido(uuid, public.metodo_pago, numeric, text) to authenticated;

-- ============================================================
-- 10. Datos semilla
-- ============================================================
insert into public.categorias (nombre, descripcion)
values
    ('Platos', 'Platos principales del restaurante'),
    ('Bebidas', 'Bebidas frias y calientes'),
    ('Postres', 'Postres disponibles'),
    ('Otros', 'Otros productos vendibles')
on conflict (nombre) do nothing;

insert into public.mesas (numero, capacidad)
values
    (1, 4),
    (2, 4),
    (3, 2),
    (4, 6),
    (5, 4)
on conflict (numero) do nothing;

insert into public.clientes (identificacion, nombres, apellidos, activo, es_consumidor_final)
select null, 'Consumidor Final', null, true, true
where not exists (
    select 1 from public.clientes where es_consumidor_final = true
);

insert into public.productos (categoria_id, codigo, nombre, descripcion, precio, stock, stock_minimo)
select c.id, 'PLA-001', 'Almuerzo ejecutivo', 'Plato principal de prueba', 4.50, 30, 5
from public.categorias c
where c.nombre = 'Platos'
on conflict (codigo) do update
set categoria_id = excluded.categoria_id,
    nombre = excluded.nombre,
    descripcion = excluded.descripcion,
    precio = excluded.precio,
    stock_minimo = excluded.stock_minimo;

insert into public.productos (categoria_id, codigo, nombre, descripcion, precio, stock, stock_minimo)
select c.id, 'PLA-002', 'Hamburguesa clasica', 'Hamburguesa ficticia para pruebas', 5.00, 25, 5
from public.categorias c
where c.nombre = 'Platos'
on conflict (codigo) do update
set categoria_id = excluded.categoria_id,
    nombre = excluded.nombre,
    descripcion = excluded.descripcion,
    precio = excluded.precio,
    stock_minimo = excluded.stock_minimo;

insert into public.productos (categoria_id, codigo, nombre, descripcion, precio, stock, stock_minimo)
select c.id, 'BEB-001', 'Jugo natural', 'Bebida ficticia para pruebas', 1.50, 40, 8
from public.categorias c
where c.nombre = 'Bebidas'
on conflict (codigo) do update
set categoria_id = excluded.categoria_id,
    nombre = excluded.nombre,
    descripcion = excluded.descripcion,
    precio = excluded.precio,
    stock_minimo = excluded.stock_minimo;

insert into public.productos (categoria_id, codigo, nombre, descripcion, precio, stock, stock_minimo)
select c.id, 'BEB-002', 'Agua embotellada', 'Agua sin gas', 1.00, 50, 10
from public.categorias c
where c.nombre = 'Bebidas'
on conflict (codigo) do update
set categoria_id = excluded.categoria_id,
    nombre = excluded.nombre,
    descripcion = excluded.descripcion,
    precio = excluded.precio,
    stock_minimo = excluded.stock_minimo;

insert into public.productos (categoria_id, codigo, nombre, descripcion, precio, stock, stock_minimo)
select c.id, 'POS-001', 'Flan casero', 'Postre ficticio para pruebas', 2.00, 15, 3
from public.categorias c
where c.nombre = 'Postres'
on conflict (codigo) do update
set categoria_id = excluded.categoria_id,
    nombre = excluded.nombre,
    descripcion = excluded.descripcion,
    precio = excluded.precio,
    stock_minimo = excluded.stock_minimo;

-- ============================================================
-- 11. Consultas de verificacion
-- ============================================================
-- Tablas publicas creadas para el proyecto
select table_name
from information_schema.tables
where table_schema = 'public'
  and table_name in (
      'perfiles',
      'empleados',
      'clientes',
      'mesas',
      'categorias',
      'productos',
      'movimientos_inventario',
      'pedidos',
      'detalle_pedido',
      'pagos'
  )
order by table_name;

-- Conteos basicos de datos semilla
select 'categorias' as tabla, count(*) as total from public.categorias
union all
select 'productos', count(*) from public.productos
union all
select 'mesas', count(*) from public.mesas
union all
select 'clientes', count(*) from public.clientes;

-- Categorias, productos, mesas y Consumidor Final
select * from public.categorias order by nombre;
select codigo, nombre, precio, stock, stock_minimo, activo from public.productos order by codigo;
select numero, capacidad, estado, activo from public.mesas order by numero;
select id, nombres, apellidos, es_consumidor_final from public.clientes where es_consumidor_final = true;

-- Relaciones principales
select
    tc.table_name,
    kcu.column_name,
    ccu.table_name as tabla_referenciada,
    ccu.column_name as columna_referenciada
from information_schema.table_constraints tc
join information_schema.key_column_usage kcu
  on tc.constraint_name = kcu.constraint_name
 and tc.table_schema = kcu.table_schema
join information_schema.constraint_column_usage ccu
  on ccu.constraint_name = tc.constraint_name
 and ccu.table_schema = tc.table_schema
where tc.constraint_type = 'FOREIGN KEY'
  and tc.table_schema = 'public'
order by tc.table_name, kcu.column_name;

-- Politicas RLS
select schemaname, tablename, policyname, cmd
from pg_policies
where schemaname = 'public'
order by tablename, policyname;

-- Triggers del proyecto
select event_object_table as tabla, trigger_name
from information_schema.triggers
where trigger_schema = 'public'
order by event_object_table, trigger_name;

-- Consultas operativas utiles para la futura aplicacion
select id, codigo, nombre, precio, stock
from public.productos
where activo = true and stock > 0
order by nombre;

select id, numero, capacidad
from public.mesas
where activo = true and estado = 'LIBRE'
order by numero;

select id, numero_pedido, estado, subtotal, impuesto, total, fecha_apertura
from public.pedidos
where estado in ('ABIERTO', 'CONFIRMADO')
order by fecha_apertura desc;

select
    p.numero_pedido,
    pr.nombre as producto,
    dp.cantidad,
    dp.precio_unitario,
    dp.subtotal
from public.detalle_pedido dp
join public.pedidos p on p.id = dp.pedido_id
join public.productos pr on pr.id = dp.producto_id
order by p.fecha_apertura desc, pr.nombre;

select
    mi.created_at,
    pr.codigo,
    pr.nombre,
    mi.tipo,
    mi.cantidad,
    mi.stock_anterior,
    mi.stock_nuevo,
    mi.observacion
from public.movimientos_inventario mi
join public.productos pr on pr.id = mi.producto_id
order by mi.created_at desc;

select
    p.numero_pedido,
    p.estado,
    p.total,
    pa.metodo_pago,
    pa.monto,
    pa.created_at as fecha_pago
from public.pagos pa
join public.pedidos p on p.id = pa.pedido_id
order by pa.created_at desc;
