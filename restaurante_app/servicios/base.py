from typing import Any

from utils.errores import AppError, mensaje_amigable


class SupabaseServicio:
    def __init__(self, cliente: Any):
        self.cliente = cliente

    def ejecutar(self, operacion, contexto: str = "operacion"):
        try:
            respuesta = operacion().execute()
            return respuesta.data or []
        except Exception as error:
            raise AppError(f"{contexto}: {mensaje_amigable(error)}") from error

    def rpc(self, nombre: str, parametros: dict):
        try:
            respuesta = self.cliente.rpc(nombre, parametros).execute()
            return respuesta.data
        except Exception as error:
            raise AppError(mensaje_amigable(error)) from error
