from datetime import datetime
from decimal import Decimal
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config.settings import ASSETS_DIR, REPORTES_DIR


class ReportePDFServicio:
    verde = colors.HexColor("#24352B")
    terracota = colors.HexColor("#C66A3D")
    crema = colors.HexColor("#F5F1E8")
    carbon = colors.HexColor("#343A40")
    borde = colors.HexColor("#D9D4C8")

    def __init__(self) -> None:
        REPORTES_DIR.mkdir(exist_ok=True)
        self.estilos = getSampleStyleSheet()
        self.logo_path = ASSETS_DIR / "logo" / "logo.png"
        self._configurar_estilos()

    def _configurar_estilos(self) -> None:
        self.estilos.add(ParagraphStyle(name="Marca", parent=self.estilos["Normal"], fontName="Helvetica-Bold", fontSize=16, leading=18, textColor=self.verde))
        self.estilos.add(ParagraphStyle(name="TituloDocumento", parent=self.estilos["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=self.verde, spaceAfter=6))
        self.estilos.add(ParagraphStyle(name="SubtituloDocumento", parent=self.estilos["Normal"], fontSize=9, leading=12, textColor=self.carbon))
        self.estilos.add(ParagraphStyle(name="TituloCabecera", parent=self.estilos["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=colors.white, spaceAfter=6))
        self.estilos.add(ParagraphStyle(name="SubtituloCabecera", parent=self.estilos["Normal"], fontSize=9, leading=12, textColor=self.crema))
        self.estilos.add(ParagraphStyle(name="Etiqueta", parent=self.estilos["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=self.verde))
        self.estilos.add(ParagraphStyle(name="Valor", parent=self.estilos["Normal"], fontSize=9, leading=11, textColor=self.carbon))
        self.estilos.add(ParagraphStyle(name="Total", parent=self.estilos["Normal"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=self.verde, alignment=2))
        self.estilos.add(ParagraphStyle(name="Nota", parent=self.estilos["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#5A625B")))

    def _ruta_unica(self, nombre: str) -> Path:
        ruta = REPORTES_DIR / nombre
        if not ruta.exists():
            return ruta
        base = ruta.stem
        sufijo = ruta.suffix
        contador = 2
        while True:
            candidata = REPORTES_DIR / f"{base}_{contador}{sufijo}"
            if not candidata.exists():
                return candidata
            contador += 1

    def _documento(self, ruta: Path):
        return SimpleDocTemplate(
            str(ruta),
            pagesize=letter,
            rightMargin=0.55 * inch,
            leftMargin=0.55 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.55 * inch,
        )

    def _pie_pagina(self, canvas, doc) -> None:
        canvas.saveState()
        canvas.setStrokeColor(self.borde)
        canvas.line(doc.leftMargin, 0.42 * inch, letter[0] - doc.rightMargin, 0.42 * inch)
        canvas.setFillColor(colors.HexColor("#667066"))
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(doc.leftMargin, 0.27 * inch, "RestauranteApp - Documento interno academico")
        canvas.drawRightString(letter[0] - doc.rightMargin, 0.27 * inch, f"Pagina {doc.page}")
        canvas.restoreState()

    def _logo(self, max_width: float = 1.45 * inch, max_height: float = 0.58 * inch):
        if not self.logo_path.exists():
            return Paragraph("<b>RestauranteApp</b>", self.estilos["Marca"])
        try:
            ancho, alto = ImageReader(str(self.logo_path)).getSize()
            escala = min(max_width / ancho, max_height / alto)
            imagen = Image(str(self.logo_path), width=ancho * escala, height=alto * escala)
            imagen.hAlign = "LEFT"
            return imagen
        except Exception:
            return Paragraph("<b>RestauranteApp</b>", self.estilos["Marca"])

    def _encabezado(self, titulo: str, subtitulo: str):
        bloque_titulo = [
            Paragraph(self._texto(titulo), self.estilos["TituloCabecera"]),
            Paragraph(self._texto(subtitulo), self.estilos["SubtituloCabecera"]),
        ]
        tabla = Table([[self._logo(), bloque_titulo]], colWidths=[1.75 * inch, 5.0 * inch])
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.verde),
            ("BOX", (0, 0), (-1, -1), 0.6, self.borde),
            ("LINEBELOW", (0, 0), (-1, -1), 2, self.terracota),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
        return tabla

    def _meta_table(self, pares: list[tuple[str, str]]):
        filas = [
            [Paragraph(self._texto(etiqueta), self.estilos["Etiqueta"]), Paragraph(self._texto(valor), self.estilos["Valor"])]
            for etiqueta, valor in pares
        ]
        tabla = Table(filas, colWidths=[1.35 * inch, 5.4 * inch])
        tabla.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, self.borde),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, self.borde),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF4EF")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return tabla

    def generar_comanda(self, pedido: dict, detalle: list[dict], productos: dict[str, dict], cliente: dict | None, mesa: dict | None) -> Path:
        numero = pedido.get("numero_pedido", "pedido")
        ruta = self._ruta_unica(f"pedido_{numero}.pdf")
        doc = self._documento(ruta)
        elementos = [
            self._encabezado(f"Comanda {numero}", "Orden interna para preparacion y control de mesa"),
            Spacer(1, 14),
            self._meta_table([
                ("Fecha", self._fecha(pedido.get("fecha_apertura", ""))),
                ("Mesa", f"Mesa {mesa.get('numero') if mesa else ''}"),
                ("Cliente", self._nombre_cliente(cliente)),
                ("Estado", pedido.get("estado", "")),
                ("Observaciones", pedido.get("observaciones") or "Sin observaciones"),
            ]),
            Spacer(1, 14),
            Paragraph("Detalle del pedido", self.estilos["Etiqueta"]),
            Spacer(1, 6),
            self._tabla_detalle(detalle, productos),
            Spacer(1, 12),
            self._total_box("Total provisional", pedido.get("total", 0)),
        ]
        doc.build(elementos, onFirstPage=self._pie_pagina, onLaterPages=self._pie_pagina)
        return ruta

    def generar_comprobante(self, pedido: dict, detalle: list[dict], productos: dict[str, dict], cliente: dict | None, mesa: dict | None, pago: dict | None) -> Path:
        numero = pedido.get("numero_pedido", "pedido")
        ruta = self._ruta_unica(f"comprobante_{numero}.pdf")
        doc = self._documento(ruta)
        elementos = [
            self._encabezado(f"Comprobante de venta {numero}", "Comprobante interno academico - no valido como factura electronica SRI"),
            Spacer(1, 14),
            self._meta_table([
                ("Fecha de pago", self._fecha(pago.get("created_at", "") if pago else datetime.now().isoformat(timespec="seconds"))),
                ("Cliente", self._nombre_cliente(cliente)),
                ("Mesa", f"Mesa {mesa.get('numero') if mesa else ''}"),
                ("Metodo de pago", pago.get("metodo_pago", "Pendiente") if pago else "Pendiente"),
                ("Referencia", pago.get("referencia") or "N/A" if pago else "N/A"),
            ]),
            Spacer(1, 14),
            Paragraph("Detalle de consumo", self.estilos["Etiqueta"]),
            Spacer(1, 6),
            self._tabla_detalle(detalle, productos),
            Spacer(1, 12),
            self._resumen_montos(pedido),
            Spacer(1, 14),
            Paragraph("Gracias por su visita. Este documento resume la operacion registrada en el sistema academico.", self.estilos["Nota"]),
        ]
        doc.build(elementos, onFirstPage=self._pie_pagina, onLaterPages=self._pie_pagina)
        return ruta

    def generar_reporte_ventas(self, pagos: list[dict], pedidos: dict[str, dict]) -> Path:
        fecha = datetime.now().date().isoformat()
        ruta = self._ruta_unica(f"ventas_{fecha}.pdf")
        doc = self._documento(ruta)
        total = sum(Decimal(str(p.get("monto", 0))) for p in pagos)
        metodos = self._totalizar_metodos(pagos)
        elementos = [
            self._encabezado(f"Reporte de ventas {fecha}", "Resumen de pagos registrados y pedidos cobrados"),
            Spacer(1, 14),
            self._indicadores([
                ("Pagos registrados", str(len(pagos))),
                ("Total vendido", f"${total:.2f}"),
                ("Metodos usados", str(len(metodos))),
            ]),
            Spacer(1, 14),
            Paragraph("Ventas registradas", self.estilos["Etiqueta"]),
            Spacer(1, 6),
            self._tabla_ventas(pagos, pedidos),
            Spacer(1, 14),
            Paragraph("Totales por metodo de pago", self.estilos["Etiqueta"]),
            Spacer(1, 6),
            self._tabla_metodos(metodos),
        ]
        doc.build(elementos, onFirstPage=self._pie_pagina, onLaterPages=self._pie_pagina)
        return ruta

    def _tabla_detalle(self, detalle: list[dict], productos: dict[str, dict]) -> Table:
        filas = [["Producto", "Cant.", "P. unit.", "Subtotal", "Obs."]]
        for item in detalle:
            producto = productos.get(item.get("producto_id", ""), {})
            filas.append([
                Paragraph(self._texto(producto.get("nombre", item.get("producto_id", ""))), self.estilos["Valor"]),
                item.get("cantidad", 0),
                f"${Decimal(str(item.get('precio_unitario', 0))):.2f}",
                f"${Decimal(str(item.get('subtotal', 0))):.2f}",
                Paragraph(self._texto(item.get("observaciones") or ""), self.estilos["Valor"]),
            ])
        return self._tabla(filas, col_widths=[2.45 * inch, 0.65 * inch, 0.9 * inch, 0.95 * inch, 1.8 * inch])

    def _tabla_ventas(self, pagos: list[dict], pedidos: dict[str, dict]) -> Table:
        filas = [["Pedido", "Metodo", "Monto", "Fecha"]]
        for pago in pagos:
            pedido = pedidos.get(pago.get("pedido_id", ""), {})
            filas.append([
                pedido.get("numero_pedido", ""),
                pago.get("metodo_pago", ""),
                f"${Decimal(str(pago.get('monto', 0))):.2f}",
                self._fecha(pago.get("created_at", "")),
            ])
        return self._tabla(filas, col_widths=[1.45 * inch, 1.35 * inch, 1.1 * inch, 2.85 * inch])

    def _tabla_metodos(self, metodos: dict[str, Decimal]) -> Table:
        filas = [["Metodo de pago", "Total"]]
        for metodo, total in sorted(metodos.items()):
            filas.append([metodo, f"${total:.2f}"])
        if len(filas) == 1:
            filas.append(["Sin pagos", "$0.00"])
        return self._tabla(filas, col_widths=[4.9 * inch, 1.85 * inch])

    def _tabla(self, filas: list[list], col_widths: list[float] | None = None) -> Table:
        tabla = Table(filas, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.verde),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.35, self.borde),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8.5),
            ("FONTSIZE", (0, 1), (-1, -1), 8.5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 1), (3, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.crema]),
        ]))
        return tabla

    def _total_box(self, etiqueta: str, valor) -> Table:
        tabla = Table(
            [[Paragraph(self._texto(etiqueta), self.estilos["Etiqueta"]), Paragraph(f"${Decimal(str(valor)):.2f}", self.estilos["Total"])]],
            colWidths=[4.65 * inch, 2.1 * inch],
            hAlign="LEFT",
        )
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF4EF")),
            ("BOX", (0, 0), (-1, -1), 0.6, self.terracota),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        return tabla

    def _resumen_montos(self, pedido: dict) -> Table:
        filas = [
            ["Subtotal", f"${Decimal(str(pedido.get('subtotal', 0))):.2f}"],
            ["Impuesto", f"${Decimal(str(pedido.get('impuesto', 0))):.2f}"],
            ["Total", f"${Decimal(str(pedido.get('total', 0))):.2f}"],
        ]
        tabla = Table(filas, colWidths=[4.85 * inch, 1.9 * inch], hAlign="LEFT")
        tabla.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.6, self.borde),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, self.borde),
            ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#EEF4EF")),
            ("TEXTCOLOR", (0, 2), (-1, 2), self.verde),
            ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        return tabla

    def _indicadores(self, valores: list[tuple[str, str]]) -> Table:
        fila = [
            [Paragraph(self._texto(etiqueta), self.estilos["Etiqueta"]), Paragraph(self._texto(valor), self.estilos["Total"])]
            for etiqueta, valor in valores
        ]
        tabla = Table([fila], colWidths=[2.17 * inch] * len(fila))
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF4EF")),
            ("BOX", (0, 0), (-1, -1), 0.5, self.borde),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, self.borde),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        return tabla

    def _totalizar_metodos(self, pagos: list[dict]) -> dict[str, Decimal]:
        totales: dict[str, Decimal] = {}
        for pago in pagos:
            metodo = pago.get("metodo_pago", "SIN METODO")
            totales[metodo] = totales.get(metodo, Decimal("0")) + Decimal(str(pago.get("monto", 0)))
        return totales

    def _nombre_cliente(self, cliente: dict | None) -> str:
        if not cliente:
            return "Consumidor Final"
        return f"{cliente.get('nombres', '')} {cliente.get('apellidos') or ''}".strip()

    def _fecha(self, valor: str) -> str:
        if not valor:
            return ""
        return str(valor).replace("T", " ")[:19]

    def _texto(self, valor) -> str:
        return escape(str(valor if valor is not None else ""))
