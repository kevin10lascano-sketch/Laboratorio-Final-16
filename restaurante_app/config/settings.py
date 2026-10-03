import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BASE_DIR.parent


def es_ejecutable() -> bool:
    return bool(getattr(sys, "frozen", False))


def ruta_recursos() -> Path:
    if es_ejecutable():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return BASE_DIR


def ruta_salida_usuario() -> Path:
    if es_ejecutable():
        return Path(sys.executable).resolve().parent
    return PROJECT_DIR


ASSETS_DIR = ruta_recursos() / "assets"
REPORTES_DIR = ruta_salida_usuario() / "reportes_generados"

# Completar con los datos de Supabase antes de ejecutar o generar el .exe.
# La publishable key esta pensada para clientes publicos; nunca usar service_role aqui.
SUPABASE_URL = "https://sukksxlrcpdrchmqprrr.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_HG0NdDtfD6JApCcJMQPKJQ_AMq_k6n7"

APP_NAME = "RestauranteApp"
IMPUESTO_POR_DEFECTO = 0.0

COLORES = {
    "verde": "#24352B",
    "terracota": "#C66A3D",
    "crema": "#F5F1E8",
    "blanco": "#FFFFFF",
    "carbon": "#343A40",
    "texto": "#26302A",
    "borde": "#D9D4C8",
    "exito": "#2E7D32",
    "advertencia": "#B7791F",
    "error": "#B42318",
    "info": "#2563EB",
    "libre": "#DFF3E4",
    "ocupada": "#F8D9CC",
}
