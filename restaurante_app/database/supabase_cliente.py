from supabase import Client, create_client

from config.settings import SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL


class ConfiguracionSupabaseError(RuntimeError):
    pass


_cliente: Client | None = None


def obtener_cliente_supabase() -> Client:
    global _cliente

    if not SUPABASE_URL or not SUPABASE_PUBLISHABLE_KEY:
        raise ConfiguracionSupabaseError(
            "Configure SUPABASE_URL y SUPABASE_PUBLISHABLE_KEY en el archivo .env."
        )

    if _cliente is None:
        _cliente = create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)

    return _cliente
