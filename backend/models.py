from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import date

class ItemFactura(BaseModel):
    descripcion: str
    cantidad: float
    precio_unitario: float
    precio_total: float
    
    @field_validator('precio_total')
    def validar_total_item(cls, v, info):
        if 'cantidad' in info.data and 'precio_unitario' in info.data:
            calculado = round(info.data['cantidad'] * info.data['precio_unitario'], 2)
            if abs(calculado - v) > 0.01:
                raise ValueError(f'Total del item no coincide: {calculado} vs {v}')
        return v

class FacturaComercial(BaseModel):
    numero_factura: str
    fecha_expedicion: date
    lugar_expedicion: str
    nombre_vendedor: str
    direccion_vendedor: str
    pais_vendedor: str
    nombre_comprador: str
    direccion_comprador: str
    ciudad_comprador: str
    items: List[ItemFactura]
    precio_neto_factura: float
    moneda: str
    incoterm: str
    lugar_entrega: str
    descuentos: Optional[float] = 0
    concepto_descuento: Optional[str] = None
    gastos_transporte: Optional[float] = 0
    costo_seguro: Optional[float] = 0
    es_original: bool = True
    es_definitiva: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "numero_factura": "INV-2025-001",
                "fecha_expedicion": "2025-11-01",
                "lugar_expedicion": "Shanghai, China",
                "nombre_vendedor": "Supplier Ltd",
                "direccion_vendedor": "123 Business St",
                "pais_vendedor": "China",
                "nombre_comprador": "Importadora Colombia",
                "direccion_comprador": "Calle 100 No 10",
                "ciudad_comprador": "Bogotá",
                "items": [{"descripcion": "Componentes", "cantidad": 100, "precio_unitario": 10.00, "precio_total": 1000.00}],
                "precio_neto_factura": 1000.00,
                "moneda": "USD",
                "incoterm": "FOB",
                "lugar_entrega": "Puerto Shanghai",
                "es_original": True,
                "es_definitiva": True
            }
        }
