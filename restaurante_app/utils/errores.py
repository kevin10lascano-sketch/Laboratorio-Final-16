class AppError(Exception):
    """Error esperado que puede mostrarse al usuario."""


def mensaje_amigable(error: Exception) -> str:
    texto = str(error)
    equivalencias = {
        "Invalid login credentials": "Correo o contrasena incorrectos.",
        "Email not confirmed": "El correo aun no ha sido confirmado.",
        "duplicate key": "Ya existe un registro con esos datos.",
        "violates row-level security": "No tiene permisos para realizar esta accion.",
        "Stock insuficiente": "No hay stock suficiente para completar la operacion.",
        "La mesa debe estar LIBRE": "Seleccione una mesa libre para abrir el pedido.",
        "No se puede modificar": "El registro no puede modificarse en su estado actual.",
    }
    for clave, mensaje in equivalencias.items():
        if clave.lower() in texto.lower():
            return mensaje
    if texto:
        return texto.split("\n")[0][:220]
    return "Ocurrio un problema inesperado."
