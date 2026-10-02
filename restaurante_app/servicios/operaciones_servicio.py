from datetime import datetime, timezone
from decimal import Decimal

from supabase import create_client

from config.settings import SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL
from servicios.base import SupabaseServicio
from utils.errores import AppError, mensaje_amigable


class EmpleadoServicio(SupabaseServicio):
    def listar(self):
        return self.ejecutar(lambda: self.cliente.table("empleados").select("*").order("apellidos"), "empleados")

    def listar_perfiles(self):
        return self.ejecutar(lambda: self.cliente.table("perfiles").select("*").order("apellidos"), "perfiles")

    def crear_cuenta_acceso(self, correo: str, contrasena: str) -> str:
        correo = correo.strip().lower()
        if not correo:
            raise AppError("Ingrese el correo de acceso del empleado.")
        if not contrasena:
            raise AppError("Ingrese la contrasena temporal del empleado.")
        if len(contrasena) < 6:
            raise AppError("La contrasena debe tener al menos 6 caracteres.")
        try:
            cliente_auth = create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)
            respuesta = cliente_auth.auth.sign_up({"email": correo, "password": contrasena})
            if not respuesta.user:
                raise AppError("No se pudo crear la cuenta de acceso.")
            return respuesta.user.id
        except AppError:
            raise
        except Exception as error:
            raise AppError(f"crear cuenta de acceso: {mensaje_amigable(error)}") from error

    def guardar_perfil_empleado(self, perfil_id: str, nombres: str, apellidos: str, rol: str, activo: bool):
        perfil_id = perfil_id.strip()
        if not perfil_id:
            raise AppError("No se pudo vincular la cuenta de acceso del empleado.")
        if rol not in ("ADMINISTRADOR", "MESERO", "CAJERO"):
            raise AppError("Seleccione un rol valido para el perfil.")
        payload = {
            "id": perfil_id,
            "nombres": nombres.strip(),
            "apellidos": apellidos.strip(),
            "rol": rol,
            "activo": activo,
        }
        existentes = self.ejecutar(
            lambda: self.cliente.table("perfiles").select("id").eq("id", perfil_id).limit(1),
            "buscar perfil",
        )
        if existentes:
            return self.ejecutar(
                lambda: self.cliente.table("perfiles").update(payload).eq("id", perfil_id),
                "actualizar perfil",
            )
        return self.ejecutar(lambda: self.cliente.table("perfiles").insert(payload), "crear perfil")

    def guardar(self, datos: dict, empleado_id: str | None = None):
        if not datos.get("cedula", "").strip() or not datos.get("nombres", "").strip() or not datos.get("apellidos", "").strip():
            raise AppError("Cedula, nombres y apellidos son obligatorios.")
        payload = {
            "perfil_id": datos.get("perfil_id") or None,
            "cedula": datos["cedula"].strip(),
            "nombres": datos["nombres"].strip(),
            "apellidos": datos["apellidos"].strip(),
            "telefono": datos.get("telefono") or None,
            "cargo": datos.get("cargo") or "MESERO",
            "activo": bool(datos.get("activo", True)),
        }
        if datos.get("fecha_contratacion"):
            payload["fecha_contratacion"] = datos["fecha_contratacion"]
        if empleado_id:
            return self.ejecutar(lambda: self.cliente.table("empleados").update(payload).eq("id", empleado_id), "actualizar empleado")
        return self.ejecutar(lambda: self.cliente.table("empleados").insert(payload), "registrar empleado")


class InventarioServicio(SupabaseServicio):
    def movimientos(self):
        return self.ejecutar(
            lambda: self.cliente.table("movimientos_inventario").select("*").order("created_at", desc=True).limit(100),
            "movimientos de inventario",
        )

    def registrar_movimiento(self, producto: dict, tipo: str, cantidad: int, observacion: str, usuario_id: str):
        if cantidad <= 0:
            raise AppError("La cantidad debe ser mayor que cero.")
        stock_anterior = int(producto.get("stock", 0))
        stock_nuevo = stock_anterior + cantidad if tipo == "ENTRADA" else cantidad
        if stock_nuevo < 0:
            raise AppError("El stock resultante no puede ser negativo.")
        self.ejecutar(
            lambda: self.cliente.table("productos").update({"stock": stock_nuevo}).eq("id", producto["id"]),
            "actualizar stock",
        )
        payload = {
            "producto_id": producto["id"],
            "tipo": tipo,
            "cantidad": cantidad,
            "stock_anterior": stock_anterior,
            "stock_nuevo": stock_nuevo,
            "usuario_id": usuario_id,
            "observacion": observacion or ("Entrada de inventario" if tipo == "ENTRADA" else "Ajuste de inventario"),
        }
        return self.ejecutar(lambda: self.cliente.table("movimientos_inventario").insert(payload), "registrar movimiento")


class PedidoServicio(SupabaseServicio):
    def listar(self, estado: str = ""):
        consulta = self.cliente.table("pedidos").select("*").order("fecha_apertura", desc=True)
        if estado:
            consulta = consulta.eq("estado", estado)
        return self.ejecutar(lambda: consulta, "pedidos")

    def obtener(self, pedido_id: str):
        datos = self.ejecutar(lambda: self.cliente.table("pedidos").select("*").eq("id", pedido_id).limit(1), "pedido")
        return datos[0] if datos else None

    def detalle(self, pedido_id: str):
        return self.ejecutar(lambda: self.cliente.table("detalle_pedido").select("*").eq("pedido_id", pedido_id), "detalle del pedido")

    def crear(self, cliente_id: str, mesa_id: str, mesero_id: str, observaciones: str = ""):
        if not cliente_id or not mesa_id:
            raise AppError("Seleccione cliente y mesa.")
        payload = {
            "cliente_id": cliente_id,
            "mesa_id": mesa_id,
            "mesero_id": mesero_id or None,
            "observaciones": observaciones or None,
        }
        return self.ejecutar(lambda: self.cliente.table("pedidos").insert(payload), "abrir pedido")[0]

    def agregar_detalle(self, pedido_id: str, producto_id: str, cantidad: int, observaciones: str = ""):
        if cantidad <= 0:
            raise AppError("La cantidad debe ser mayor que cero.")
        payload = {
            "pedido_id": pedido_id,
            "producto_id": producto_id,
            "cantidad": cantidad,
            "precio_unitario": 0,
            "subtotal": 0,
            "observaciones": observaciones or None,
        }
        return self.ejecutar(lambda: self.cliente.table("detalle_pedido").insert(payload), "agregar producto")

    def eliminar_detalle(self, detalle_id: str):
        return self.ejecutar(lambda: self.cliente.table("detalle_pedido").delete().eq("id", detalle_id), "eliminar detalle")

    def confirmar(self, pedido_id: str):
        return self.rpc("confirmar_pedido", {"p_pedido_id": pedido_id})

    def cancelar(self, pedido_id: str):
        pedido = self.obtener(pedido_id)
        if not pedido:
            raise AppError("Seleccione un pedido valido.")
        if pedido.get("estado") != "ABIERTO":
            raise AppError("Solo se pueden cancelar pedidos ABIERTOS.")
        return self.ejecutar(
            lambda: self.cliente.table("pedidos").update({
                "estado": "CANCELADO",
                "fecha_cierre": datetime.now(timezone.utc).isoformat(),
            }).eq("id", pedido_id),
            "cancelar pedido",
        )


class PagoServicio(SupabaseServicio):
    def registrar_pago(self, pedido_id: str, metodo_pago: str, monto: Decimal, referencia: str = ""):
        if not metodo_pago:
            raise AppError("Seleccione metodo de pago.")
        return self.rpc(
            "registrar_pago_pedido",
            {
                "p_pedido_id": pedido_id,
                "p_metodo_pago": metodo_pago,
                "p_monto": float(monto),
                "p_referencia": referencia or None,
            },
        )

    def listar(self):
        return self.ejecutar(lambda: self.cliente.table("pagos").select("*").order("created_at", desc=True), "pagos")
