# RestauranteApp

Sistema administrativo academico para restaurante, desarrollado con Python, Tkinter y Supabase.

## Objetivo

Transformar la aplicacion base de biblioteca en una aplicacion de restaurante conectada a una base PostgreSQL/Supabase. La app permite iniciar sesion con Supabase Auth, operar segun rol, gestionar catalogos, abrir pedidos, confirmar ventas, registrar pagos y generar PDFs internos.

## Tecnologias

- Python 3
- Tkinter y ttk
- Supabase Python Client
- python-dotenv
- ReportLab
- pathlib, dataclasses y type hints

Tkinter forma parte de la instalacion normal de Python y no se instala con pip.

## Estructura

```text
restaurante_app/
├── assets/
│   ├── icons/
│   ├── images/
│   ├── logo/
│   └── ICONOS_REQUERIDOS.md
├── config/
├── database/
├── modelos/
├── reportes/
├── servicios/
├── ui/
├── utils/
└── main.py

reportes_generados/
01_restaurante_supabase.sql
02_restaurante_useradmin.sql
.env.example
requirements.txt
```

## Arquitectura del proyecto

El proyecto evoluciono desde una aplicacion de biblioteca con datos JSON locales hacia una aplicacion administrativa conectada a Supabase. Se conservaron ideas utiles del proyecto inicial, como separacion por carpetas, vistas Tkinter, servicios y assets, pero el dominio cambio completamente a restaurante.

La arquitectura busca que el estudiante identifique responsabilidades:

- `main.py`: punto de entrada. Crea la ventana principal, inicializa servicios y decide si se muestra login o la interfaz principal.
- `config/`: configuracion general de la app, colores, rutas y variables de entorno.
- `database/`: crea el cliente Supabase. Ninguna vista deberia crear conexiones por su cuenta.
- `modelos/`: clases `dataclass` que representan entidades del dominio, como cliente, mesa, producto, pedido o pago.
- `servicios/`: capa intermedia entre la interfaz y Supabase. Aqui viven las consultas, validaciones de aplicacion y llamadas RPC.
- `ui/`: pantallas Tkinter. Deben encargarse de mostrar datos, capturar eventos y llamar servicios.
- `reportes/`: generacion de documentos PDF con ReportLab.
- `utils/`: utilidades reutilizables, como manejo de assets, errores y ventanas.
- `assets/`: recursos visuales, logo e iconos.

La idea principal es:

```text
Usuario -> Tkinter UI -> Servicios -> Supabase -> Servicios -> Tkinter UI
```

Esto permite estudiar POO, eventos, callbacks, separacion por capas, autenticacion, persistencia en la nube y manejo de errores sin convertir el proyecto en una arquitectura empresarial compleja.

## Diferencia con la version anterior

Antes la aplicacion trabajaba con:

- dominio de biblioteca;
- libros, usuarios y ventas simples;
- archivos JSON locales;
- usuarios y contrasenas guardados en datos locales;
- una logica de servicio concentrada en la biblioteca.

Ahora trabaja con:

- dominio de restaurante;
- Supabase Auth para inicio de sesion;
- PostgreSQL/Supabase como base de datos;
- roles reales de operacion;
- pedidos, detalle, inventario, pagos y reportes;
- servicios separados por area del sistema;
- funciones RPC de base de datos para operaciones criticas.

Esta transformacion es importante porque muestra como una aplicacion local puede evolucionar hacia un sistema conectado a una base de datos en la nube.

## Requisitos

1. Python 3 instalado.
2. Proyecto Supabase creado.
3. Script `01_restaurante_supabase.sql` ejecutado en el SQL Editor de Supabase.
4. Usuario Auth creado desde Supabase Dashboard.
5. Perfil asociado en la tabla `perfiles`.

## Archivos del repositorio

Este repositorio debe contener solo el proyecto principal:

- `restaurante_app/`
- `README.md`
- `requirements.txt`
- `.env.example`
- `01_restaurante_supabase.sql`
- `02_restaurante_useradmin.sql`

No se deben subir `.env`, `reportes_generados/`, entornos virtuales, caches, builds ni la carpeta del laboratorio web.

## Instalacion

Desde la raiz del repositorio:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuracion Supabase

Copia `.env.example` como `.env` y completa:

```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_PUBLISHABLE_KEY=tu_publishable_key
```

No uses `service_role`, secret keys ni contrasenas dentro del codigo fuente.

## Como se conecta con Supabase

El flujo de conexion es:

1. `.env` guarda `SUPABASE_URL` y `SUPABASE_PUBLISHABLE_KEY`.
2. `config/settings.py` lee esas variables con `python-dotenv`.
3. `database/supabase_cliente.py` crea un unico cliente Supabase.
4. `main.py` entrega ese cliente a los servicios.
5. Los servicios consultan tablas o ejecutan RPC.
6. Las vistas Tkinter muestran los resultados y capturan acciones del usuario.

Ejemplo conceptual:

```text
LoginView
  -> AuthServicio
    -> Supabase Auth
      -> tabla perfiles
        -> MainView segun rol
```

Para pedidos y pagos se respeta la logica critica de la base:

- Confirmar pedido usa `confirmar_pedido`.
- Registrar pago usa `registrar_pago_pedido`.

La aplicacion no debe cambiar manualmente un pedido a `CONFIRMADO` o `PAGADO` si existe una RPC encargada de hacerlo.

## Crear administrador inicial

1. Crea el usuario desde Supabase Dashboard > Authentication.
2. Copia el UUID del usuario.
3. Inserta su perfil en `perfiles`, por ejemplo:

```sql
insert into public.perfiles (id, nombres, apellidos, rol, activo)
values ('UUID_DEL_USUARIO', 'Admin', 'Principal', 'ADMINISTRADOR', true);
```

El archivo `02_restaurante_useradmin.sql` puede servir como ayuda si lo adaptas al UUID real.

## Ejecucion

```powershell
py restaurante_app/main.py
```

Tambien puedes ejecutar desde la carpeta de la aplicacion:

```powershell
cd restaurante_app
py main.py
```

## Roles

- `ADMINISTRADOR`: dashboard, empleados, clientes, mesas, categorias, productos, inventario, pedidos, caja y reportes.
- `MESERO`: dashboard operativo, mesas, clientes, productos y pedidos.
- `CAJERO`: dashboard de caja, clientes, caja y pagos.

Las restricciones visuales no reemplazan RLS. La seguridad real sigue en Supabase.

## Modulos

- Login con Supabase Auth.
- Dashboard por rol.
- Mesas con estado `LIBRE` u `OCUPADA`.
- Clientes, incluyendo el registro unico de Consumidor Final.
- Categorias y productos.
- Inventario con entradas y ajustes auditados.
- Pedidos con detalle y confirmacion por RPC `confirmar_pedido`.
- Caja con pago por RPC `registrar_pago_pedido`.
- Empleados sin creacion de cuentas Auth desde la app.
- Reportes PDF con ReportLab.

## Flujo operativo

1. Iniciar sesion.
2. Seleccionar cliente.
3. Seleccionar mesa libre.
4. Abrir pedido.
5. Agregar productos.
6. Confirmar pedido.
7. La base descuenta stock y genera movimiento.
8. Caja registra pago.
9. La base marca el pedido como pagado y libera la mesa.
10. Generar comprobante PDF.

## Atajos

- `Enter`: accion principal en login.
- `Escape`: limpiar/cancelar formulario o salir del login.
- `Ctrl+F`: enfocar busqueda cuando existe.
- `Ctrl+N`: limpiar formulario.
- `F5`: actualizar la vista actual.
- `Delete`: eliminar item seleccionado del detalle de pedido.

## Reportes

Los PDFs se guardan en:

```text
reportes_generados/
```

Nombres esperados:

- `pedido_PED-000001.pdf`
- `comprobante_PED-000001.pdf`
- `ventas_2026-09-30.pdf`

Si el archivo ya existe, la app agrega un sufijo para no sobrescribirlo.

## Assets

El logo heredado se conserva en `restaurante_app/assets/logo/`. Si no armoniza completamente con la paleta restaurante, se recomienda redisenarlo manualmente en una fase posterior. La lista de iconos sugeridos esta en `restaurante_app/assets/ICONOS_REQUERIDOS.md`.

## Limitaciones academicas

No incluye facturacion electronica SRI, delivery, reservas online, proveedores, compras, ingredientes, recetas, pasarelas de pago, contabilidad, nomina, sucursales ni app movil.

## Pruebas recomendadas

- Login incorrecto.
- Usuario sin perfil.
- Usuario inactivo.
- Mesa ocupada.
- Pedido sin detalle.
- Stock insuficiente.
- Confirmar dos veces.
- Pagar dos veces.
- Producto inactivo.
- PDF sin carpeta previa.
- Icono inexistente.

El flujo integral esperado es: abrir aplicacion, iniciar sesion, consultar dashboard, crear pedido, agregar productos, confirmar, verificar inventario/movimientos, registrar pago, generar comprobante, consultar ventas y cerrar sesion.
