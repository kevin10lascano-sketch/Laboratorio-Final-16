from datetime import date
from decimal import Decimal
import tkinter as tk
from tkinter import messagebox, ttk

from config.settings import COLORES
from reportes.pdf_reportes import ReportePDFServicio
from utils.errores import AppError


class MainView(tk.Frame):
    def __init__(self, master, servicios: dict, perfil, assets, al_cerrar_sesion):
        super().__init__(master, bg=COLORES["crema"])
        self.servicios = servicios
        self.perfil = perfil
        self.assets = assets
        self.al_cerrar_sesion = al_cerrar_sesion
        self.reportes = ReportePDFServicio()
        self.contenido: tk.Frame | None = None
        self.estado: tk.Label | None = None
        self.botones_menu: dict[str, ttk.Button] = {}
        self.iconos_vista: dict[str, tk.PhotoImage] = {}
        self.ids: dict[str, str] = {}
        self.cache: dict[str, list[dict]] = {}
        self.widgets: dict[str, object] = {}
        self._estilos()
        self._crear_shell()
        self._atajos_globales()
        self.mostrar_dashboard()

    def _estilos(self) -> None:
        estilo = ttk.Style()
        estilo.theme_use("clam")
        self._configurar_boton(
            estilo,
            "Menu.TButton",
            fondo=COLORES["verde"],
            hover="#31483A",
            presionado="#18241D",
            foco="#31483A",
            padding=(12, 10),
            anchor="w",
            font=("Segoe UI", 10, "bold"),
        )
        self._configurar_boton(
            estilo,
            "MenuActivo.TButton",
            fondo=COLORES["terracota"],
            hover="#A95832",
            presionado="#884725",
            foco="#A95832",
            padding=(12, 10),
            anchor="w",
            font=("Segoe UI", 10, "bold"),
        )
        self._configurar_boton(
            estilo,
            "Accion.TButton",
            fondo=COLORES["terracota"],
            hover="#A95832",
            presionado="#884725",
            foco="#A95832",
            padding=(10, 7),
            font=("Segoe UI", 9, "bold"),
        )
        self._configurar_boton(
            estilo,
            "Secundario.TButton",
            fondo=COLORES["carbon"],
            hover="#48515A",
            presionado="#1F2428",
            foco="#48515A",
            padding=(10, 7),
            font=("Segoe UI", 9, "bold"),
        )
        self._configurar_boton(
            estilo,
            "Peligro.TButton",
            fondo=COLORES["error"],
            hover="#8F1B13",
            presionado="#6F140E",
            foco="#8F1B13",
            padding=(10, 7),
            font=("Segoe UI", 9, "bold"),
        )
        estilo.configure(
            "Treeview.Heading",
            background=COLORES["verde"],
            foreground="white",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        )
        estilo.map(
            "Treeview.Heading",
            background=[("active", "#31483A"), ("pressed", "#18241D")],
            foreground=[("active", "white"), ("pressed", "white")],
        )
        estilo.configure(
            "Treeview",
            rowheight=27,
            font=("Segoe UI", 9),
            background="white",
            fieldbackground="white",
            foreground=COLORES["texto"],
            bordercolor=COLORES["borde"],
            lightcolor=COLORES["borde"],
            darkcolor=COLORES["borde"],
        )
        estilo.map(
            "Treeview",
            background=[
                ("selected", COLORES["verde"]),
                ("focus", "#EEF4EF"),
            ],
            foreground=[
                ("selected", "white"),
                ("focus", COLORES["texto"]),
            ],
        )

    def _configurar_boton(
        self,
        estilo: ttk.Style,
        nombre: str,
        fondo: str,
        hover: str,
        presionado: str,
        foco: str,
        padding,
        font,
        anchor: str = "center",
    ) -> None:
        estilo.configure(
            nombre,
            background=fondo,
            foreground="white",
            padding=padding,
            borderwidth=0,
            focusthickness=2,
            focuscolor="#E7D3C9",
            anchor=anchor,
            font=font,
        )
        estilo.map(
            nombre,
            background=[
                ("disabled", "#B8B8B8"),
                ("pressed", presionado),
                ("active", hover),
                ("focus", foco),
            ],
            foreground=[
                ("disabled", "#F4F4F4"),
                ("pressed", "white"),
                ("active", "white"),
                ("focus", "white"),
            ],
        )

    def _crear_shell(self) -> None:
        sidebar = tk.Frame(self, bg=COLORES["verde"], width=232)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        canvas_menu = tk.Canvas(
            sidebar,
            bg=COLORES["verde"],
            highlightthickness=0,
            borderwidth=0,
            width=216,
        )
        scroll_menu = ttk.Scrollbar(sidebar, orient="vertical", command=canvas_menu.yview)
        canvas_menu.configure(yscrollcommand=scroll_menu.set)
        scroll_menu.pack(side="right", fill="y")
        canvas_menu.pack(side="left", fill="both", expand=True)

        frame_menu = tk.Frame(canvas_menu, bg=COLORES["verde"], padx=14, pady=16)
        ventana_menu = canvas_menu.create_window((0, 0), window=frame_menu, anchor="nw")

        def ajustar_scroll(_event=None):
            canvas_menu.configure(scrollregion=canvas_menu.bbox("all"))

        def ajustar_ancho(event):
            canvas_menu.itemconfigure(ventana_menu, width=event.width)

        def activar_rueda(_event):
            canvas_menu.bind_all("<MouseWheel>", desplazar_menu)

        def desactivar_rueda(_event):
            canvas_menu.unbind_all("<MouseWheel>")

        def desplazar_menu(event):
            canvas_menu.yview_scroll(int(-1 * (event.delta / 120)), "units")

        frame_menu.bind("<Configure>", ajustar_scroll)
        canvas_menu.bind("<Configure>", ajustar_ancho)
        sidebar.bind("<Enter>", activar_rueda)
        sidebar.bind("<Leave>", desactivar_rueda)

        tk.Label(frame_menu, text="RestauranteApp", bg=COLORES["verde"], fg="white", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        tk.Label(frame_menu, text=f"{self.perfil.nombre_completo}\n{self.perfil.rol}", bg=COLORES["verde"], fg=COLORES["crema"], justify="left", font=("Segoe UI", 9)).pack(anchor="w", pady=(6, 18))
        for nombre, comando, roles in self._modulos():
            if self.perfil.rol in roles:
                boton = self._boton(
                    frame_menu,
                    nombre,
                    comando,
                    "Menu.TButton",
                    self._iconos_menu(nombre),
                )
                boton.pack(fill="x", pady=(0, 7))
                self.botones_menu[nombre] = boton
        tk.Frame(frame_menu, bg=COLORES["verde"], height=16).pack(fill="x")
        self._boton(frame_menu, "Cerrar sesion", self.cerrar_sesion, "Peligro.TButton", ("logout.png",)).pack(fill="x")
        principal = tk.Frame(self, bg=COLORES["crema"])
        principal.pack(side="left", fill="both", expand=True)
        header = tk.Frame(principal, bg=COLORES["blanco"], padx=20, pady=10, highlightbackground=COLORES["borde"], highlightthickness=1)
        header.pack(fill="x")
        tk.Label(header, text="Sistema administrativo de restaurante", bg=COLORES["blanco"], fg=COLORES["verde"], font=("Segoe UI", 13, "bold")).pack(side="left")
        tk.Label(header, text=f"{self.perfil.correo}", bg=COLORES["blanco"], fg=COLORES["carbon"], font=("Segoe UI", 9)).pack(side="right")
        self.contenido = tk.Frame(principal, bg=COLORES["crema"], padx=22, pady=18)
        self.contenido.pack(fill="both", expand=True)
        pie = tk.Frame(principal, bg=COLORES["blanco"], padx=16, pady=7, highlightbackground=COLORES["borde"], highlightthickness=1)
        pie.pack(fill="x", side="bottom")
        self.estado = tk.Label(pie, text="F5: actualizar | Ctrl+F: buscar | Ctrl+N: nuevo | Escape: limpiar/cancelar", bg=COLORES["blanco"], fg=COLORES["carbon"], font=("Segoe UI", 9))
        self.estado.pack(side="left")

    def _modulos(self):
        todos = ("ADMINISTRADOR", "MESERO", "CAJERO")
        return [
            ("Dashboard", self.mostrar_dashboard, todos),
            ("Mesas", self.mostrar_mesas, ("ADMINISTRADOR", "MESERO")),
            ("Pedidos", self.mostrar_pedidos, ("ADMINISTRADOR", "MESERO")),
            ("Clientes", self.mostrar_clientes, todos),
            ("Productos", self.mostrar_productos, ("ADMINISTRADOR", "MESERO")),
            ("Categorias", self.mostrar_categorias, ("ADMINISTRADOR",)),
            ("Inventario", self.mostrar_inventario, ("ADMINISTRADOR",)),
            ("Caja", self.mostrar_caja, ("ADMINISTRADOR", "CAJERO")),
            ("Empleados", self.mostrar_empleados, ("ADMINISTRADOR",)),
            ("Reportes", self.mostrar_reportes, ("ADMINISTRADOR",)),
        ]

    def _iconos_menu(self, modulo: str) -> tuple[str, ...]:
        mapa = {
            "Dashboard": ("dashboard.png",),
            "Mesas": ("mesas.png",),
            "Pedidos": ("pedidos.png",),
            "Clientes": ("clientes.png",),
            "Productos": ("productos.png",),
            "Categorias": ("categorias.png",),
            "Inventario": ("inventario.png",),
            "Caja": ("caja.png",),
            "Empleados": ("empleados.png",),
            "Reportes": ("reportes.png",),
        }
        return mapa.get(modulo, ())

    def _boton(self, padre, texto: str, comando, estilo: str, iconos: tuple[str, ...] = ()):
        imagen = None
        if iconos:
            imagen = self.assets.icono(iconos[0], iconos[1:])
        if imagen is not None:
            self.iconos_vista[f"{texto}-{len(self.iconos_vista)}"] = imagen
            return ttk.Button(
                padre,
                text=f"  {texto}",
                image=imagen,
                compound="left",
                style=estilo,
                command=comando,
            )
        return ttk.Button(padre, text=texto, style=estilo, command=comando)

    def _atajos_globales(self) -> None:
        self.bind_all("<F5>", lambda _e: self._refrescar_actual())
        self.bind_all("<Control-f>", lambda _e: self._enfocar_busqueda())
        self.bind_all("<Control-n>", lambda _e: self._limpiar_actual())
        self.bind_all("<Escape>", lambda _e: self._limpiar_actual())

    def limpiar(self) -> None:
        assert self.contenido is not None
        ids_persistentes = {
            clave: valor
            for clave, valor in self.ids.items()
            if clave in ("pedido", "mesa_preseleccionada", "ultimo_pagado")
        }
        for hijo in self.contenido.winfo_children():
            hijo.destroy()
        self.widgets.clear()
        self.ids = ids_persistentes

    def seccion(self, nombre: str, subtitulo: str = "") -> None:
        self.limpiar()
        for texto, boton in self.botones_menu.items():
            boton.configure(style="MenuActivo.TButton" if texto == nombre else "Menu.TButton")
        assert self.contenido is not None
        tk.Label(self.contenido, text=nombre, bg=COLORES["crema"], fg=COLORES["verde"], font=("Segoe UI", 21, "bold")).pack(anchor="w")
        if subtitulo:
            tk.Label(self.contenido, text=subtitulo, bg=COLORES["crema"], fg=COLORES["carbon"], font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 14))

    def area_scroll(self, padre):
        contenedor = tk.Frame(padre, bg=COLORES["crema"])
        contenedor.pack(fill="both", expand=True)
        canvas = tk.Canvas(contenedor, bg=COLORES["crema"], highlightthickness=0, borderwidth=0)
        scroll = ttk.Scrollbar(contenedor, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        interior = tk.Frame(canvas, bg=COLORES["crema"])
        ventana = canvas.create_window((0, 0), window=interior, anchor="nw")

        def actualizar_region(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def ajustar_ancho(event):
            canvas.itemconfigure(ventana, width=event.width)

        def desplazar(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def activar_rueda(_event):
            canvas.bind_all("<MouseWheel>", desplazar)

        def desactivar_rueda(_event):
            canvas.unbind_all("<MouseWheel>")

        interior.bind("<Configure>", actualizar_region)
        canvas.bind("<Configure>", ajustar_ancho)
        contenedor.bind("<Enter>", activar_rueda)
        contenedor.bind("<Leave>", desactivar_rueda)
        return interior

    def panel(self, padre, titulo: str):
        frame = tk.LabelFrame(padre, text=titulo, bg=COLORES["blanco"], fg=COLORES["verde"], padx=12, pady=12, font=("Segoe UI", 10, "bold"))
        return frame

    def campo(self, padre, etiqueta: str, fila: int, clave: str, ancho: int = 24):
        tk.Label(padre, text=etiqueta, bg=COLORES["blanco"], fg=COLORES["texto"], font=("Segoe UI", 9, "bold")).grid(row=fila, column=0, sticky="w", pady=(0, 7), padx=(0, 8))
        entrada = tk.Entry(padre, width=ancho, font=("Segoe UI", 9))
        entrada.grid(row=fila, column=1, sticky="ew", pady=(0, 7))
        self.widgets[clave] = entrada
        return entrada

    def combo(self, padre, etiqueta: str, fila: int, clave: str, valores=()):
        tk.Label(padre, text=etiqueta, bg=COLORES["blanco"], fg=COLORES["texto"], font=("Segoe UI", 9, "bold")).grid(row=fila, column=0, sticky="w", pady=(0, 7), padx=(0, 8))
        combo = ttk.Combobox(padre, values=list(valores), state="readonly", width=25)
        combo.grid(row=fila, column=1, sticky="ew", pady=(0, 7))
        self.widgets[clave] = combo
        return combo

    def tabla(self, padre, columnas: tuple[str, ...], encabezados: tuple[str, ...], clave: str):
        marco = tk.Frame(padre, bg=COLORES["blanco"])
        marco.pack(fill="both", expand=True)
        tree = ttk.Treeview(marco, columns=columnas, show="headings")
        scroll_y = ttk.Scrollbar(marco, orient="vertical", command=tree.yview)
        scroll_x = ttk.Scrollbar(marco, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        for col, enc in zip(columnas, encabezados):
            tree.heading(col, text=enc)
            tree.column(col, width=120, anchor="w")
        tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        marco.grid_rowconfigure(0, weight=1)
        marco.grid_columnconfigure(0, weight=1)
        self.widgets[clave] = tree
        return tree

    def _limpiar_tabla(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    def _nombre_cliente(self, cliente: dict | None) -> str:
        if not cliente:
            return "Cliente no encontrado"
        return f"{cliente.get('nombres', '')} {cliente.get('apellidos') or ''}".strip()

    def _entry(self, clave: str) -> str:
        widget = self.widgets.get(clave)
        return widget.get().strip() if widget else ""

    def _set_entry(self, clave: str, valor) -> None:
        widget = self.widgets.get(clave)
        if isinstance(widget, ttk.Combobox):
            widget.set("" if valor is None else str(valor))
            return
        if widget:
            widget.delete(0, tk.END)
            widget.insert(0, "" if valor is None else str(valor))

    def _mensaje(self, texto: str) -> None:
        if self.estado:
            self.estado.config(text=texto)

    def manejar_error(self, titulo: str, error: Exception) -> None:
        messagebox.showerror(titulo, str(error))
        self._mensaje(str(error))

    def _refrescar_actual(self):
        actual = next((n for n, b in self.botones_menu.items() if str(b.cget("style")) == "MenuActivo.TButton"), "Dashboard")
        getattr(self, f"mostrar_{actual.lower()}", self.mostrar_dashboard)()

    def _enfocar_busqueda(self):
        busqueda = self.widgets.get("busqueda")
        if busqueda:
            busqueda.focus()

    def _limpiar_actual(self):
        for widget in self.widgets.values():
            if isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)
            elif isinstance(widget, ttk.Combobox):
                widget.set("")

    # Dashboard
    def mostrar_dashboard(self):
        self.seccion("Dashboard", "Resumen operativo segun el rol actual.")
        datos = self._datos_basicos()
        pedidos = datos["pedidos"]
        pagos = datos["pagos"]
        productos = datos["productos"]
        mesas = datos["mesas"]
        if self.perfil.rol == "CAJERO":
            metricas = [
                ("Pedidos por cobrar", sum(1 for p in pedidos if p["estado"] == "CONFIRMADO")),
                ("Ventas registradas", len(pagos)),
                ("Total ventas", f"${sum(Decimal(str(p.get('monto', 0))) for p in pagos):.2f}"),
            ]
        elif self.perfil.rol == "MESERO":
            metricas = [
                ("Mesas libres", sum(1 for m in mesas if m["estado"] == "LIBRE")),
                ("Mesas ocupadas", sum(1 for m in mesas if m["estado"] == "OCUPADA")),
                ("Pedidos abiertos", sum(1 for p in pedidos if p["estado"] == "ABIERTO")),
                ("Pedidos confirmados", sum(1 for p in pedidos if p["estado"] == "CONFIRMADO")),
            ]
        else:
            metricas = [
                ("Mesas libres", sum(1 for m in mesas if m["estado"] == "LIBRE")),
                ("Mesas ocupadas", sum(1 for m in mesas if m["estado"] == "OCUPADA")),
                ("Pedidos abiertos", sum(1 for p in pedidos if p["estado"] == "ABIERTO")),
                ("Ventas", f"${sum(Decimal(str(p.get('monto', 0))) for p in pagos):.2f}"),
                ("Stock bajo", sum(1 for p in productos if int(p.get("stock", 0)) <= int(p.get("stock_minimo", 0)))),
            ]
        grid = tk.Frame(self.contenido, bg=COLORES["crema"])
        grid.pack(fill="x", pady=(8, 0))
        for i, (titulo, valor) in enumerate(metricas):
            card = tk.Frame(grid, bg=COLORES["blanco"], padx=16, pady=14, highlightbackground=COLORES["borde"], highlightthickness=1)
            card.grid(row=i // 3, column=i % 3, sticky="ew", padx=(0, 12), pady=(0, 12))
            grid.grid_columnconfigure(i % 3, weight=1)
            tk.Label(card, text=titulo, bg=COLORES["blanco"], fg=COLORES["carbon"], font=("Segoe UI", 10, "bold")).pack(anchor="w")
            tk.Label(card, text=str(valor), bg=COLORES["blanco"], fg=COLORES["terracota"], font=("Segoe UI", 24, "bold")).pack(anchor="w")

    def _datos_basicos(self):
        try:
            return {
                "mesas": self.servicios["mesas"].listar(),
                "pedidos": self.servicios["pedidos"].listar(),
                "pagos": self.servicios["pagos"].listar() if self.perfil.rol in ("ADMINISTRADOR", "CAJERO") else [],
                "productos": self.servicios["productos"].listar(incluir_inactivos=True),
            }
        except AppError as error:
            self.manejar_error("Dashboard", error)
            return {"mesas": [], "pedidos": [], "pagos": [], "productos": []}

    # Mesas
    def mostrar_mesas(self):
        self.seccion("Mesas", "Vista visual de disponibilidad. Doble clic en una mesa ocupada para revisar pedidos.")
        barra = tk.Frame(self.contenido, bg=COLORES["crema"])
        barra.pack(fill="x", pady=(0, 10))
        self._boton(barra, "Actualizar", self.mostrar_mesas, "Secundario.TButton", ("actualizar.png",)).pack(side="left")
        cuerpo = tk.Frame(self.contenido, bg=COLORES["crema"])
        cuerpo.pack(fill="both", expand=True)
        try:
            mesas = self.servicios["mesas"].listar()
        except AppError as error:
            self.manejar_error("Mesas", error)
            return
        for i, mesa in enumerate(mesas):
            libre = mesa["estado"] == "LIBRE"
            color = COLORES["libre"] if libre else COLORES["ocupada"]
            card = tk.Frame(cuerpo, bg=color, padx=14, pady=12, highlightbackground=COLORES["borde"], highlightthickness=1)
            card.grid(row=i // 4, column=i % 4, sticky="nsew", padx=(0, 12), pady=(0, 12))
            cuerpo.grid_columnconfigure(i % 4, weight=1)
            tk.Label(card, text=f"Mesa {mesa['numero']}", bg=color, fg=COLORES["verde"], font=("Segoe UI", 16, "bold")).pack(anchor="w")
            tk.Label(card, text=f"Capacidad: {mesa['capacidad']} personas", bg=color, fg=COLORES["texto"]).pack(anchor="w")
            tk.Label(card, text=f"Estado: {mesa['estado']}", bg=color, fg=COLORES["texto"], font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 0))
            accion = "Abrir pedido" if libre else "Ver pedido"
            self._boton(
                card,
                accion,
                lambda mesa_actual=mesa: self.ir_a_pedidos_desde_mesa(mesa_actual),
                "Accion.TButton",
                ("pedidos.png",),
            ).pack(anchor="w", pady=(10, 0))

    def ir_a_pedidos_desde_mesa(self, mesa: dict):
        self.ids["mesa_preseleccionada"] = mesa["id"]
        self.cache["mesa_preseleccionada"] = mesa
        try:
            activos = [
                p for p in self.servicios["pedidos"].listar()
                if p.get("mesa_id") == mesa["id"] and p.get("estado") in ("ABIERTO", "CONFIRMADO")
            ]
        except AppError as error:
            self.manejar_error("Mesas", error)
            return
        if activos:
            self.ids["pedido"] = activos[0]["id"]
        else:
            self.ids.pop("pedido", None)
        self.mostrar_pedidos()

    # Clientes
    def mostrar_clientes(self):
        self.seccion("Clientes", "Busqueda, registro y desactivacion de clientes.")
        self._vista_crud_clientes()

    def _vista_crud_clientes(self):
        cuerpo = tk.Frame(self.contenido, bg=COLORES["crema"])
        cuerpo.pack(fill="both", expand=True)
        cuerpo.grid_columnconfigure(1, weight=1)
        form = self.panel(cuerpo, "Datos del cliente")
        form.grid(row=0, column=0, sticky="n", padx=(0, 14))
        self.campo(form, "Identificacion", 0, "identificacion")
        self.campo(form, "Nombres", 1, "nombres")
        self.campo(form, "Apellidos", 2, "apellidos")
        self.campo(form, "Telefono", 3, "telefono")
        self.campo(form, "Correo", 4, "correo")
        activo = tk.BooleanVar(value=True)
        self.widgets["activo_var"] = activo
        tk.Checkbutton(form, text="Activo", variable=activo, bg=COLORES["blanco"]).grid(row=5, column=1, sticky="w")
        self._boton(form, "Guardar", self.guardar_cliente, "Accion.TButton", ("guardar.png",)).grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 6))
        self._boton(form, "Limpiar", self._limpiar_actual, "Secundario.TButton", ("clean.png",)).grid(row=7, column=0, columnspan=2, sticky="ew")
        lista = self.panel(cuerpo, "Clientes")
        lista.grid(row=0, column=1, sticky="nsew")
        top = tk.Frame(lista, bg=COLORES["blanco"])
        top.pack(fill="x", pady=(0, 8))
        self.campo(top, "Buscar", 0, "busqueda", 30)
        self._boton(top, "Buscar", self.refrescar_clientes, "Secundario.TButton", ("search.png",)).grid(row=0, column=2, padx=(8, 0))
        tree = self.tabla(lista, ("identificacion", "nombres", "telefono", "estado"), ("Identificacion", "Cliente", "Telefono", "Estado"), "tabla_clientes")
        tree.bind("<<TreeviewSelect>>", self.seleccionar_cliente)
        self.refrescar_clientes()

    def refrescar_clientes(self):
        tree = self.widgets.get("tabla_clientes")
        if not tree:
            return
        self._limpiar_tabla(tree)
        try:
            datos = self.servicios["clientes"].listar(self._entry("busqueda"))
        except AppError as error:
            self.manejar_error("Clientes", error)
            return
        self.cache["clientes"] = datos
        for c in datos:
            iid = c["id"]
            self.ids[iid] = iid
            tree.insert("", tk.END, iid=iid, values=(c.get("identificacion") or "Consumidor Final", f"{c.get('nombres','')} {c.get('apellidos') or ''}", c.get("telefono") or "", "Activo" if c.get("activo") else "Inactivo"))

    def seleccionar_cliente(self, _event=None):
        tree = self.widgets["tabla_clientes"]
        sel = tree.selection()
        if not sel:
            return
        cliente = next((c for c in self.cache.get("clientes", []) if c["id"] == sel[0]), None)
        if not cliente:
            return
        self.ids["cliente"] = cliente["id"]
        for clave in ("identificacion", "nombres", "apellidos", "telefono", "correo"):
            self._set_entry(clave, cliente.get(clave))
        self.widgets["activo_var"].set(bool(cliente.get("activo")))

    def guardar_cliente(self):
        try:
            self.servicios["clientes"].guardar({
                "identificacion": self._entry("identificacion"),
                "nombres": self._entry("nombres"),
                "apellidos": self._entry("apellidos"),
                "telefono": self._entry("telefono"),
                "correo": self._entry("correo"),
                "activo": self.widgets["activo_var"].get(),
            }, self.ids.get("cliente"))
            self.ids.pop("cliente", None)
            self.refrescar_clientes()
            self._mensaje("Cliente guardado correctamente.")
        except AppError as error:
            self.manejar_error("Clientes", error)

    # Categorias y productos
    def mostrar_categorias(self):
        self.seccion("Categorias", "Administracion sencilla del menu.")
        cuerpo = tk.Frame(self.contenido, bg=COLORES["crema"])
        cuerpo.pack(fill="both", expand=True)
        cuerpo.grid_columnconfigure(1, weight=1)
        form = self.panel(cuerpo, "Categoria")
        form.grid(row=0, column=0, sticky="n", padx=(0, 14))
        self.campo(form, "Nombre", 0, "nombre")
        self.campo(form, "Descripcion", 1, "descripcion")
        activo = tk.BooleanVar(value=True)
        self.widgets["activo_var"] = activo
        tk.Checkbutton(form, text="Activa", variable=activo, bg=COLORES["blanco"]).grid(row=2, column=1, sticky="w")
        self._boton(form, "Guardar", self.guardar_categoria, "Accion.TButton", ("guardar.png",)).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        lista = self.panel(cuerpo, "Categorias")
        lista.grid(row=0, column=1, sticky="nsew")
        tree = self.tabla(lista, ("nombre", "descripcion", "estado"), ("Nombre", "Descripcion", "Estado"), "tabla_categorias")
        tree.bind("<<TreeviewSelect>>", self.seleccionar_categoria)
        self.refrescar_categorias()

    def refrescar_categorias(self):
        tree = self.widgets.get("tabla_categorias")
        if not tree:
            return
        self._limpiar_tabla(tree)
        try:
            datos = self.servicios["categorias"].listar()
        except AppError as error:
            self.manejar_error("Categorias", error)
            return
        self.cache["categorias"] = datos
        for c in datos:
            tree.insert("", tk.END, iid=c["id"], values=(c["nombre"], c.get("descripcion") or "", "Activa" if c.get("activo") else "Inactiva"))

    def seleccionar_categoria(self, _event=None):
        tree = self.widgets["tabla_categorias"]
        sel = tree.selection()
        if not sel:
            return
        cat = next((c for c in self.cache.get("categorias", []) if c["id"] == sel[0]), None)
        if cat:
            self.ids["categoria"] = cat["id"]
            self._set_entry("nombre", cat.get("nombre"))
            self._set_entry("descripcion", cat.get("descripcion"))
            self.widgets["activo_var"].set(bool(cat.get("activo")))

    def guardar_categoria(self):
        try:
            self.servicios["categorias"].guardar(self._entry("nombre"), self._entry("descripcion"), self.widgets["activo_var"].get(), self.ids.get("categoria"))
            self.ids.pop("categoria", None)
            self.refrescar_categorias()
            self._mensaje("Categoria guardada.")
        except AppError as error:
            self.manejar_error("Categorias", error)

    def mostrar_productos(self):
        self.seccion("Productos", "Productos vendibles con precio, stock y estado.")
        cuerpo = tk.Frame(self.contenido, bg=COLORES["crema"])
        cuerpo.pack(fill="both", expand=True)
        cuerpo.grid_columnconfigure(1, weight=1)
        form = self.panel(cuerpo, "Producto")
        form.grid(row=0, column=0, sticky="n", padx=(0, 14))
        cats = self._opciones_categorias()
        self.combo(form, "Categoria", 0, "categoria", cats.keys())
        self.campo(form, "Codigo", 1, "codigo")
        self.campo(form, "Nombre", 2, "nombre")
        self.campo(form, "Descripcion", 3, "descripcion")
        self.campo(form, "Precio", 4, "precio")
        self.campo(form, "Stock", 5, "stock")
        self.campo(form, "Stock minimo", 6, "stock_minimo")
        activo = tk.BooleanVar(value=True)
        self.widgets["activo_var"] = activo
        self.cache["cat_options"] = cats
        tk.Checkbutton(form, text="Activo", variable=activo, bg=COLORES["blanco"]).grid(row=7, column=1, sticky="w")
        self._boton(form, "Guardar", self.guardar_producto, "Accion.TButton", ("guardar.png",)).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        lista = self.panel(cuerpo, "Productos")
        lista.grid(row=0, column=1, sticky="nsew")
        top = tk.Frame(lista, bg=COLORES["blanco"])
        top.pack(fill="x", pady=(0, 8))
        self.campo(top, "Buscar", 0, "busqueda", 30)
        self._boton(top, "Buscar", self.refrescar_productos, "Secundario.TButton", ("search.png",)).grid(row=0, column=2, padx=(8, 0))
        tree = self.tabla(lista, ("codigo", "nombre", "precio", "stock", "estado"), ("Codigo", "Producto", "Precio", "Stock", "Estado"), "tabla_productos")
        tree.bind("<<TreeviewSelect>>", self.seleccionar_producto)
        self.refrescar_productos()

    def _opciones_categorias(self):
        try:
            cats = self.servicios["categorias"].listar(solo_activas=True)
        except AppError:
            cats = []
        return {c["nombre"]: c["id"] for c in cats}

    def refrescar_productos(self):
        tree = self.widgets.get("tabla_productos")
        if not tree:
            return
        self._limpiar_tabla(tree)
        try:
            datos = self.servicios["productos"].listar(self._entry("busqueda"), incluir_inactivos=True)
        except AppError as error:
            self.manejar_error("Productos", error)
            return
        self.cache["productos"] = datos
        for p in datos:
            estado = "Inactivo" if not p.get("activo") else "Agotado" if int(p.get("stock", 0)) == 0 else "Stock bajo" if int(p.get("stock", 0)) <= int(p.get("stock_minimo", 0)) else "Disponible"
            tree.insert("", tk.END, iid=p["id"], values=(p["codigo"], p["nombre"], f"${Decimal(str(p['precio'])):.2f}", p["stock"], estado))

    def seleccionar_producto(self, _event=None):
        tree = self.widgets["tabla_productos"]
        sel = tree.selection()
        if not sel:
            return
        prod = next((p for p in self.cache.get("productos", []) if p["id"] == sel[0]), None)
        if not prod:
            return
        self.ids["producto"] = prod["id"]
        cat_nombre = next((n for n, cid in self.cache.get("cat_options", {}).items() if cid == prod.get("categoria_id")), "")
        self._set_entry("categoria", cat_nombre)
        for clave in ("codigo", "nombre", "descripcion", "precio", "stock", "stock_minimo"):
            self._set_entry(clave, prod.get(clave))
        self.widgets["activo_var"].set(bool(prod.get("activo")))

    def guardar_producto(self):
        try:
            categoria_id = self.cache.get("cat_options", {}).get(self._entry("categoria"), "")
            self.servicios["productos"].guardar({
                "categoria_id": categoria_id,
                "codigo": self._entry("codigo"),
                "nombre": self._entry("nombre"),
                "descripcion": self._entry("descripcion"),
                "precio": self._entry("precio"),
                "stock": self._entry("stock") or "0",
                "stock_minimo": self._entry("stock_minimo") or "0",
                "activo": self.widgets["activo_var"].get(),
            }, self.ids.get("producto"))
            self.ids.pop("producto", None)
            self.refrescar_productos()
            self._mensaje("Producto guardado.")
        except AppError as error:
            self.manejar_error("Productos", error)

    # Inventario
    def mostrar_inventario(self):
        self.seccion("Inventario", "Entradas y ajustes quedan auditados; salidas se generan por venta.")
        cuerpo = tk.Frame(self.contenido, bg=COLORES["crema"])
        cuerpo.pack(fill="both", expand=True)
        cuerpo.grid_columnconfigure(1, weight=1)
        form = self.panel(cuerpo, "Movimiento")
        form.grid(row=0, column=0, sticky="n", padx=(0, 14))
        productos = {f"{p['codigo']} - {p['nombre']}": p for p in self.servicios["productos"].listar(incluir_inactivos=False)}
        self.cache["prod_options"] = productos
        self.combo(form, "Producto", 0, "producto_combo", productos.keys())
        self.combo(form, "Tipo", 1, "tipo", ("ENTRADA", "AJUSTE"))
        self.campo(form, "Cantidad / stock nuevo", 2, "cantidad")
        self.campo(form, "Observacion", 3, "observacion")
        self._boton(form, "Registrar movimiento", self.registrar_movimiento, "Accion.TButton", ("inventario.png",)).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        lista = self.panel(cuerpo, "Stock actual y movimientos")
        lista.grid(row=0, column=1, sticky="nsew")
        tree = self.tabla(lista, ("codigo", "producto", "stock", "minimo", "estado"), ("Codigo", "Producto", "Stock", "Min.", "Estado"), "tabla_inventario")
        self.refrescar_inventario(tree)

    def refrescar_inventario(self, tree=None):
        tree = tree or self.widgets.get("tabla_inventario")
        if not tree:
            return
        self._limpiar_tabla(tree)
        for p in self.servicios["productos"].listar(incluir_inactivos=True):
            estado = "Agotado" if int(p["stock"]) == 0 else "Stock bajo" if int(p["stock"]) <= int(p["stock_minimo"]) else "OK"
            tree.insert("", tk.END, iid=p["id"], values=(p["codigo"], p["nombre"], p["stock"], p["stock_minimo"], estado))

    def registrar_movimiento(self):
        try:
            producto = self.cache["prod_options"].get(self._entry("producto_combo"))
            if not producto:
                raise AppError("Seleccione un producto.")
            self.servicios["inventario"].registrar_movimiento(producto, self._entry("tipo"), int(self._entry("cantidad")), self._entry("observacion"), self.perfil.id)
            self.mostrar_inventario()
            self._mensaje("Movimiento registrado.")
        except (ValueError, AppError) as error:
            self.manejar_error("Inventario", error)

    # Pedidos
    def _flujo_pedidos(self, padre):
        flujo = tk.Frame(padre, bg=COLORES["crema"])
        flujo.pack(fill="x", pady=(0, 12))
        pasos = (
            ("1", "Asignar mesa", "Cliente + mesa libre"),
            ("2", "Tomar pedido", "Agregar productos"),
            ("3", "Confirmar", "Descuenta inventario"),
            ("4", "Cobrar en caja", "Libera la mesa"),
        )
        for indice, (numero, titulo, detalle) in enumerate(pasos):
            tarjeta = tk.Frame(
                flujo,
                bg=COLORES["blanco"],
                padx=12,
                pady=10,
                highlightbackground=COLORES["borde"],
                highlightthickness=1,
            )
            tarjeta.grid(row=0, column=indice, sticky="ew", padx=(0, 10))
            flujo.grid_columnconfigure(indice, weight=1)
            tk.Label(tarjeta, text=numero, bg=COLORES["terracota"], fg="white", width=3, font=("Segoe UI", 10, "bold")).pack(anchor="w")
            tk.Label(tarjeta, text=titulo, bg=COLORES["blanco"], fg=COLORES["verde"], font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(6, 0))
            tk.Label(tarjeta, text=detalle, bg=COLORES["blanco"], fg=COLORES["carbon"], font=("Segoe UI", 8)).pack(anchor="w")

    def mostrar_pedidos(self):
        self.seccion("Pedidos", "1) Seleccione cliente y mesa libre. 2) Abra pedido. 3) Agregue productos. 4) Confirme o cancele si el cliente se retira.")
        area = self.area_scroll(self.contenido)
        self._flujo_pedidos(area)
        cuerpo = tk.Frame(area, bg=COLORES["crema"])
        cuerpo.pack(fill="both", expand=True)
        cuerpo.grid_columnconfigure(1, weight=1)
        cuerpo.grid_rowconfigure(0, weight=1)
        form = self.panel(cuerpo, "Atencion de mesa")
        form.grid(row=0, column=0, sticky="n", padx=(0, 14))
        clientes_todos = self.servicios["clientes"].listar()
        clientes_lista = [c for c in clientes_todos if c.get("activo")]
        mesas_lista = self.servicios["mesas"].listar()
        productos_lista = self.servicios["productos"].listar(incluir_inactivos=False)
        clientes = {f"{c.get('identificacion') or 'CF'} - {c['nombres']} {c.get('apellidos') or ''}".strip(): c["id"] for c in clientes_lista}
        mesas = {f"Mesa {m['numero']} ({m['estado']})": m["id"] for m in mesas_lista if m["estado"] == "LIBRE" or m["id"] == self.ids.get("mesa_preseleccionada")}
        productos = {f"{p['codigo']} - {p['nombre']} (${Decimal(str(p['precio'])):.2f})": p["id"] for p in productos_lista}
        self.cache["clientes_options"] = clientes
        self.cache["mesas_options"] = mesas
        self.cache["productos_options"] = productos
        self.cache["clientes_por_id"] = {c["id"]: c for c in clientes_todos}
        self.cache["mesas_por_id"] = {m["id"]: m for m in mesas_lista}
        self.cache["productos_por_id"] = {p["id"]: p for p in productos_lista}
        self.combo(form, "Cliente", 0, "cliente_combo", clientes.keys())
        self.combo(form, "Mesa libre", 1, "mesa_combo", mesas.keys())
        self._preseleccionar_mesa_pedido()
        self.campo(form, "Observaciones", 2, "observaciones")
        self._boton(form, "Abrir pedido", self.abrir_pedido, "Accion.TButton", ("add.png",)).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 10))
        self.combo(form, "Producto", 4, "producto_combo", productos.keys())
        self.campo(form, "Cantidad", 5, "cantidad")
        self.campo(form, "Obs. item", 6, "obs_item")
        self.widgets["btn_agregar_pedido"] = self._boton(form, "Agregar producto", self.agregar_producto_pedido, "Accion.TButton", ("add.png",))
        self.widgets["btn_agregar_pedido"].grid(row=7, column=0, columnspan=2, sticky="ew", pady=(12, 6))
        self.widgets["btn_confirmar_pedido"] = self._boton(form, "Confirmar pedido", self.confirmar_pedido, "Secundario.TButton", ("confirmar.png",))
        self.widgets["btn_confirmar_pedido"].grid(row=8, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self.widgets["btn_cancelar_pedido"] = self._boton(form, "Cancelar pedido abierto", self.cancelar_pedido, "Peligro.TButton", ("cancelar.png",))
        self.widgets["btn_cancelar_pedido"].grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self.widgets["btn_comanda_pedido"] = self._boton(form, "Generar comanda PDF", self.generar_comanda, "Secundario.TButton", ("pdf.png",))
        self.widgets["btn_comanda_pedido"].grid(row=10, column=0, columnspan=2, sticky="ew")
        self._actualizar_acciones_pedido(None)

        resumen = tk.Frame(form, bg="#EEF4EF", padx=10, pady=9, highlightbackground=COLORES["borde"], highlightthickness=1)
        resumen.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        self.widgets["pedido_resumen"] = tk.Label(
            resumen,
            text="Seleccione o abra un pedido para ver mesa, cliente y total.",
            bg="#EEF4EF",
            fg=COLORES["texto"],
            justify="left",
            wraplength=230,
            font=("Segoe UI", 9),
        )
        self.widgets["pedido_resumen"].pack(anchor="w", fill="x")

        lista = self.panel(cuerpo, "Pedidos")
        lista.grid(row=0, column=1, sticky="nsew")
        tree = self.tabla(
            lista,
            ("numero", "mesa", "cliente", "estado", "total", "fecha"),
            ("Pedido", "Mesa", "Cliente", "Estado", "Total", "Fecha"),
            "tabla_pedidos",
        )
        tree.bind("<<TreeviewSelect>>", self.seleccionar_pedido)
        detalle = self.panel(area, "Detalle del pedido seleccionado")
        detalle.pack(fill="both", expand=True, pady=(12, 0))
        tdet = self.tabla(detalle, ("producto", "cantidad", "precio", "subtotal", "obs"), ("Producto", "Cant.", "P. unit.", "Subtotal", "Obs."), "tabla_detalle")
        tdet.bind("<Delete>", lambda _e: self.eliminar_item_pedido())
        self.refrescar_pedidos()
        if "pedido" in self.ids:
            self.seleccionar_pedido_por_id(self.ids["pedido"])

    def refrescar_pedidos(self):
        tree = self.widgets.get("tabla_pedidos")
        if not tree:
            return
        self._limpiar_tabla(tree)
        datos = self.servicios["pedidos"].listar()
        self.cache["pedidos"] = datos
        for p in datos:
            mesa = self.cache.get("mesas_por_id", {}).get(p.get("mesa_id"), {})
            cliente = self.cache.get("clientes_por_id", {}).get(p.get("cliente_id"), {})
            tree.insert(
                "",
                tk.END,
                iid=p["id"],
                values=(
                    p["numero_pedido"],
                    f"Mesa {mesa.get('numero', '')}",
                    self._nombre_cliente(cliente),
                    p["estado"],
                    f"${Decimal(str(p['total'])):.2f}",
                    p["fecha_apertura"],
                ),
            )

    def _preseleccionar_mesa_pedido(self):
        mesa_id = self.ids.get("mesa_preseleccionada")
        if not mesa_id:
            return
        opcion = next((texto for texto, valor in self.cache.get("mesas_options", {}).items() if valor == mesa_id), "")
        if opcion:
            self._set_entry("mesa_combo", opcion)

    def abrir_pedido(self):
        try:
            pedido = self.servicios["pedidos"].crear(
                self.cache["clientes_options"].get(self._entry("cliente_combo"), ""),
                self.cache["mesas_options"].get(self._entry("mesa_combo"), ""),
                self.perfil.id,
                self._entry("observaciones"),
            )
            self.ids["pedido"] = pedido["id"]
            self.mostrar_pedidos()
            self._mensaje(f"Pedido {pedido['numero_pedido']} abierto.")
        except AppError as error:
            self.manejar_error("Pedidos", error)

    def seleccionar_pedido(self, _event=None):
        tree = self.widgets["tabla_pedidos"]
        sel = tree.selection()
        if not sel:
            return
        self.ids["pedido"] = sel[0]
        pedido = next((p for p in self.cache.get("pedidos", []) if p["id"] == self.ids["pedido"]), None)
        if pedido:
            self.ids["mesa_preseleccionada"] = pedido.get("mesa_id", "")
            self.actualizar_resumen_pedido(pedido)
        self.refrescar_detalle_pedido()

    def seleccionar_pedido_por_id(self, pedido_id: str):
        tree = self.widgets.get("tabla_pedidos")
        if not tree or not tree.exists(pedido_id):
            return
        tree.selection_set(pedido_id)
        tree.focus(pedido_id)
        tree.see(pedido_id)
        self.ids["pedido"] = pedido_id
        self.seleccionar_pedido()

    def actualizar_resumen_pedido(self, pedido: dict):
        resumen = self.widgets.get("pedido_resumen")
        if not resumen:
            return
        mesa = self.cache.get("mesas_por_id", {}).get(pedido.get("mesa_id"), {})
        cliente = self.cache.get("clientes_por_id", {}).get(pedido.get("cliente_id"), {})
        texto = (
            f"Pedido: {pedido.get('numero_pedido', '')}\n"
            f"Mesa: {mesa.get('numero', '')} | Estado: {pedido.get('estado', '')}\n"
            f"Cliente: {self._nombre_cliente(cliente)}\n"
            f"Total actual: ${Decimal(str(pedido.get('total', 0))):.2f}"
        )
        resumen.config(text=texto)
        self._actualizar_acciones_pedido(pedido.get("estado", ""))

    def _actualizar_acciones_pedido(self, estado: str | None):
        abierto = estado == "ABIERTO"
        seleccionado = bool(estado)
        reglas = {
            "btn_agregar_pedido": abierto,
            "btn_confirmar_pedido": abierto,
            "btn_cancelar_pedido": abierto,
            "btn_comanda_pedido": seleccionado and estado != "CANCELADO",
        }
        for clave, habilitado in reglas.items():
            boton = self.widgets.get(clave)
            if boton:
                boton.configure(state="normal" if habilitado else "disabled")

    def refrescar_detalle_pedido(self):
        tree = self.widgets.get("tabla_detalle")
        if not tree or "pedido" not in self.ids:
            return
        self._limpiar_tabla(tree)
        detalle = self.servicios["pedidos"].detalle(self.ids["pedido"])
        productos = {p["id"]: p for p in self.servicios["productos"].listar(incluir_inactivos=True)}
        self.cache["detalle"] = detalle
        self.cache["productos_por_id"] = productos
        for d in detalle:
            prod = productos.get(d["producto_id"], {})
            tree.insert("", tk.END, iid=d["id"], values=(prod.get("nombre", ""), d["cantidad"], f"${Decimal(str(d['precio_unitario'])):.2f}", f"${Decimal(str(d['subtotal'])):.2f}", d.get("observaciones") or ""))

    def agregar_producto_pedido(self):
        try:
            if "pedido" not in self.ids:
                raise AppError("Seleccione o abra un pedido.")
            producto_id = self.cache["productos_options"].get(self._entry("producto_combo"), "")
            self.servicios["pedidos"].agregar_detalle(self.ids["pedido"], producto_id, int(self._entry("cantidad")), self._entry("obs_item"))
            self.refrescar_pedidos()
            self.refrescar_detalle_pedido()
        except (ValueError, AppError) as error:
            self.manejar_error("Pedidos", error)

    def eliminar_item_pedido(self):
        tree = self.widgets.get("tabla_detalle")
        if not tree or not tree.selection():
            return
        if not messagebox.askyesno("Pedidos", "Eliminar item seleccionado?"):
            return
        try:
            self.servicios["pedidos"].eliminar_detalle(tree.selection()[0])
            self.refrescar_detalle_pedido()
            self.refrescar_pedidos()
        except AppError as error:
            self.manejar_error("Pedidos", error)

    def confirmar_pedido(self):
        try:
            if "pedido" not in self.ids:
                raise AppError("Seleccione un pedido.")
            self.servicios["pedidos"].confirmar(self.ids["pedido"])
            self.mostrar_pedidos()
            self._mensaje("Pedido confirmado. Inventario actualizado por RPC.")
        except AppError as error:
            self.manejar_error("Pedidos", error)

    def cancelar_pedido(self):
        try:
            if "pedido" not in self.ids:
                raise AppError("Seleccione un pedido abierto.")
            pedido = self.servicios["pedidos"].obtener(self.ids["pedido"])
            if not pedido:
                raise AppError("Seleccione un pedido valido.")
            confirmar = messagebox.askyesno(
                "Cancelar pedido",
                f"Cancelar {pedido.get('numero_pedido', '')}?\n\nLa mesa quedara libre si el pedido esta ABIERTO.",
            )
            if not confirmar:
                return
            self.servicios["pedidos"].cancelar(self.ids["pedido"])
            self.ids.pop("pedido", None)
            self.ids.pop("mesa_preseleccionada", None)
            self.mostrar_pedidos()
            self._mensaje("Pedido cancelado. La mesa fue liberada por la base.")
        except AppError as error:
            self.manejar_error("Pedidos", error)

    def generar_comanda(self):
        try:
            if "pedido" not in self.ids:
                raise AppError("Seleccione un pedido.")
            pedido = self.servicios["pedidos"].obtener(self.ids["pedido"])
            detalle = self.servicios["pedidos"].detalle(self.ids["pedido"])
            productos = {p["id"]: p for p in self.servicios["productos"].listar(incluir_inactivos=True)}
            clientes = {c["id"]: c for c in self.servicios["clientes"].listar()}
            mesas = {m["id"]: m for m in self.servicios["mesas"].listar(False)}
            ruta = self.reportes.generar_comanda(pedido, detalle, productos, clientes.get(pedido["cliente_id"]), mesas.get(pedido["mesa_id"]))
            messagebox.showinfo("PDF", f"Comanda generada:\n{ruta}")
        except (AppError, OSError) as error:
            self.manejar_error("PDF", error)

    # Caja
    def mostrar_caja(self):
        self.seccion("Caja", "Seleccione un pedido confirmado, verifique mesa/cliente y registre el pago.")
        cuerpo = tk.Frame(self.contenido, bg=COLORES["crema"])
        cuerpo.pack(fill="both", expand=True)
        cuerpo.grid_columnconfigure(0, weight=1)
        lista = self.panel(cuerpo, "Pedidos por cobrar")
        lista.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        tree = self.tabla(
            lista,
            ("numero", "mesa", "cliente", "total", "fecha"),
            ("Pedido", "Mesa", "Cliente", "Total", "Fecha"),
            "tabla_caja",
        )
        tree.bind("<<TreeviewSelect>>", self.seleccionar_pedido_caja)
        form = self.panel(cuerpo, "Registrar pago")
        form.grid(row=0, column=1, sticky="n")
        resumen = tk.Frame(form, bg="#EEF4EF", padx=10, pady=9, highlightbackground=COLORES["borde"], highlightthickness=1)
        resumen.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        self.widgets["caja_resumen"] = tk.Label(
            resumen,
            text="Seleccione un pedido para cobrar.",
            bg="#EEF4EF",
            fg=COLORES["texto"],
            justify="left",
            wraplength=230,
            font=("Segoe UI", 9),
        )
        self.widgets["caja_resumen"].pack(anchor="w", fill="x")
        self.combo(form, "Metodo", 1, "metodo", ("EFECTIVO", "TARJETA", "TRANSFERENCIA"))
        self.campo(form, "Monto", 2, "monto")
        self.campo(form, "Referencia", 3, "referencia")
        self._boton(form, "Registrar pago", self.registrar_pago, "Accion.TButton", ("cobrar.png",)).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 6))
        self._boton(form, "Generar comprobante", self.generar_comprobante, "Secundario.TButton", ("pdf.png",)).grid(row=5, column=0, columnspan=2, sticky="ew")
        self.refrescar_caja()

    def refrescar_caja(self):
        tree = self.widgets.get("tabla_caja")
        if not tree:
            return
        self._limpiar_tabla(tree)
        clientes = {c["id"]: c for c in self.servicios["clientes"].listar()}
        mesas = {m["id"]: m for m in self.servicios["mesas"].listar(False)}
        self.cache["clientes_caja"] = clientes
        self.cache["mesas_caja"] = mesas
        pedidos = self.servicios["pedidos"].listar("CONFIRMADO")
        self.cache["caja"] = pedidos
        for p in pedidos:
            mesa = mesas.get(p.get("mesa_id"), {})
            cliente = clientes.get(p.get("cliente_id"), {})
            tree.insert(
                "",
                tk.END,
                iid=p["id"],
                values=(
                    p["numero_pedido"],
                    f"Mesa {mesa.get('numero', '')}",
                    self._nombre_cliente(cliente),
                    f"${Decimal(str(p['total'])):.2f}",
                    p["fecha_apertura"],
                ),
            )

    def seleccionar_pedido_caja(self, _event=None):
        tree = self.widgets["tabla_caja"]
        if tree.selection():
            self.ids["pedido_caja"] = tree.selection()[0]
            pedido = next((p for p in self.cache.get("caja", []) if p["id"] == self.ids["pedido_caja"]), None)
            if pedido:
                self._set_entry("monto", pedido.get("total"))
                mesa = self.cache.get("mesas_caja", {}).get(pedido.get("mesa_id"), {})
                cliente = self.cache.get("clientes_caja", {}).get(pedido.get("cliente_id"), {})
                resumen = self.widgets.get("caja_resumen")
                if resumen:
                    resumen.config(
                        text=(
                            f"Pedido: {pedido.get('numero_pedido', '')}\n"
                            f"Mesa: {mesa.get('numero', '')}\n"
                            f"Cliente: {self._nombre_cliente(cliente)}\n"
                            f"Total a cobrar: ${Decimal(str(pedido.get('total', 0))):.2f}"
                        )
                    )

    def registrar_pago(self):
        try:
            if "pedido_caja" not in self.ids:
                raise AppError("Seleccione un pedido confirmado.")
            self.servicios["pagos"].registrar_pago(self.ids["pedido_caja"], self._entry("metodo"), Decimal(self._entry("monto")), self._entry("referencia"))
            self.ids["ultimo_pagado"] = self.ids["pedido_caja"]
            self.ids.pop("pedido_caja", None)
            self.refrescar_caja()
            self._mensaje("Pago registrado. Pedido pagado y mesa liberada por la base.")
        except (ValueError, AppError) as error:
            self.manejar_error("Caja", error)

    def generar_comprobante(self):
        try:
            pedido_id = self.ids.get("pedido_caja") or self.ids.get("ultimo_pagado")
            if not pedido_id:
                raise AppError("Seleccione un pedido.")
            pedido = self.servicios["pedidos"].obtener(pedido_id)
            detalle = self.servicios["pedidos"].detalle(pedido_id)
            productos = {p["id"]: p for p in self.servicios["productos"].listar(incluir_inactivos=True)}
            clientes = {c["id"]: c for c in self.servicios["clientes"].listar()}
            mesas = {m["id"]: m for m in self.servicios["mesas"].listar(False)}
            pagos = [p for p in self.servicios["pagos"].listar() if p["pedido_id"] == pedido_id]
            ruta = self.reportes.generar_comprobante(pedido, detalle, productos, clientes.get(pedido["cliente_id"]), mesas.get(pedido["mesa_id"]), pagos[0] if pagos else None)
            messagebox.showinfo("PDF", f"Comprobante generado:\n{ruta}")
        except (AppError, OSError) as error:
            self.manejar_error("PDF", error)

    # Empleados y reportes
    def mostrar_empleados(self):
        self.seccion("Empleados", "Registre empleados y cree su cuenta de acceso desde este panel administrativo.")
        cuerpo = tk.Frame(self.contenido, bg=COLORES["crema"])
        cuerpo.pack(fill="both", expand=True)
        cuerpo.grid_columnconfigure(1, weight=1)
        form = self.panel(cuerpo, "Empleado y acceso")
        form.grid(row=0, column=0, sticky="n", padx=(0, 14))

        nota = tk.Label(
            form,
            text=(
                "Cree aqui la cuenta del empleado con correo y contrasena temporal. "
                "La fecha se completa con la fecha actual del sistema."
            ),
            bg="#EEF4EF",
            fg=COLORES["texto"],
            justify="left",
            wraplength=265,
            padx=10,
            pady=8,
            font=("Segoe UI", 8),
        )
        nota.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        for i, clave in enumerate(("cedula", "nombres", "apellidos", "telefono", "fecha_contratacion"), start=1):
            self.campo(form, clave.replace("_", " ").title(), i, clave)
        self.combo(form, "Cargo", 6, "cargo", ("ADMINISTRADOR", "MESERO", "CAJERO"))
        self.campo(form, "Correo acceso", 7, "correo_acceso", 30)
        tk.Label(form, text="Contrasena", bg=COLORES["blanco"], fg=COLORES["texto"], font=("Segoe UI", 9, "bold")).grid(row=8, column=0, sticky="w", pady=(0, 7), padx=(0, 8))
        contrasena = tk.Entry(form, width=30, font=("Segoe UI", 9), show="*")
        contrasena.grid(row=8, column=1, sticky="ew", pady=(0, 7))
        self.widgets["contrasena_acceso"] = contrasena
        activo = tk.BooleanVar(value=True)
        self.widgets["activo_var"] = activo
        tk.Checkbutton(form, text="Activo", variable=activo, bg=COLORES["blanco"]).grid(row=9, column=1, sticky="w")
        self._boton(form, "Guardar empleado", self.guardar_empleado, "Accion.TButton", ("guardar.png",)).grid(row=10, column=0, columnspan=2, sticky="ew", pady=(12, 6))
        self._boton(form, "Limpiar", self.limpiar_formulario_empleado, "Secundario.TButton", ("clean.png",)).grid(row=11, column=0, columnspan=2, sticky="ew")
        self._set_entry("fecha_contratacion", date.today().isoformat())
        self._set_entry("cargo", "MESERO")
        lista = self.panel(cuerpo, "Empleados")
        lista.grid(row=0, column=1, sticky="nsew")
        tree = self.tabla(
            lista,
            ("cedula", "nombre", "cargo", "acceso", "estado"),
            ("Cedula", "Empleado", "Cargo", "Acceso", "Estado"),
            "tabla_empleados",
        )
        tree.bind("<<TreeviewSelect>>", self.seleccionar_empleado)
        self.refrescar_empleados()

    def refrescar_empleados(self):
        tree = self.widgets.get("tabla_empleados")
        if not tree:
            return
        self._limpiar_tabla(tree)
        datos = self.servicios["empleados"].listar()
        perfiles = {p["id"]: p for p in self.servicios["empleados"].listar_perfiles()}
        self.cache["perfiles_empleados"] = perfiles
        self.cache["empleados"] = datos
        for e in datos:
            perfil = perfiles.get(e.get("perfil_id") or "")
            acceso = "Vinculado" if perfil else "Sin cuenta"
            if perfil and not perfil.get("activo"):
                acceso = "Perfil inactivo"
            tree.insert(
                "",
                tk.END,
                iid=e["id"],
                values=(
                    e["cedula"],
                    f"{e['nombres']} {e['apellidos']}",
                    e["cargo"],
                    acceso,
                    "Activo" if e["activo"] else "Inactivo",
                ),
            )

    def seleccionar_empleado(self, _event=None):
        tree = self.widgets["tabla_empleados"]
        if not tree.selection():
            return
        emp = next((e for e in self.cache.get("empleados", []) if e["id"] == tree.selection()[0]), None)
        if not emp:
            return
        self.ids["empleado"] = emp["id"]
        for clave in ("cedula", "nombres", "apellidos", "telefono", "fecha_contratacion", "cargo"):
            self._set_entry(clave, emp.get(clave))
        self._set_entry("correo_acceso", "")
        self._set_entry("contrasena_acceso", "")
        self.widgets["activo_var"].set(bool(emp.get("activo")))

    def guardar_empleado(self):
        try:
            datos = {k: self._entry(k) for k in ("cedula", "nombres", "apellidos", "telefono", "fecha_contratacion", "cargo")}
            datos["activo"] = self.widgets["activo_var"].get()
            empleado_actual = next((e for e in self.cache.get("empleados", []) if e["id"] == self.ids.get("empleado")), None)
            perfil_id = empleado_actual.get("perfil_id") if empleado_actual else ""
            if not perfil_id and (not self._entry("correo_acceso") or not self._entry("contrasena_acceso")):
                raise AppError("Ingrese correo y contrasena para crear la cuenta de acceso del empleado.")
            if not perfil_id:
                perfil_id = self.servicios["empleados"].crear_cuenta_acceso(
                    self._entry("correo_acceso"),
                    self._entry("contrasena_acceso"),
                )
            datos["perfil_id"] = perfil_id
            if perfil_id:
                self.servicios["empleados"].guardar_perfil_empleado(
                    perfil_id,
                    datos["nombres"],
                    datos["apellidos"],
                    datos["cargo"],
                    datos["activo"],
                )
            self.servicios["empleados"].guardar(datos, self.ids.get("empleado"))
            self.refrescar_empleados()
            self.limpiar_formulario_empleado()
            self._mensaje("Empleado guardado. La cuenta de acceso quedo vinculada cuando se ingreso correo y contrasena.")
        except AppError as error:
            self.manejar_error("Empleados", error)

    def limpiar_formulario_empleado(self):
        for clave in ("cedula", "nombres", "apellidos", "telefono", "fecha_contratacion", "cargo", "correo_acceso", "contrasena_acceso"):
            self._set_entry(clave, "")
        self._set_entry("fecha_contratacion", date.today().isoformat())
        self._set_entry("cargo", "MESERO")
        self.widgets["activo_var"].set(True)
        self.ids.pop("empleado", None)
        tabla = self.widgets.get("tabla_empleados")
        if tabla:
            for item in tabla.selection():
                tabla.selection_remove(item)

    def mostrar_reportes(self):
        self.seccion("Reportes", "Generacion de reporte academico de ventas.")
        self._boton(self.contenido, "Generar reporte de ventas PDF", self.generar_reporte_ventas, "Accion.TButton", ("pdf.png",)).pack(anchor="w", pady=(0, 12))
        lista = self.panel(self.contenido, "Pagos registrados")
        lista.pack(fill="both", expand=True)
        tree = self.tabla(lista, ("pedido", "metodo", "monto", "fecha"), ("Pedido", "Metodo", "Monto", "Fecha"), "tabla_reportes")
        pagos = self.servicios["pagos"].listar()
        pedidos = {p["id"]: p for p in self.servicios["pedidos"].listar()}
        self.cache["pagos"] = pagos
        self.cache["pedidos_por_id"] = pedidos
        for pago in pagos:
            pedido = pedidos.get(pago["pedido_id"], {})
            tree.insert("", tk.END, values=(pedido.get("numero_pedido", ""), pago["metodo_pago"], f"${Decimal(str(pago['monto'])):.2f}", pago["created_at"]))

    def generar_reporte_ventas(self):
        try:
            ruta = self.reportes.generar_reporte_ventas(self.cache.get("pagos", []), self.cache.get("pedidos_por_id", {}))
            messagebox.showinfo("PDF", f"Reporte generado:\n{ruta}")
        except OSError as error:
            self.manejar_error("Reportes", error)

    def cerrar_sesion(self):
        if messagebox.askyesno("Sesion", "Cerrar sesion?"):
            self.servicios["auth"].cerrar_sesion()
            self.al_cerrar_sesion()
