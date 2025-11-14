from typing import Dict, List
from models import FacturaComercial
from datetime import date, timedelta

class ValidadorDIAN:
    """Motor de validación de facturas según Cartilla CT-COA-0124 DIAN"""
    
    @staticmethod
    def validar(factura: FacturaComercial) -> Dict:
        """Valida una factura y retorna resultado detallado"""
        resultado = {
            "cumple": True,
            "errores": [],
            "advertencias": [],
            "sugerencias": []
        }
        
        # Validación 1: Tipo de documento
        if not factura.es_definitiva:
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "es_definitiva",
                "mensaje": "La factura debe ser definitiva, no se aceptan facturas pro forma",
                "codigo": "VALOR_001"
            })
            resultado["sugerencias"].append("Solicite al vendedor una factura comercial definitiva")
        
        if not factura.es_original:
            resultado["advertencias"].append({
                "campo": "es_original",
                "mensaje": "Se recomienda presentar el original de la factura"
            })
        
        # Validación 2: Número de factura
        if not factura.numero_factura or factura.numero_factura.strip() == "":
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "numero_factura",
                "mensaje": "El número de factura es obligatorio",
                "codigo": "VALOR_002"
            })
        
        # Validación 3: Lugar de expedición
        if not factura.lugar_expedicion or len(factura.lugar_expedicion) < 3:
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "lugar_expedicion",
                "mensaje": "El lugar de expedición debe especificarse claramente",
                "codigo": "VALOR_003"
            })
        
        # Validación 4: Datos del vendedor
        if len(factura.nombre_vendedor) < 3:
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "nombre_vendedor",
                "mensaje": "El nombre del vendedor debe ser completo",
                "codigo": "VALOR_004"
            })
        
        if len(factura.direccion_vendedor) < 5:
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "direccion_vendedor",
                "mensaje": "La dirección del vendedor debe ser completa",
                "codigo": "VALOR_005"
            })
        
        # Validación 5: Datos del comprador
        if len(factura.nombre_comprador) < 3:
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "nombre_comprador",
                "mensaje": "El nombre del comprador debe ser completo",
                "codigo": "VALOR_006"
            })
        
        if len(factura.direccion_comprador) < 5:
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "direccion_comprador",
                "mensaje": "La dirección del comprador debe ser completa",
                "codigo": "VALOR_007"
            })
        
        # Validación 6: Descripción de mercancía
        for idx, item in enumerate(factura.items):
            if len(item.descripcion) < 10:
                resultado["cumple"] = False
                resultado["errores"].append({
                    "campo": f"items[{idx}].descripcion",
                    "mensaje": f"Descripción demasiado genérica: '{item.descripcion}'",
                    "codigo": "VALOR_008"
                })
                resultado["sugerencias"].append(f"Incluya marca, modelo y características del item {idx + 1}")
        
        # Validación 7: Fechas
        hoy = date.today()
        if factura.fecha_expedicion > hoy:
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "fecha_expedicion",
                "mensaje": f"La fecha ({factura.fecha_expedicion}) no puede ser futura",
                "codigo": "VALOR_009"
            })
        
        if factura.fecha_expedicion < (hoy - timedelta(days=365)):
            resultado["advertencias"].append({
                "campo": "fecha_expedicion",
                "mensaje": f"La factura tiene más de un año ({factura.fecha_expedicion})"
            })
        
        # Validación 8: Coherencia de valores
        total_items = round(sum(item.precio_total for item in factura.items), 2)
        if abs(total_items - factura.precio_neto_factura) > 0.01:
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "precio_neto_factura",
                "mensaje": f"Precio neto ({factura.precio_neto_factura}) no coincide con suma de items ({total_items})",
                "codigo": "VALOR_010"
            })
            resultado["sugerencias"].append("Recalcule el precio neto")
        
        # Validación 9: Moneda válida
        monedas_validas = ["USD", "EUR", "COP", "CNY", "GBP", "JPY"]
        if factura.moneda not in monedas_validas:
            resultado["advertencias"].append({
                "campo": "moneda",
                "mensaje": f"Moneda '{factura.moneda}' no es común. Verifique código ISO"
            })
        
        # Validación 10: Incoterms
        incoterms_validos = ["EXW", "FCA", "FAS", "FOB", "CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP"]
        if factura.incoterm not in incoterms_validos:
            resultado["advertencias"].append({
                "campo": "incoterm",
                "mensaje": f"Incoterm '{factura.incoterm}' no reconocido"
            })
        
        # Validación 11: Gastos por Incoterm
        if factura.incoterm in ["CIF", "CIP"]:
            if factura.costo_seguro == 0:
                resultado["cumple"] = False
                resultado["errores"].append({
                    "campo": "costo_seguro",
                    "mensaje": f"Incoterm {factura.incoterm} debe incluir costo de seguro",
                    "codigo": "VALOR_011"
                })
                resultado["sugerencias"].append("Agregue el costo del seguro según póliza")
        
        if factura.incoterm in ["CFR", "CPT", "CIF", "CIP", "DAP", "DPU", "DDP"]:
            if factura.gastos_transporte == 0:
                resultado["advertencias"].append({
                    "campo": "gastos_transporte",
                    "mensaje": f"Incoterm {factura.incoterm} usualmente incluye gastos de transporte"
                })
        
        # Validación 12: Descuentos
        if factura.descuentos > 0:
            if not factura.concepto_descuento or factura.concepto_descuento.strip() == "":
                resultado["cumple"] = False
                resultado["errores"].append({
                    "campo": "concepto_descuento",
                    "mensaje": "Los descuentos deben tener concepto identificado",
                    "codigo": "VALOR_012"
                })
                resultado["sugerencias"].append("Especifique el motivo del descuento (pronto pago, volumen, etc.)")
            
            if factura.descuentos > factura.precio_neto_factura:
                resultado["cumple"] = False
                resultado["errores"].append({
                    "campo": "descuentos",
                    "mensaje": "El descuento no puede ser mayor al precio neto",
                    "codigo": "VALOR_013"
                })
        
        return resultado
