from pathlib import Path

from dotenv import load_dotenv
import os


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BASE_DIR.parent
ASSETS_DIR = BASE_DIR / "assets"
REPORTES_DIR = PROJECT_DIR / "reportes_generados"

load_dotenv(PROJECT_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()

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
