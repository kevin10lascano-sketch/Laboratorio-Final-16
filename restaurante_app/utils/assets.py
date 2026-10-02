from pathlib import Path
import tkinter as tk

from config.settings import ASSETS_DIR


class AssetManager:
    def __init__(self) -> None:
        self._cache: dict[str, tk.PhotoImage] = {}

    def icono(self, nombre_archivo: str, alternativas: tuple[str, ...] = ()) -> tk.PhotoImage | None:
        for nombre in (nombre_archivo, *alternativas):
            ruta = ASSETS_DIR / "icons" / nombre
            imagen = self._cargar(ruta)
            if imagen is not None:
                return imagen
        return None

    def logo(self, nombre_archivo: str = "logo.png") -> tk.PhotoImage | None:
        ruta = ASSETS_DIR / "logo" / nombre_archivo
        return self._cargar(ruta)

    def _cargar(self, ruta: Path) -> tk.PhotoImage | None:
        clave = str(ruta)
        if clave in self._cache:
            return self._cache[clave]
        if not ruta.exists():
            return None
        try:
            imagen = tk.PhotoImage(file=str(ruta))
        except tk.TclError:
            return None
        self._cache[clave] = imagen
        return imagen
