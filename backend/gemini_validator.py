import google.generativeai as genai
from typing import Dict, List, Optional
import json
import time


class GeminiValidator:
    """
    Validador inteligente que usa Gemini AI para análisis de facturas.
    """
    
    def __init__(self, api_key: str):
        """
        Se crea el constructor para iniciar la configuración de Gemini AI
        
        Args:
            api_key: API key de Google Gemini
        """
        genai.configure(api_key=api_key)
        # modelos = genai.list_models()
        # for m in modelos:
        #     print(f"{m.name} soportados {m.supported_generation_methods}")
        #     print('-----------------------')
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        # Rate limiting: evitar exceder límites de API
        self.ultima_llamada = 0
        self.min_tiempo_entre_llamadas = 0.05
    
    # def _esperar_rate_limit(self):
    #     """
    #     Implementa un límite de llamadas para no exceder la capacidad de la API.
    #     """
    #     tiempo_actual = time.time()
    #     tiempo_transcurrido = tiempo_actual - self.ultima_llamada
        
    #     if tiempo_transcurrido < self.min_tiempo_entre_llamadas:
    #         time.sleep(self.min_tiempo_entre_llamadas - tiempo_transcurrido)
        
    #     self.ultima_llamada = time.time()
    
    def _limpiar_respuesta_json(self, texto: str) -> str:
        """
        Limpia la respuesta de Gemini para extraer JSON puro.
        
        Args:
            texto: Respuesta raw de Gemini
            
        Returns:
            str: JSON limpio
        """
        texto = texto.strip()
        
        # Remover bloques markdown si existen
        if texto.startswith("```json"):
            texto = texto.replace("```json", "").replace("```", "").strip()
        elif texto.startswith("```"):
            texto = texto.replace("```", "").strip()
        
        return texto
    
    def validar_descripcion_mercancia(
        self, 
        descripcion: str, 
        cantidad: float, 
        precio: float
    ) -> Dict:
        """
        Analiza si una descripción de mercancía cumple con requisitos DIAN usando IA.
        
        Args:
            descripcion: Descripción del producto
            cantidad: Cantidad de unidades
            precio: Precio unitario
            
        Returns:
            Dict con estructura:
            {
                "es_valida": bool,
                "razon": str,
                "sugerencia": str
            }
        """
        # self._esperar_rate_limit()
        
        prompt = f"""
Eres un experto en comercio internacional y normativa aduanera colombiana (DIAN).

Analiza si la siguiente descripción de mercancía en una factura de importación cumple con los requisitos de la DIAN:

Descripción: "{descripcion}"
Cantidad: {cantidad}
Precio unitario: ${precio}

Una descripción válida según la DIAN debe incluir:
1. Nombre específico del producto (no genérico como "productos varios")
2. Marca comercial (si aplica)
3. Modelo o referencia (si aplica)
4. Características técnicas relevantes (material, tamaño, capacidad, etc.)
5. Composición o ingredientes principales (si aplica)

Criterios de evaluación:
- INVÁLIDO: Descripciones genéricas como "productos", "mercancía", "items"
- INSUFICIENTE: Solo nombre sin detalles técnicos
- VÁLIDO: Nombre + marca/modelo + características técnicas

Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
{{
  "es_valida": true o false,
  "razon": "explicación breve de por qué es válida o no",
  "sugerencia": "cómo mejorar la descripción (solo si no es válida, sino dejar vacío)"
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            texto = self._limpiar_respuesta_json(response.text)
            resultado = json.loads(texto)
            
            # Validar que tenga la estructura esperada
            if not all(key in resultado for key in ["es_valida", "razon", "sugerencia"]):
                raise ValueError("Respuesta de IA con estructura inválida")
            
            return resultado
            
        except Exception as e:
            # Fallback: si la IA falla, retornar estructura segura
            return {
                "es_valida": None,
                "razon": f"Error al analizar con IA: {str(e)}",
                "sugerencia": ""
            }
    
    def analizar_coherencia_factura(self, factura_data: Dict) -> Dict:
        """
        Analiza la coherencia general de una factura completa usando IA.
        Detecta inconsistencias entre campos relacionados.
        
        Args:
            factura_data: Diccionario con datos principales de la factura
            
        Returns:
            Dict con estructura:
            {
                "coherente": bool,
                "problemas": List[str],
                "advertencias": List[str]
            }
        """
        # self._esperar_rate_limit()
        
        # Preparar datos para enviar a IA (solo lo esencial)
        datos_simplificados = {
            "proveedor": factura_data.get("supplier", ""),
            "cliente": factura_data.get("customer", ""),
            "pais_origen": factura_data.get("country_of_origin", ""),
            "moneda": factura_data.get("currency", ""),
            "incoterm": factura_data.get("incoterm", ""),
            "puerto_carga": factura_data.get("port_of_loading", ""),
            "puerto_descarga": factura_data.get("port_of_discharge", ""),
            "valor_total": factura_data.get("total_value", "")
        }
        
        prompt = f"""
Eres un experto en comercio internacional y normativa aduanera colombiana.

Analiza la siguiente factura de importación y detecta INCONSISTENCIAS o INCOHERENCIAS entre sus datos:

Datos de la factura:
{json.dumps(datos_simplificados, indent=2, ensure_ascii=False)}

Verifica específicamente:

1. COHERENCIA GEOGRÁFICA:
   - ¿La moneda es típica del país del proveedor?
   - ¿Los puertos declarados existen y son coherentes?
   - ¿El país de origen coincide con la ubicación del proveedor?

2. COHERENCIA COMERCIAL:
   - ¿El Incoterm tiene sentido según los puertos declarados?
   - ¿El valor total parece razonable (no es $0 ni cantidades irreales)?

3. CONSISTENCIA DE DATOS:
   - ¿Hay campos críticos vacíos que deberían estar llenos?
   - ¿Hay contradicciones obvias?

Responde ÚNICAMENTE en formato JSON válido con esta estructura exacta:
{{
  "coherente": true o false,
  "problemas": ["problema grave 1", "problema grave 2"],
  "advertencias": ["advertencia 1", "advertencia 2"]
}}

Si todo está bien, usa listas vacías para problemas y advertencias.
"""
        
        try:
            response = self.model.generate_content(prompt)
            texto = self._limpiar_respuesta_json(response.text)
            resultado = json.loads(texto)
            
            # Validar estructura
            if not all(key in resultado for key in ["coherente", "problemas", "advertencias"]):
                raise ValueError("Respuesta de IA con estructura inválida")
            
            return resultado
            
        except Exception as e:
            # Fallback seguro
            return {
                "coherente": None,
                "problemas": [],
                "advertencias": [f"Error en análisis IA: {str(e)}"]
            }
    
    def sugerir_correccion(
        self, 
        campo: str, 
        valor_actual: str, 
        contexto: str
    ) -> str:
        """
        Genera una sugerencia inteligente de corrección para un campo con error.
        
        Args:
            campo: Nombre del campo con error
            valor_actual: Valor actual del campo
            contexto: Contexto adicional sobre el error
            
        Returns:
            str: Sugerencia de corrección
        """
        # self._esperar_rate_limit()
        
        prompt = f"""
Campo de factura con error: {campo}
Valor actual: "{valor_actual}"
Contexto del error: {contexto}

Genera una sugerencia breve (máximo 2 líneas) de cómo corregir este campo para cumplir con requisitos de la DIAN Colombia.
La sugerencia debe ser específica, accionable y en español.

Responde SOLO con la sugerencia, sin formato adicional.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return "Revise y complete este campo según los requisitos DIAN"
    
    def verificar_precios_coherentes(
        self, 
        items: List[Dict]
    ) -> Dict:
        """
        Analiza si los precios de los items son coherentes y razonables.
        
        Args:
            items: Lista de diccionarios con información de items
            
        Returns:
            Dict con análisis de precios
        """
        # self._esperar_rate_limit()
        
        # Preparar resumen de items para IA
        items_resumidos = []
        for i, item in enumerate(items[:7]):  # Máximo 10 items para no saturar
            items_resumidos.append({
                "numero": i + 1,
                "descripcion": item.get("Description", "")[:100],
                "cantidad": item.get("Quantity", ""),
                "precio_unitario": item.get("UnitPrice", ""),
                "total": item.get("NetValuePerItem", "")
            })
        
        prompt = f"""
Analiza si los precios de estos items de factura son coherentes y razonables:

{json.dumps(items_resumidos, indent=2, ensure_ascii=False)}

Detecta:
1. Precios unitarios sospechosamente bajos o altos
2. Inconsistencias en cálculos (cantidad × precio ≠ total)
3. Precios poco realistas para el tipo de producto

Responde en formato JSON:
{{
  "precios_coherentes": true o false,
  "items_sospechosos": ["item 1: razón", "item 2: razón"]
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            texto = self._limpiar_respuesta_json(response.text)
            return json.loads(texto)
        except:
            return {
                "precios_coherentes": None,
                "items_sospechosos": []
            }
