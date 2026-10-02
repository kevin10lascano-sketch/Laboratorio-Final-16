from decimal import Decimal

from servicios.base import SupabaseServicio
from utils.errores import AppError


class ClienteServicio(SupabaseServicio):
    def listar(self, busqueda: str = "", solo_activos: bool = False):
        consulta = self.cliente.table("clientes").select("*").order("nombres")
        if solo_activos:
            consulta = consulta.eq("activo", True)
        datos = self.ejecutar(lambda: consulta, "clientes")
        if busqueda.strip():
            b = busqueda.strip().lower()
            datos = [
                c for c in datos
                if b in (c.get("identificacion") or "").lower()
                or b in (c.get("nombres") or "").lower()
                or b in (c.get("apellidos") or "").lower()
            ]
        return datos

    def consumidor_final(self):
        datos = self.ejecutar(
            lambda: self.cliente.table("clientes").select("*").eq("es_consumidor_final", True).limit(1),
            "consumidor final",
        )
        return datos[0] if datos else None

    def guardar(self, datos: dict, cliente_id: str | None = None):
        payload = {
            "identificacion": datos.get("identificacion") or None,
            "nombres": datos["nombres"].strip(),
            "apellidos": datos.get("apellidos") or None,
            "telefono": datos.get("telefono") or None,
            "correo": datos.get("correo") or None,
            "activo": bool(datos.get("activo", True)),
        }
        if not payload["nombres"]:
            raise AppError("El nombre del cliente es obligatorio.")
        if cliente_id:
            return self.ejecutar(lambda: self.cliente.table("clientes").update(payload).eq("id", cliente_id), "actualizar cliente")
        return self.ejecutar(lambda: self.cliente.table("clientes").insert(payload), "registrar cliente")


class MesaServicio(SupabaseServicio):
    def listar(self, solo_activas: bool = True):
        consulta = self.cliente.table("mesas").select("*").order("numero")
        if solo_activas:
            consulta = consulta.eq("activo", True)
        return self.ejecutar(lambda: consulta, "mesas")

    def guardar(self, numero: int, capacidad: int, activo: bool, mesa_id: str | None = None):
        if numero <= 0 or capacidad <= 0:
            raise AppError("Numero y capacidad deben ser mayores que cero.")
        payload = {"numero": numero, "capacidad": capacidad, "activo": activo}
        if mesa_id:
            return self.ejecutar(lambda: self.cliente.table("mesas").update(payload).eq("id", mesa_id), "actualizar mesa")
        return self.ejecutar(lambda: self.cliente.table("mesas").insert(payload), "registrar mesa")


class CategoriaServicio(SupabaseServicio):
    def listar(self, solo_activas: bool = False):
        consulta = self.cliente.table("categorias").select("*").order("nombre")
        if solo_activas:
            consulta = consulta.eq("activo", True)
        return self.ejecutar(lambda: consulta, "categorias")

    def guardar(self, nombre: str, descripcion: str, activo: bool, categoria_id: str | None = None):
        if not nombre.strip():
            raise AppError("El nombre de la categoria es obligatorio.")
        payload = {"nombre": nombre.strip(), "descripcion": descripcion.strip() or None, "activo": activo}
        if categoria_id:
            return self.ejecutar(lambda: self.cliente.table("categorias").update(payload).eq("id", categoria_id), "actualizar categoria")
        return self.ejecutar(lambda: self.cliente.table("categorias").insert(payload), "registrar categoria")


class ProductoServicio(SupabaseServicio):
    def listar(self, busqueda: str = "", categoria_id: str = "", incluir_inactivos: bool = True):
        consulta = self.cliente.table("productos").select("*").order("nombre")
        if categoria_id:
            consulta = consulta.eq("categoria_id", categoria_id)
        if not incluir_inactivos:
            consulta = consulta.eq("activo", True)
        datos = self.ejecutar(lambda: consulta, "productos")
        if busqueda.strip():
            b = busqueda.strip().lower()
            datos = [
                p for p in datos
                if b in (p.get("codigo") or "").lower() or b in (p.get("nombre") or "").lower()
            ]
        return datos

    def guardar(self, datos: dict, producto_id: str | None = None):
        try:
            precio = Decimal(str(datos.get("precio", "0")))
            stock = int(datos.get("stock", 0))
            stock_minimo = int(datos.get("stock_minimo", 0))
        except Exception as error:
            raise AppError("Precio y stock deben ser numericos.") from error
        if not datos.get("categoria_id"):
            raise AppError("Seleccione una categoria.")
        if not datos.get("codigo", "").strip() or not datos.get("nombre", "").strip():
            raise AppError("Codigo y nombre son obligatorios.")
        if precio < 0 or stock < 0 or stock_minimo < 0:
            raise AppError("Precio y stock no pueden ser negativos.")
        payload = {
            "categoria_id": datos["categoria_id"],
            "codigo": datos["codigo"].strip(),
            "nombre": datos["nombre"].strip(),
            "descripcion": datos.get("descripcion") or None,
            "precio": float(precio),
            "stock": stock,
            "stock_minimo": stock_minimo,
            "activo": bool(datos.get("activo", True)),
        }
        if producto_id:
            return self.ejecutar(lambda: self.cliente.table("productos").update(payload).eq("id", producto_id), "actualizar producto")
        return self.ejecutar(lambda: self.cliente.table("productos").insert(payload), "registrar producto")
