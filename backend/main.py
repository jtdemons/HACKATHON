from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from models import FacturaComercial
from validators import ValidadorDIAN
import json

app = FastAPI(
    title="Validador de Facturas DIAN",
    description="Sistema de validación de facturas comerciales de importación",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "mensaje": "API Validador de Facturas DIAN",
        "version": "1.0.0",
        "endpoints": ["/validar", "/validar-lote", "/requisitos"]
    }

@app.post("/validar")
async def validar_factura(factura: FacturaComercial):
    """Valida una factura individual"""
    try:
        resultado = ValidadorDIAN.validar(factura)
        return {
            "success": True,
            "factura_numero": factura.numero_factura,
            "resultado": resultado
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/validar-lote")
async def validar_lote(file: UploadFile = File(...)):
    """Valida múltiples facturas desde JSON"""
    try:
        contenido = await file.read()
        facturas_data = json.loads(contenido)
        
        if not isinstance(facturas_data, list):
            facturas_data = [facturas_data]
        
        resultados = []
        
        for idx, factura_data in enumerate(facturas_data):
            try:
                factura = FacturaComercial(**factura_data)
                validacion = ValidadorDIAN.validar(factura)
                
                resultados.append({
                    "indice": idx,
                    "factura_numero": factura.numero_factura,
                    "resultado": validacion
                })
            except Exception as e:
                resultados.append({
                    "indice": idx,
                    "factura_numero": factura_data.get("numero_factura", "N/A"),
                    "resultado": {
                        "cumple": False,
                        "errores": [{"campo": "general", "mensaje": str(e)}],
                        "advertencias": [],
                        "sugerencias": []
                    }
                })
        
        total = len(resultados)
        aprobadas = sum(1 for r in resultados if r["resultado"]["cumple"])
        
        return {
            "success": True,
            "resumen": {
                "total": total,
                "aprobadas": aprobadas,
                "rechazadas": total - aprobadas,
                "porcentaje": round((aprobadas / total * 100), 1) if total > 0 else 0
            },
            "facturas": resultados
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="JSON no válido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/requisitos")
async def obtener_requisitos():
    """Retorna requisitos DIAN"""
    return {
        "normativa": "Resolución Andina 1684/2014 - Art. 9",
        "cartilla": "CT-COA-0124",
        "campos_obligatorios": {
            "identificacion": ["Número de factura", "Fecha de expedición", "Lugar de expedición"],
            "partes": ["Nombre y dirección del vendedor", "Nombre y dirección del comprador"],
            "mercancia": ["Descripción detallada", "Cantidad", "Precio unitario", "Precio total"],
            "valores": ["Precio neto total", "Moneda de transacción", "Descuentos discriminados"],
            "terminos": ["INCOTERM", "Lugar de entrega", "Gastos de transporte", "Costo de seguro"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
