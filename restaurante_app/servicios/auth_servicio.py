from modelos import Perfil
from utils.errores import AppError, mensaje_amigable


class SesionActual:
    def __init__(self) -> None:
        self.perfil: Perfil | None = None

    def iniciar(self, perfil: Perfil) -> None:
        self.perfil = perfil

    def cerrar(self) -> None:
        self.perfil = None

    @property
    def rol(self) -> str:
        return self.perfil.rol if self.perfil else ""

    @property
    def usuario_id(self) -> str:
        return self.perfil.id if self.perfil else ""


class AuthServicio:
    def __init__(self, cliente):
        self.cliente = cliente
        self.sesion = SesionActual()

    def iniciar_sesion(self, correo: str, contrasena: str) -> Perfil:
        if not correo.strip() or not contrasena:
            raise AppError("Ingrese correo y contrasena.")
        try:
            respuesta = self.cliente.auth.sign_in_with_password(
                {"email": correo.strip(), "password": contrasena}
            )
            usuario = respuesta.user
            if usuario is None:
                raise AppError("No se pudo obtener el usuario autenticado.")
            datos = (
                self.cliente.table("perfiles")
                .select("id,nombres,apellidos,rol,activo")
                .eq("id", usuario.id)
                .single()
                .execute()
                .data
            )
            if not datos:
                raise AppError("El usuario no tiene un perfil asociado en la base.")
            if not datos.get("activo", False):
                raise AppError("El perfil del usuario esta inactivo.")
            perfil = Perfil(
                id=datos["id"],
                nombres=datos.get("nombres", ""),
                apellidos=datos.get("apellidos", ""),
                rol=datos.get("rol", ""),
                activo=bool(datos.get("activo")),
                correo=correo.strip(),
            )
            self.sesion.iniciar(perfil)
            return perfil
        except AppError:
            raise
        except Exception as error:
            raise AppError(mensaje_amigable(error)) from error

    def cerrar_sesion(self) -> None:
        try:
            self.cliente.auth.sign_out()
        except Exception:
            pass
        self.sesion.cerrar()
