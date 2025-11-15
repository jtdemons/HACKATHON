from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from models import FacturaComercial
from validators import ValidadorDIAN
import json
import os
from typing import Optional

app = FastAPI(
    title="Validador de Facturas DIAN con IA",
    description="Sistema de validación de facturas comerciales de importación potenciado por Gemini AI",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def obtener_api_key() -> Optional[str]:
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        print(f"✅ API Key cargada desde variable de entorno (longitud: {len(api_key)})")
        return api_key
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        
        if api_key:
            print(f"✅ API Key cargada desde archivo .env (longitud: {len(api_key)})")
            return api_key
    except ImportError:
        print("ℹ️ python-dotenv no instalado. Instálalo con: pip install python-dotenv")
    
    print("⚠️ No se encontró API Key de Gemini. El sistema funcionará sin IA.")
    return None


GEMINI_API_KEY = obtener_api_key()

validador = ValidadorDIAN(gemini_api_key=GEMINI_API_KEY)


@app.get("/")
async def root():
    return {
        "mensaje": "API de Validación de Facturas DIAN con IA",
        "version": "2.0.0",
        "ia_activa": validador.usa_ia,
        "modelo_ia": "Gemini 1.5 Flash" if validador.usa_ia else "N/A",
        "endpoints": {
            "GET /": "Información de la API",
            "POST /validar": "Valida una factura individual",
            "POST /validar-lote": "Valida múltiples facturas desde JSON",
            "GET /requisitos": "Requisitos legales DIAN",
            "GET /health": "Estado del sistema"
        },
        "documentacion": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "validador": "activo",
        "ia": "activa" if validador.usa_ia else "inactiva"
    }


@app.post("/validar")
async def validar_factura(factura: FacturaComercial):
    try:
        resultado = validador.validar(factura)
        
        return {
            "success": True,
            "factura_numero": factura.invoice_number,
            "resultado": resultado,
            "ia_utilizada": validador.usa_ia
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al validar factura: {str(e)}"
        )


@app.post("/validar-lote")
async def validar_lote(file: UploadFile = File(...)):
    try:
        contenido = await file.read()
        facturas_data = json.loads(contenido)
        if not isinstance(facturas_data, list):
            facturas_data = [facturas_data]
        
        resultados = []
        
        # aqui validamos cada factura
        for idx, factura_data in enumerate(facturas_data):
            try:
                factura = FacturaComercial(**factura_data)
                validacion = validador.validar(factura)
                resultados.append({
                    "indice": idx,
                    "factura_numero": factura.invoice_number,
                    "resultado": validacion
                })
                
            except Exception as e:
                resultados.append({
                    "indice": idx,
                    "factura_numero": factura_data.get("Fields", [{}])[0].get("Value", "N/A") 
                                      if isinstance(factura_data.get("Fields"), list) else "N/A",
                    "resultado": {
                        "cumple": False,
                        "errores": [{
                            "campo": "estructura_json",
                            "mensaje": f"Error al parsear factura: {str(e)}",
                            "codigo": "ERROR_JSON"
                        }],
                        "advertencias": [],
                        "sugerencias": ["Verifique que el JSON tenga la estructura correcta"],
                        "validacion_ia": None
                    }
                })
        
        total = len(resultados)
        aprobadas = sum(1 for r in resultados if r["resultado"]["cumple"])
        rechazadas = total - aprobadas
        porcentaje = round((aprobadas / total * 100), 1) if total > 0 else 0
        
        return {
            "success": True,
            "resumen": {
                "total": total,
                "aprobadas": aprobadas,
                "rechazadas": rechazadas,
                "porcentaje": porcentaje,
                "estado": "✅ TODAS CUMPLEN" if rechazadas == 0 else f"⚠️ {rechazadas} NO CUMPLEN"
            },
            "facturas": resultados,
            "ia_utilizada": validador.usa_ia
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"JSON no válido: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )


@app.get("/requisitos")
async def obtener_requisitos():
    return {
        "normativa": "Resolución Andina 1684/2014 - Artículo 9",
        "cartilla": "CT-COA-0124",
        "titulo": "Factura Comercial en la Determinación del Valor en Aduana",
        "campos_obligatorios": {
            "identificacion": [
                "Número de factura único",
                "Fecha de expedición",
                "Lugar de expedición"
            ],
            "partes": [
                "Nombre completo y dirección del vendedor",
                "Nombre completo y dirección del comprador",
                "NIT o Tax ID (recomendado)"
            ],
            "mercancia": [
                "Descripción detallada de cada producto",
                "Marca y modelo (si aplica)",
                "Cantidad de unidades",
                "Precio unitario",
                "Precio total por ítem"
            ],
            "valores": [
                "Precio neto total de la factura",
                "Moneda de transacción",
                "Descuentos discriminados con concepto",
                "Coherencia entre suma de items y total"
            ],
            "terminos_comerciales": [
                "INCOTERM válido (FOB, CIF, CIP, etc.)",
                "Lugar de entrega",
                "Puerto de carga",
                "Puerto de descarga",
                "País de origen"
            ]
        },
        "validaciones_ia": [
            "Análisis semántico de descripciones de mercancía",
            "Detección de inconsistencias entre campos relacionados",
            "Verificación de coherencia geográfica y comercial",
            "Sugerencias inteligentes de corrección"
        ] if validador.usa_ia else []
    }


# Aqui vamos a realizar el manejo de errores

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Endpoint no encontrado",
        "mensaje": "Verifique la ruta de la petición",
        "endpoints_disponibles": ["/", "/validar", "/validar-lote", "/requisitos", "/health"]
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {
        "error": "Error interno del servidor",
        "mensaje": "Por favor contacte al administrador del sistema"
    }



if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("🚀 Iniciando Validador de Facturas DIAN")
    print("=" * 80)
    print(f"ℹ️ Inteligencia Artificial: {'✅ ACTIVA' if validador.usa_ia else '❌ INACTIVA'}")
    print(f"ℹ️ Servidor: http://localhost:8000")
    print(f"ℹ️ Documentación: http://localhost:8000/docs")
    print("=" * 80)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
