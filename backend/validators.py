"""
validators.py - Motor de validación de facturas usando IA
Valida facturas según la Cartilla CT-COA-0124 haciendo un análisis con Gemini
"""

from typing import Dict, List, Optional
from models import FacturaComercial
from datetime import date, timedelta
from gemini_validator import GeminiValidator


class ValidadorDIAN:
    """
    El validador maneja reglas de la DIAN y validaciones hechas por gemini
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Inicializa el validador, opcionalmente con capacidades de IA.
        
        Args:
            gemini_api_key: API key de Google Gemini (opcional)
        """
        self.usa_ia = False
        self.gemini = None
        
        if gemini_api_key:
            try:
                self.gemini = GeminiValidator(gemini_api_key)
                self.usa_ia = True
                print("✅ Validador IA inicializado correctamente")
            except Exception as e:
                print(f"⚠️ No se pudo inicializar Gemini IA: {e}")
                print("ℹ️ Continuando solo con validaciones tradicionales")
                self.usa_ia = False
    
    def validar(self, factura: FacturaComercial) -> Dict:
        """
        Valida una factura completa y retorna resultado detallado.
        
        Args:
            factura: Objeto FacturaComercial a validar
            
        Returns:
            Dict con estructura:
            {
                "cumple": bool,
                "errores": List[Dict],
                "advertencias": List[Dict],
                "sugerencias": List[str],
                "validacion_ia": Dict (si usa_ia=True)
            }
        """
        # Estructura de resultado
        resultado = {
            "cumple": True,
            "errores": [],
            "advertencias": [],
            "sugerencias": [],
            "validacion_ia": None
        }
        
        # VALIDACIONES BÁSICAS
        
        self._validar_tipo_documento(factura, resultado)
        self._validar_numero_factura(factura, resultado)
        self._validar_datos_vendedor(factura, resultado)
        self._validar_datos_comprador(factura, resultado)
        self._validar_fecha(factura, resultado)
        self._validar_descripciones_items(factura, resultado)
        self._validar_coherencia_valores(factura, resultado)
        self._validar_moneda(factura, resultado)
        self._validar_incoterms(factura, resultado)
        self._validar_puertos(factura, resultado)
        self._validar_pais_origen(factura, resultado)
        
        # VALIDACIONES CON IA
        
        if self.usa_ia and self.gemini:
            try:
                self._validar_con_ia(factura, resultado)
            except Exception as e:
                print(f"⚠️ Error en validación IA: {e}")
                # No detener la validación si falla la IA
                resultado["advertencias"].append({
                    "campo": "validacion_ia",
                    "mensaje": "El análisis con IA no pudo completarse"
                })
        
        return resultado
    
    # VALIDACIONES DETERMINÍSTICAS
    
    def _validar_tipo_documento(self, factura: FacturaComercial, resultado: Dict):
        """Valida que la factura sea definitiva (no pro forma)"""
        tipo_factura = factura.invoice_type.upper()
        
        if "PRO FORMA" in tipo_factura or "PROFORMA" in tipo_factura:
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "InvoiceType",
                "mensaje": f"No se aceptan facturas pro forma. Tipo actual: '{factura.invoice_type}'",
                "codigo": "DIAN_001"
            })
            resultado["sugerencias"].append(
                "Solicite al proveedor una factura comercial definitiva (Commercial Invoice)"
            )
    
    def _validar_numero_factura(self, factura: FacturaComercial, resultado: Dict):
        """Valida que exista número de factura"""
        if not factura.invoice_number or factura.invoice_number.strip() == "":
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "InvoiceNumber",
                "mensaje": "El número de factura es obligatorio",
                "codigo": "DIAN_002"
            })
            resultado["sugerencias"].append("Solicite el número de factura al proveedor")
    
    def _validar_datos_vendedor(self, factura: FacturaComercial, resultado: Dict):
        """Valida completitud de datos del vendedor (Supplier)"""
        # Nombre del vendedor
        if not factura.supplier or len(factura.supplier.strip()) < 3:
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "Supplier",
                "mensaje": "El nombre del vendedor es obligatorio y debe ser completo",
                "codigo": "DIAN_003"
            })
            resultado["sugerencias"].append("Complete la razón social del proveedor")
        
        # Dirección del vendedor
        if not factura.supplier_address or len(factura.supplier_address.strip()) < 10:
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "SupplierAddress",
                "mensaje": "La dirección del vendedor debe ser completa",
                "codigo": "DIAN_004"
            })
            resultado["sugerencias"].append("Incluya dirección completa: calle, número, ciudad, país")
    
    def _validar_datos_comprador(self, factura: FacturaComercial, resultado: Dict):
        """Valida completitud de datos del comprador (Customer)"""
        # Nombre del comprador
        if not factura.customer or len(factura.customer.strip()) < 3:
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "Customer",
                "mensaje": "El nombre del comprador es obligatorio",
                "codigo": "DIAN_005"
            })
        
        # Dirección del comprador
        if not factura.customer_address or len(factura.customer_address.strip()) < 5:
            resultado["advertencias"].append({
                "campo": "CustomerAddress",
                "mensaje": "La dirección del comprador debería ser más completa"
            })
        
        # NIT del comprador (importante para Colombia)
        if not factura.customer_tax_id or factura.customer_tax_id.strip() == "":
            resultado["advertencias"].append({
                "campo": "CustomerTaxID",
                "mensaje": "Se recomienda incluir el NIT del comprador colombiano"
            })
    
    def _validar_fecha(self, factura: FacturaComercial, resultado: Dict):
        """Valida coherencia de fecha de expedición"""
        # Verificar que exista fecha
        if not factura.invoice_date or factura.invoice_date.strip() == "":
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "InvoiceDate",
                "mensaje": "La fecha de expedición es obligatoria",
                "codigo": "DIAN_006"
            })
            return
        
        # Intentar parsear fecha
        fecha_factura = factura.parse_date()
        
        if fecha_factura:
            hoy = date.today()
            
            # Fecha no puede ser futura
            if fecha_factura > hoy:
                resultado["cumple"] = False
                resultado["errores"].append({
                    "campo": "InvoiceDate",
                    "mensaje": f"La fecha ({fecha_factura}) no puede ser futura",
                    "codigo": "DIAN_007"
                })
                resultado["sugerencias"].append("Verifique la fecha de emisión con el proveedor")
            
            # Advertencia si la factura es muy antigua
            if fecha_factura < (hoy - timedelta(days=365)):
                resultado["advertencias"].append({
                    "campo": "InvoiceDate",
                    "mensaje": f"La factura tiene más de un año de antigüedad ({fecha_factura})"
                })
        else:
            # No se pudo parsear la fecha
            resultado["advertencias"].append({
                "campo": "InvoiceDate",
                "mensaje": f"Formato de fecha no reconocido: '{factura.invoice_date}'"
            })
    
    def _validar_descripciones_items(self, factura: FacturaComercial, resultado: Dict):
        """
        Valida que las descripciones de mercancía sean suficientemente específicas.
        Incluye validación con IA si está disponible.
        """
        for idx, item in enumerate(factura.Table):
            descripcion = item.Description.strip()
            
            # Validación básica: longitud mínima
            if len(descripcion) < 10:
                resultado["cumple"] = False
                resultado["errores"].append({
                    "campo": f"Table[{idx}].Description",
                    "mensaje": f"Descripción demasiado corta: '{descripcion}'",
                    "codigo": "DIAN_008"
                })
                resultado["sugerencias"].append(
                    f"Item {idx + 1}: Incluya marca, modelo y características técnicas"
                )
                continue
            
            # VALIDACIÓN CON IA (si está disponible)
            if self.usa_ia and self.gemini:
                try:
                    cantidad = item.get_quantity_float()
                    precio = item.get_unit_price_float()
                    
                    # Llamar a Gemini para análisis avanzado
                    analisis_ia = self.gemini.validar_descripcion_mercancia(
                        descripcion, cantidad, precio
                    )
                    
                    # Si la IA dice que no es válida
                    if analisis_ia.get("es_valida") == False:
                        resultado["advertencias"].append({
                            "campo": f"Table[{idx}].Description",
                            "mensaje": f"🤖 IA detectó: {analisis_ia.get('razon', 'Descripción insuficiente')}"
                        })
                        
                        # Agregar sugerencia de la IA
                        if analisis_ia.get("sugerencia"):
                            resultado["sugerencias"].append(
                                f"🤖 Item {idx + 1}: {analisis_ia['sugerencia']}"
                            )
                
                except Exception as e:
                    # No detener si falla análisis IA de un item
                    print(f"⚠️ Error IA en item {idx}: {e}")
    
    def _validar_coherencia_valores(self, factura: FacturaComercial, resultado: Dict):
        """Valida coherencia entre cantidades, precios y totales"""
        # Validar cada item individualmente
        for idx, item in enumerate(factura.Table):
            try:
                cantidad = item.get_quantity_float()
                precio_unit = item.get_unit_price_float()
                total_item = item.get_net_value_float()
                
                if cantidad > 0 and precio_unit > 0:
                    # Calcular total esperado
                    total_calculado = round(cantidad * precio_unit, 2)
                    diferencia = abs(total_calculado - total_item)
                    
                    # Tolerancia: 1% del valor o mínimo $1
                    tolerancia = max(total_calculado * 0.01, 1.0)
                    
                    if diferencia > tolerancia:
                        resultado["advertencias"].append({
                            "campo": f"Table[{idx}].NetValuePerItem",
                            "mensaje": f"Item {idx+1}: Posible error. Calculado: ${total_calculado:.2f}, Declarado: ${total_item:.2f}"
                        })
            except Exception as e:
                # Si hay error convirtiendo números, registrar advertencia
                resultado["advertencias"].append({
                    "campo": f"Table[{idx}]",
                    "mensaje": f"No se pudieron validar valores numéricos del item {idx+1}"
                })
        
        # Validar suma total de items vs total de factura
        try:
            total_items = sum(item.get_net_value_float() for item in factura.Table)
            total_factura = factura.get_total_float()
            
            if total_factura > 0:
                diferencia = abs(total_items - total_factura)
                tolerancia = max(total_factura * 0.01, 2.0)  # 1% o mínimo $2
                
                if diferencia > tolerancia:
                    resultado["advertencias"].append({
                        "campo": "TotalInvoiceValue",
                        "mensaje": f"Suma de items (${total_items:.2f}) difiere del total declarado (${total_factura:.2f})"
                    })
        except:
            pass
    
    def _validar_moneda(self, factura: FacturaComercial, resultado: Dict):
        """Valida que se especifique moneda válida"""
        if not factura.currency or factura.currency.strip() == "":
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "Currency",
                "mensaje": "La moneda de transacción es obligatoria",
                "codigo": "DIAN_009"
            })
            resultado["sugerencias"].append("Especifique la moneda (USD, EUR, COP, etc.)")
        else:
            # Lista de monedas comunes
            monedas_validas = ["USD", "EUR", "COP", "CNY", "GBP", "JPY", "CAD", "MXN"]
            if factura.currency.upper() not in monedas_validas:
                resultado["advertencias"].append({
                    "campo": "Currency",
                    "mensaje": f"Moneda '{factura.currency}' no es común. Verifique código ISO"
                })
    
    def _validar_incoterms(self, factura: FacturaComercial, resultado: Dict):
        """Valida que se especifique Incoterm válido"""
        if not factura.incoterm or factura.incoterm.strip() == "":
            resultado["cumple"] = False
            resultado["errores"].append({
                "campo": "Incoterm",
                "mensaje": "El Incoterm es obligatorio para importación",
                "codigo": "DIAN_010"
            })
            resultado["sugerencias"].append("Especifique el Incoterm (FOB, CIF, CIP, etc.)")
        else:
            # Lista de Incoterms válidos (Incoterms 2020)
            incoterms_validos = [
                "EXW", "FCA", "FAS", "FOB",  # Grupo E y F
                "CFR", "CIF", "CPT", "CIP",  # Grupo C
                "DAP", "DPU", "DDP"           # Grupo D
            ]
            
            incoterm_upper = factura.incoterm.upper()
            if incoterm_upper not in incoterms_validos:
                resultado["advertencias"].append({
                    "campo": "Incoterm",
                    "mensaje": f"Incoterm '{factura.incoterm}' no reconocido o desactualizado"
                })
    
    def _validar_puertos(self, factura: FacturaComercial, resultado: Dict):
        """Valida que se especifiquen puertos de carga y descarga"""
        if not factura.port_of_loading or factura.port_of_loading.strip() == "":
            resultado["advertencias"].append({
                "campo": "PortOfLoading",
                "mensaje": "Debería especificarse el puerto de carga"
            })
        
        if not factura.port_of_discharge or factura.port_of_discharge.strip() == "":
            resultado["advertencias"].append({
                "campo": "PortOfDischarge",
                "mensaje": "Debería especificarse el puerto de descarga en Colombia"
            })
    
    def _validar_pais_origen(self, factura: FacturaComercial, resultado: Dict):
        """Valida que se especifique país de origen"""
        if not factura.country_of_origin or factura.country_of_origin.strip() == "":
            resultado["advertencias"].append({
                "campo": "CountryOfOrigin",
                "mensaje": "Se recomienda especificar el país de origen de la mercancía"
            })
    
    # VALIDACIÓN CON IA 
    
    def _validar_con_ia(self, factura: FacturaComercial, resultado: Dict):
        """
        Realiza validaciones avanzadas usando Gemini AI.
        Analiza coherencia general de la factura.
        """
        if not self.gemini:
            return
        
        try:
            # Convertir factura a dict simple para enviar a IA
            factura_dict = factura.to_simple_dict()
            
            # Llamar a Gemini para análisis de coherencia
            coherencia = self.gemini.analizar_coherencia_factura(factura_dict)
            
            # Guardar resultado de IA en la estructura de respuesta
            resultado["validacion_ia"] = {
                "coherente": coherencia.get("coherente"),
                "problemas_detectados": coherencia.get("problemas", []),
                "advertencias_ia": coherencia.get("advertencias", [])
            }
            
            # Agregar problemas detectados por IA a la lista general
            for problema in coherencia.get("problemas", []):
                resultado["advertencias"].append({
                    "campo": "coherencia_general",
                    "mensaje": f"🤖 IA: {problema}"
                })
            
            # Agregar advertencias de IA
            for advertencia in coherencia.get("advertencias", []):
                resultado["advertencias"].append({
                    "campo": "coherencia_general",
                    "mensaje": f"🤖 IA: {advertencia}"
                })
        
        except Exception as e:
            print(f"⚠️ Error en análisis de coherencia con IA: {e}")
            # No detener la validación completa si falla IA
            resultado["validacion_ia"] = {
                "coherente": None,
                "problemas_detectados": [],
                "advertencias_ia": [f"Error en análisis: {str(e)}"]
            }
