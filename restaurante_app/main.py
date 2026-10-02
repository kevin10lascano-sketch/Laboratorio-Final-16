import tkinter as tk
from tkinter import messagebox

from database.supabase_cliente import ConfiguracionSupabaseError, obtener_cliente_supabase
from servicios.auth_servicio import AuthServicio
from servicios.catalogos_servicio import CategoriaServicio, ClienteServicio, MesaServicio, ProductoServicio
from servicios.operaciones_servicio import EmpleadoServicio, InventarioServicio, PagoServicio, PedidoServicio
from ui.login_view import LoginView
from ui.main_view import MainView
from utils.assets import AssetManager
from utils.ventanas import centrar_ventana


class AplicacionRestaurante:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("RestauranteApp")
        self.root.minsize(980, 640)
        centrar_ventana(self.root, 1180, 720)
        self.assets = AssetManager()
        icono = self.assets.logo("icono.png")
        if icono:
            self.root.iconphoto(True, icono)
        self.vista_actual: tk.Frame | None = None
        self.servicios = self._crear_servicios()
        self.mostrar_login()

    def _crear_servicios(self) -> dict:
        cliente = obtener_cliente_supabase()
        auth = AuthServicio(cliente)
        return {
            "auth": auth,
            "clientes": ClienteServicio(cliente),
            "mesas": MesaServicio(cliente),
            "categorias": CategoriaServicio(cliente),
            "productos": ProductoServicio(cliente),
            "empleados": EmpleadoServicio(cliente),
            "inventario": InventarioServicio(cliente),
            "pedidos": PedidoServicio(cliente),
            "pagos": PagoServicio(cliente),
        }

    def cambiar_vista(self, vista: tk.Frame) -> None:
        if self.vista_actual is not None:
            self.vista_actual.destroy()
        self.vista_actual = vista
        self.vista_actual.pack(fill="both", expand=True)

    def mostrar_login(self) -> None:
        self.cambiar_vista(
            LoginView(
                self.root,
                self.servicios["auth"],
                self.assets,
                self.mostrar_principal,
                self.root.destroy,
            )
        )

    def mostrar_principal(self, perfil) -> None:
        self.cambiar_vista(
            MainView(
                self.root,
                self.servicios,
                perfil,
                self.assets,
                self.mostrar_login,
            )
        )

    def ejecutar(self) -> None:
        self.root.mainloop()


def main() -> None:
    try:
        app = AplicacionRestaurante()
    except ConfiguracionSupabaseError as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Configuracion Supabase", str(error))
        return
    app.ejecutar()


if __name__ == "__main__":
    main()
