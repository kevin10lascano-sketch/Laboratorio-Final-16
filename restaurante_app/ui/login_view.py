import tkinter as tk
from tkinter import ttk

from config.settings import COLORES
from utils.errores import AppError


class LoginView(tk.Frame):
    def __init__(self, master, auth_servicio, assets, al_iniciar_sesion, al_salir):
        super().__init__(master, bg=COLORES["crema"])
        self.auth_servicio = auth_servicio
        self.assets = assets
        self.al_iniciar_sesion = al_iniciar_sesion
        self.al_salir = al_salir
        self.correo_entry: tk.Entry | None = None
        self.contrasena_entry: tk.Entry | None = None
        self.mensaje: tk.Label | None = None
        self.logo = None
        self._estilos()
        self._crear()

    def _estilos(self) -> None:
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure(
            "Login.TButton",
            background=COLORES["terracota"],
            foreground="white",
            padding=(14, 9),
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            focusthickness=2,
            focuscolor="#F0C7B4",
        )
        estilo.map(
            "Login.TButton",
            background=[
                ("pressed", "#884725"),
                ("active", "#A95832"),
                ("focus", "#A95832"),
                ("disabled", "#D5A58D"),
            ],
            foreground=[
                ("pressed", "white"),
                ("active", "white"),
                ("focus", "white"),
                ("disabled", "#F7EEE9"),
            ],
        )
        estilo.configure(
            "Salir.TButton",
            background=COLORES["carbon"],
            foreground="white",
            padding=(14, 9),
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
            focusthickness=2,
            focuscolor="#B8BEC4",
        )
        estilo.map(
            "Salir.TButton",
            background=[
                ("pressed", "#1F2428"),
                ("active", "#48515A"),
                ("focus", "#48515A"),
                ("disabled", "#A7ADB3"),
            ],
            foreground=[
                ("pressed", "white"),
                ("active", "white"),
                ("focus", "white"),
                ("disabled", "#ECEFF1"),
            ],
        )

    def _crear(self) -> None:
        color_panel = COLORES["verde"]
        color_texto_panel = COLORES["crema"]
        panel = tk.Frame(
            self,
            bg=color_panel,
            padx=38,
            pady=32,
            highlightbackground="#1A261F",
            highlightthickness=1,
        )
        panel.place(relx=0.5, rely=0.5, anchor="center")
        self.logo = self.assets.logo()
        if self.logo:
            tk.Label(panel, image=self.logo, bg=color_panel).pack(pady=(0, 10))
        tk.Label(panel, text="RestauranteApp", bg=color_panel, fg="white", font=("Segoe UI", 24, "bold")).pack()
        tk.Label(panel, text="Acceso con Supabase Auth", bg=color_panel, fg=color_texto_panel, font=("Segoe UI", 10)).pack(pady=(4, 22))
        tk.Label(panel, text="Correo", bg=color_panel, fg=color_texto_panel, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.correo_entry = tk.Entry(
            panel,
            width=34,
            font=("Segoe UI", 11),
            bg=COLORES["blanco"],
            fg=COLORES["texto"],
            insertbackground=COLORES["verde"],
            relief="flat",
            highlightthickness=1,
            highlightbackground="#D7CEC1",
            highlightcolor=COLORES["terracota"],
        )
        self.correo_entry.pack(pady=(5, 12), ipady=4)
        tk.Label(panel, text="Contrasena", bg=color_panel, fg=color_texto_panel, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.contrasena_entry = tk.Entry(
            panel,
            width=34,
            font=("Segoe UI", 11),
            show="*",
            bg=COLORES["blanco"],
            fg=COLORES["texto"],
            insertbackground=COLORES["verde"],
            relief="flat",
            highlightthickness=1,
            highlightbackground="#D7CEC1",
            highlightcolor=COLORES["terracota"],
        )
        self.contrasena_entry.pack(pady=(5, 12), ipady=4)
        self.mensaje = tk.Label(panel, text="", bg=color_panel, fg="#FFD2C4", wraplength=310, justify="left", font=("Segoe UI", 9))
        self.mensaje.pack(fill="x", pady=(0, 12))
        acciones = tk.Frame(panel, bg=color_panel)
        acciones.pack(fill="x")
        ttk.Button(acciones, text="Iniciar sesion", style="Login.TButton", command=self.iniciar_sesion).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(acciones, text="Salir", style="Salir.TButton", command=self.al_salir).pack(side="left", fill="x", expand=True)
        self.correo_entry.bind("<Return>", lambda _e: self.contrasena_entry.focus())
        self.contrasena_entry.bind("<Return>", lambda _e: self.iniciar_sesion())
        self.bind_all("<Escape>", lambda _e: self.al_salir())
        self.correo_entry.focus()

    def iniciar_sesion(self) -> None:
        assert self.correo_entry and self.contrasena_entry and self.mensaje
        try:
            perfil = self.auth_servicio.iniciar_sesion(self.correo_entry.get(), self.contrasena_entry.get())
        except AppError as error:
            self.mensaje.config(text=str(error))
            return
        self.mensaje.config(text="")
        self.al_iniciar_sesion(perfil)
