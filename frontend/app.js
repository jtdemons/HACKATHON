const API_URL = 'http://localhost:8000';

async function verRequisitos() {
    const div = document.getElementById('requisitos');
    
    try {
        const response = await fetch(`${API_URL}/requisitos`);
        const data = await response.json();
        
        const html = `
            <div class="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-8">
                <h2 class="text-3xl font-bold mb-2 text-blue-400">
                    <i class="fas fa-balance-scale"></i> Requisitos Legales DIAN
                </h2>
                <p class="text-gray-400 text-sm mb-6">
                    ${data.normativa} | ${data.cartilla}
                </p>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    ${Object.entries(data.campos_obligatorios).map(([categoria, campos]) => `
                        <div class="bg-slate-700 border border-slate-600 p-6 rounded-lg">
                            <h3 class="font-bold text-lg mb-3 text-blue-300 capitalize">
                                <i class="fas fa-check-double"></i> ${categoria.replace('_', ' ')}
                            </h3>
                            <ul class="space-y-2">
                                ${campos.map(campo => `
                                    <li class="flex items-start gap-2">
                                        <i class="fas fa-circle text-blue-500 text-xs mt-1.5"></i>
                                        <span class="text-gray-300">${campo}</span>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        div.innerHTML = html;
        div.classList.remove('hidden');
        div.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        mostrarError('Error al cargar requisitos: ' + error.message);
    }
}

async function descargarEjemplo() {
    try {
        const ejemplo = {
            "numero_factura": "INV-2025-00124",
            "fecha_expedicion": "2025-11-01",
            "lugar_expedicion": "Shanghai, China",
            "nombre_vendedor": "Shanghai Premium Manufacturing Co., Ltd.",
            "direccion_vendedor": "123 Industrial Development Zone, Pudong District",
            "pais_vendedor": "China",
            "nombre_comprador": "Importadora Colombia SAS",
            "direccion_comprador": "Calle 100 No. 10-20 Apto 502",
            "ciudad_comprador": "Bogotá",
            "items": [
                {
                    "descripcion": "Microcontrolador ARM Cortex-M4 STM32F407, especificación industrial 32-bit",
                    "cantidad": 500,
                    "precio_unitario": 12.50,
                    "precio_total": 6250.00
                },
                {
                    "descripcion": "Módulo WiFi 6E modelo AX-1200PRO con certificación FCC",
                    "cantidad": 250,
                    "precio_unitario": 18.75,
                    "precio_total": 4687.50
                }
            ],
            "precio_neto_factura": 10937.50,
            "moneda": "USD",
            "incoterm": "FOB",
            "lugar_entrega": "Puerto de Shanghai Terminal PSA",
            "descuentos": 0,
            "concepto_descuento": null,
            "gastos_transporte": 0,
            "costo_seguro": 0,
            "es_original": true,
            "es_definitiva": true
        };
        
        const blob = new Blob([JSON.stringify([ejemplo], null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'factura_ejemplo_valida.json';
        a.click();
        URL.revokeObjectURL(url);
        
        mostrarMensaje('✓ Archivo descargado correctamente', 'success');
    } catch (error) {
        mostrarError('Error: ' + error.message);
    }
}

async function cargarJSON(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const div = document.getElementById('resultados');
    div.innerHTML = `
        <div class="bg-slate-800 border border-slate-700 rounded-xl p-8 text-center">
            <i class="fas fa-spinner fa-spin text-6xl text-blue-400 mb-4"></i>
            <p class="text-xl text-gray-300">Procesando validación...</p>
        </div>
    `;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_URL}/validar-lote`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error en la validación');
        }
        
        const data = await response.json();
        mostrarResultados(data);
    } catch (error) {
        mostrarError('Error: ' + error.message);
    }
    
    event.target.value = '';
}

function mostrarResultados(data) {
    const resumen = data.resumen;
    const facturas = data.facturas;
    
    const html = `
        <!-- Resumen -->
        <div class="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-8 mb-8">
            <h2 class="text-3xl font-bold mb-6 text-blue-400">
                <i class="fas fa-chart-pie"></i> Resumen de Validación
            </h2>
            
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div class="bg-blue-900 bg-opacity-50 border border-blue-500 p-6 rounded-xl text-center">
                    <div class="text-4xl font-bold text-blue-300 mb-2">${resumen.total}</div>
                    <div class="text-sm text-gray-400">Total Facturas</div>
                </div>
                
                <div class="bg-green-900 bg-opacity-50 border border-green-500 p-6 rounded-xl text-center">
                    <div class="text-4xl font-bold text-green-300 mb-2">${resumen.aprobadas}</div>
                    <div class="text-sm text-gray-400">Aprobadas ✓</div>
                </div>
                
                <div class="bg-red-900 bg-opacity-50 border border-red-500 p-6 rounded-xl text-center">
                    <div class="text-4xl font-bold text-red-300 mb-2">${resumen.rechazadas}</div>
                    <div class="text-sm text-gray-400">Rechazadas ✗</div>
                </div>
                
                <div class="bg-purple-900 bg-opacity-50 border border-purple-500 p-6 rounded-xl text-center">
                    <div class="text-4xl font-bold text-purple-300 mb-2">${resumen.porcentaje}%</div>
                    <div class="text-sm text-gray-400">Cumplimiento</div>
                </div>
            </div>
            
            <!-- Barra de progreso -->
            <div class="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                <div class="bg-gradient-to-r from-blue-500 to-blue-400 h-2 rounded-full transition-all duration-500" 
                     style="width: ${resumen.porcentaje}%"></div>
            </div>
        </div>
        
        <!-- Resultados detallados -->
        <div class="space-y-4">
            <h3 class="text-2xl font-bold text-blue-400 mb-4">
                <i class="fas fa-list"></i> Detalle de Facturas
            </h3>
            ${facturas.map(factura => crearTarjetaFactura(factura)).join('')}
        </div>
    `;
    
    document.getElementById('resultados').innerHTML = html;
    document.getElementById('resultados').scrollIntoView({ behavior: 'smooth' });
}

function crearTarjetaFactura(factura) {
    const cumple = factura.resultado.cumple;
    const estado = cumple ? 'CUMPLE ✓' : 'NO CUMPLE ✗';
    
    const borderClass = cumple ? 'border-green-500 bg-green-900 bg-opacity-30' : 'border-red-500 bg-red-900 bg-opacity-30';
    const iconoClass = cumple ? 'text-green-400' : 'text-red-400';
    const icono = cumple ? 'fa-check-circle' : 'fa-times-circle';
    
    return `
        <div class="bg-slate-800 border-l-4 ${borderClass} rounded-lg p-6 shadow-lg">
            <!-- Header -->
            <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-3">
                    <i class="fas ${icono} text-2xl ${iconoClass}"></i>
                    <div>
                        <h3 class="text-xl font-bold text-gray-100">${factura.factura_numero}</h3>
                        <span class="inline-block px-3 py-1 rounded-full text-xs font-semibold mt-1 ${
                            cumple ? 'bg-green-500 bg-opacity-30 text-green-300' : 'bg-red-500 bg-opacity-30 text-red-300'
                        }">
                            ${estado}
                        </span>
                    </div>
                </div>
                <div class="text-right text-sm text-gray-400">
                    <p><strong>Errores:</strong> ${factura.resultado.errores.length}</p>
                    <p><strong>Advertencias:</strong> ${factura.resultado.advertencias.length}</p>
                </div>
            </div>
            
            <!-- Errores -->
            ${factura.resultado.errores.length > 0 ? `
                <div class="mb-4 bg-red-900 bg-opacity-40 border-l-4 border-red-500 p-4 rounded">
                    <h4 class="font-bold text-red-300 mb-2 flex items-center gap-2">
                        <i class="fas fa-exclamation-triangle"></i>
                        Errores Críticos (${factura.resultado.errores.length})
                    </h4>
                    <ul class="space-y-2">
                        ${factura.resultado.errores.map(error => `
                            <li class="text-sm text-gray-300">
                                <strong class="text-red-300">${error.campo}:</strong>
                                <span>${error.mensaje}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}
            
            <!-- Advertencias -->
            ${factura.resultado.advertencias.length > 0 ? `
                <div class="mb-4 bg-yellow-900 bg-opacity-40 border-l-4 border-yellow-500 p-4 rounded">
                    <h4 class="font-bold text-yellow-300 mb-2 flex items-center gap-2">
                        <i class="fas fa-info-circle"></i>
                        Advertencias (${factura.resultado.advertencias.length})
                    </h4>
                    <ul class="space-y-2">
                        ${factura.resultado.advertencias.map(adv => `
                            <li class="text-sm text-gray-300">
                                <strong class="text-yellow-300">${adv.campo}:</strong>
                                <span>${adv.mensaje}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}
            
            <!-- Sugerencias -->
            ${factura.resultado.sugerencias.length > 0 ? `
                <div class="bg-blue-900 bg-opacity-40 border-l-4 border-blue-500 p-4 rounded">
                    <h4 class="font-bold text-blue-300 mb-2 flex items-center gap-2">
                        <i class="fas fa-lightbulb"></i>
                        Acciones Sugeridas (${factura.resultado.sugerencias.length})
                    </h4>
                    <ul class="space-y-2">
                        ${factura.resultado.sugerencias.map(sugerencia => `
                            <li class="text-sm text-gray-300 flex items-start gap-2">
                                <i class="fas fa-arrow-right text-blue-400 mt-0.5"></i>
                                <span>${sugerencia}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
}

function mostrarError(mensaje) {
    document.getElementById('resultados').innerHTML = `
        <div class="bg-red-900 bg-opacity-50 border-l-4 border-red-500 rounded-lg p-6 shadow-lg">
            <div class="flex items-center gap-3">
                <i class="fas fa-exclamation-circle text-red-400 text-3xl"></i>
                <div>
                    <h3 class="font-bold text-red-300 text-lg">Error de Validación</h3>
                    <p class="text-red-200 text-sm">${mensaje}</p>
                </div>
            </div>
        </div>
    `;
}

function mostrarMensaje(mensaje, tipo = 'info') {
    const colores = {
        success: { bg: 'bg-green-900', border: 'border-green-500', text: 'text-green-300' },
        error: { bg: 'bg-red-900', border: 'border-red-500', text: 'text-red-300' },
        info: { bg: 'bg-blue-900', border: 'border-blue-500', text: 'text-blue-300' }
    };
    const color = colores[tipo] || colores.info;
    
    const div = document.createElement('div');
    div.className = `fixed top-4 right-4 ${color.bg} bg-opacity-50 border-l-4 ${color.border} ${color.text} p-4 rounded-lg shadow-xl z-50 animate-pulse max-w-sm`;
    div.innerHTML = `
        <div class="flex items-center gap-3">
            <i class="fas fa-info-circle"></i>
            <p class="font-semibold text-sm">${mensaje}</p>
        </div>
    `;
    document.body.appendChild(div);
    
    setTimeout(() => div.remove(), 3000);
}
