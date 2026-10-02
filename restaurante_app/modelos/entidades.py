from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class Perfil:
    id: str
    nombres: str
    apellidos: str
    rol: str
    activo: bool
    correo: str = ""

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}".strip()


@dataclass
class Empleado:
    id: str
    perfil_id: Optional[str]
    cedula: str
    nombres: str
    apellidos: str
    telefono: str
    cargo: str
    activo: bool
    fecha_contratacion: str


@dataclass
class Cliente:
    id: str
    identificacion: Optional[str]
    nombres: str
    apellidos: Optional[str]
    telefono: Optional[str]
    correo: Optional[str]
    activo: bool
    es_consumidor_final: bool

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos or ''}".strip()


@dataclass
class Mesa:
    id: str
    numero: int
    capacidad: int
    estado: str
    activo: bool


@dataclass
class Categoria:
    id: str
    nombre: str
    descripcion: Optional[str]
    activo: bool


@dataclass
class Producto:
    id: str
    categoria_id: str
    codigo: str
    nombre: str
    descripcion: Optional[str]
    precio: Decimal
    stock: int
    stock_minimo: int
    activo: bool


@dataclass
class Pedido:
    id: str
    numero_pedido: str
    cliente_id: str
    mesa_id: str
    mesero_id: Optional[str]
    estado: str
    subtotal: Decimal
    impuesto: Decimal
    total: Decimal
    observaciones: Optional[str]
    fecha_apertura: str
    fecha_cierre: Optional[str]


@dataclass
class DetallePedido:
    id: str
    pedido_id: str
    producto_id: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    observaciones: Optional[str]


@dataclass
class Pago:
    id: str
    pedido_id: str
    cajero_id: Optional[str]
    metodo_pago: str
    monto: Decimal
    referencia: Optional[str]
    created_at: str


@dataclass
class MovimientoInventario:
    id: str
    producto_id: str
    tipo: str
    cantidad: int
    stock_anterior: int
    stock_nuevo: int
    usuario_id: Optional[str]
    pedido_id: Optional[str]
    observacion: Optional[str]
    created_at: str
