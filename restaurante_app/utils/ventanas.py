import tkinter as tk


def centrar_ventana(ventana: tk.Tk | tk.Toplevel, ancho: int, alto: int) -> None:
    ventana.update_idletasks()
    pantalla_ancho = ventana.winfo_screenwidth()
    pantalla_alto = ventana.winfo_screenheight()
    x = max((pantalla_ancho - ancho) // 2, 0)
    y = max((pantalla_alto - alto) // 2, 0)
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
