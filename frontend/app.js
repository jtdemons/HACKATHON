
//app.js📌 - Lógica del frontend para validación de facturas/**


// CONFIGURACIÓN

// URL de la API
const API_URL = 'http://localhost:8000';


//FUNCIONES PRINCIPALES

/**
 * 📌Muestra los requisitos legales DIAN en el UI
 */
async function verRequisitos() {
    const div = document.getElementById('requisitos');
    
    try {
        const response = await fetch(`${API_URL}/requisitos`);
        const data = await response.json();
        
        const html = `
            <div class="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-8 animate-fade-in">
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
                                <i class="fas fa-check-double"></i> ${categoria.replace(/_/g, ' ')}
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
                
                ${data.validaciones_ia && data.validaciones_ia.length > 0 ? `
                    <div class="mt-6 bg-purple-900 bg-opacity-40 border border-purple-500 p-6 rounded-lg">
                        <h3 class="font-bold text-lg mb-3 text-purple-300">
                            <i class="fas fa-robot"></i> Validaciones con Inteligencia Artificial
                        </h3>
                        <ul class="space-y-2">
                            ${data.validaciones_ia.map(validacion => `
                                <li class="flex items-start gap-2">
                                    <i class="fas fa-star text-purple-400 text-xs mt-1.5"></i>
                                    <span class="text-gray-300">${validacion}</span>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
        
        div.innerHTML = html;
        div.classList.remove('hidden');
        div.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
    } catch (error) {
        mostrarError('Error al cargar requisitos: ' + error.message);
    }
}

// 📌Descarga un archivo JSON de ejemplo para pruebas

function descargarEjemplo() {
    const ejemplo = {
        "Fields": [
            {"Fields": "Supplier", "Value": "Tech Supplies International Inc."},
            {"Fields": "Customer", "Value": "Importadora Colombiana SAS"},
            {"Fields": "SupplierAddress", "Value": "1234 Technology Ave, Silicon Valley, CA 94025, USA"},
            {"Fields": "CustomerAddress", "Value": "Calle 100 No. 10-20, Bogotá, Colombia"},
            {"Fields": "CustomerTaxID", "Value": "900123456-7"},
            {"Fields": "InvoiceNumber", "Value": "INV-2025-001234"},
            {"Fields": "InvoiceDate", "Value": "2025-11-10"},
            {"Fields": "Currency", "Value": "USD"},
            {"Fields": "Incoterm", "Value": "FOB"},
            {"Fields": "InvoiceType", "Value": "Commercial Invoice"},
            {"Fields": "PortOfLoading", "Value": "Los Angeles, CA"},
            {"Fields": "PortOfDischarge", "Value": "Cartagena, Colombia"},
            {"Fields": "CountryOfOrigin", "Value": "United States"},
            {"Fields": "TotalInvoiceValue", "Value": "15000.00"},
            {"Fields": "PaymentTerms", "Value": "NET 30"}
        ],
        "Table": [
            {
                "SKU": "TECH-001",
                "Description": "Laptop Dell Latitude 5520, Intel Core i7-1185G7, 16GB RAM, 512GB SSD, pantalla 15.6 pulgadas",
                "Quantity": "50",
                "UnitOfMeasurement": "PCS",
                "UnitPrice": "250.00",
                "NetValuePerItem": "12500.00",
                "Currency": "USD",
                "HSCode": "8471.30.01.00",
                "Weight": "2.5 kg"
            },
            {
                "SKU": "TECH-002",
                "Description": "Mouse inalámbrico Logitech MX Master 3, ergonómico, bluetooth, color grafito",
                "Quantity": "100",
                "UnitOfMeasurement": "PCS",
                "UnitPrice": "25.00",
                "NetValuePerItem": "2500.00",
                "Currency": "USD",
                "HSCode": "8471.60.60.00",
                "Weight": "0.15 kg"
            }
        ]
    };
    
    try {
        const blob = new Blob([JSON.stringify([ejemplo], null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'factura_ejemplo_valida.json';
        a.click();
        URL.revokeObjectURL(url);
        
        mostrarMensaje('✅ Archivo de ejemplo descargado', 'success');
    } catch (error) {
        mostrarError('Error al descargar ejemplo: ' + error.message);
    }
}



async function cargarJSON(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const div = document.getElementById('resultados');
    
    // 📌Mostrar indicador de carga
    div.innerHTML = `
        <div class="bg-slate-800 border border-slate-700 rounded-xl p-8 text-center">
            <i class="fas fa-spinner fa-spin text-6xl text-blue-400 mb-4"></i>
            <p class="text-xl text-gray-300 mb-2">Procesando validación...</p>
            <p class="text-sm text-gray-500">Analizando facturas con IA 🤖</p>
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
    
    // Limpiar input file
    event.target.value = '';
}



function mostrarResultados(data) {
    const resumen = data.resumen;
    const facturas = data.facturas;
    const usaIA = data.ia_utilizada;
    
    const html = `
        <!-- Banner de IA -->
        ${usaIA ? `
            <div class="bg-gradient-to-r from-purple-900 to-purple-800 border-l-4 border-purple-400 rounded-lg p-4 mb-6 shadow-lg">
                <div class="flex items-center gap-3">
                    <i class="fas fa-robot text-3xl text-purple-300"></i>
                    <div>
                        <p class="font-bold text-white">Validación potenciada con Gemini AI</p>
                        <p class="text-sm text-purple-200">Análisis inteligente y sugerencias contextuales activadas</p>
                    </div>
                </div>
            </div>
        ` : ''}
        
        <!-- Resumen -->
        <div class="bg-slate-800 border border-slate-700 rounded-xl shadow-xl p-8 mb-8">
            <h2 class="text-3xl font-bold mb-6 text-blue-400">
                <i class="fas fa-chart-pie"></i> Resumen de Validación
            </h2>
            
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div class="bg-blue-900 bg-opacity-50 border border-blue-500 p-6 rounded-xl text-center transform hover:scale-105 transition-transform">
                    <div class="text-5xl font-bold text-blue-300 mb-2">${resumen.total}</div>
                    <div class="text-sm text-gray-400">Total Facturas</div>
                </div>
                
                <div class="bg-green-900 bg-opacity-50 border border-green-500 p-6 rounded-xl text-center transform hover:scale-105 transition-transform">
                    <div class="text-5xl font-bold text-green-300 mb-2">${resumen.aprobadas}</div>
                    <div class="text-sm text-gray-400">Aprobadas ✓</div>
                </div>
                
                <div class="bg-red-900 bg-opacity-50 border border-red-500 p-6 rounded-xl text-center transform hover:scale-105 transition-transform">
                    <div class="text-5xl font-bold text-red-300 mb-2">${resumen.rechazadas}</div>
                    <div class="text-sm text-gray-400">Rechazadas ✗</div>
                </div>
                
                <div class="bg-purple-900 bg-opacity-50 border border-purple-500 p-6 rounded-xl text-center transform hover:scale-105 transition-transform">
                    <div class="text-5xl font-bold text-purple-300 mb-2">${resumen.porcentaje}%</div>
                    <div class="text-sm text-gray-400">Cumplimiento</div>
                </div>
            </div>
            
            <!-- Barra de progreso -->
            <div class="w-full bg-slate-700 rounded-full h-3 overflow-hidden mb-4">
                <div class="bg-gradient-to-r from-blue-500 via-purple-500 to-blue-400 h-3 rounded-full transition-all duration-1000 animate-pulse" 
                     style="width: ${resumen.porcentaje}%"></div>
            </div>
            
            <p class="text-center text-lg font-semibold ${resumen.rechazadas === 0 ? 'text-green-400' : 'text-yellow-400'}">
                ${resumen.estado}
            </p>
        </div>
        
        <!-- Resultados detallados -->
        <div class="space-y-4">
            <h3 class="text-2xl font-bold text-blue-400 mb-4 flex items-center gap-2">
                <i class="fas fa-list"></i> 
                Detalle de Facturas
            </h3>
            ${facturas.map((factura, idx) => crearTarjetaFactura(factura, idx)).join('')}
        </div>
    `;
    
    document.getElementById('resultados').innerHTML = html;
    document.getElementById('resultados').scrollIntoView({ behavior: 'smooth' });
}



function crearTarjetaFactura(factura, indice) {
    const cumple = factura.resultado.cumple;
    const resultado = factura.resultado;
    
    const borderClass = cumple 
        ? 'border-green-500 bg-green-900 bg-opacity-20' 
        : 'border-red-500 bg-red-900 bg-opacity-20';
    
    const iconoClass = cumple ? 'text-green-400' : 'text-red-400';
    const icono = cumple ? 'fa-check-circle' : 'fa-times-circle';
    const estadoTexto = cumple ? 'CUMPLE ✓' : 'NO CUMPLE ✗';
    
    return `
        <div class="bg-slate-800 border-l-4 ${borderClass} rounded-lg p-6 shadow-lg hover:shadow-xl transition-shadow">
            <!-- Header -->
            <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-3">
                    <i class="fas ${icono} text-3xl ${iconoClass}"></i>
                    <div>
                        <h3 class="text-xl font-bold text-gray-100">
                            Factura #${indice + 1}: ${factura.factura_numero || 'Sin número'}
                        </h3>
                        <span class="inline-block px-3 py-1 rounded-full text-xs font-semibold mt-1 ${
                            cumple 
                                ? 'bg-green-500 bg-opacity-30 text-green-300' 
                                : 'bg-red-500 bg-opacity-30 text-red-300'
                        }">
                            ${estadoTexto}
                        </span>
                    </div>
                </div>
                <div class="text-right text-sm text-gray-400">
                    <p><strong>Errores:</strong> <span class="text-red-400 font-bold">${resultado.errores.length}</span></p>
                    <p><strong>Advertencias:</strong> <span class="text-yellow-400 font-bold">${resultado.advertencias.length}</span></p>
                </div>
            </div>
            
            <!-- Errores críticos -->
            ${resultado.errores.length > 0 ? `
                <div class="mb-4 bg-red-900 bg-opacity-40 border-l-4 border-red-500 p-4 rounded">
                    <h4 class="font-bold text-red-300 mb-2 flex items-center gap-2">
                        <i class="fas fa-exclamation-triangle"></i>
                        Errores Críticos (${resultado.errores.length})
                    </h4>
                    <ul class="space-y-2">
                        ${resultado.errores.map(error => `
                            <li class="text-sm text-gray-200">
                                <strong class="text-red-300">${error.campo}:</strong>
                                <span>${error.mensaje}</span>
                                ${error.codigo ? `<code class="ml-2 px-2 py-1 bg-red-950 rounded text-xs">${error.codigo}</code>` : ''}
                            </li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}
            
            <!-- Advertencias -->
            ${resultado.advertencias.length > 0 ? `
                <div class="mb-4 bg-yellow-900 bg-opacity-40 border-l-4 border-yellow-500 p-4 rounded">
                    <h4 class="font-bold text-yellow-300 mb-2 flex items-center gap-2">
                        <i class="fas fa-info-circle"></i>
                        Advertencias (${resultado.advertencias.length})
                    </h4>
                    <ul class="space-y-2">
                        ${resultado.advertencias.map(adv => `
                            <li class="text-sm text-gray-200">
                                <strong class="text-yellow-300">${adv.campo}:</strong>
                                <span>${adv.mensaje}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}
            
            <!-- Sugerencias -->
            ${resultado.sugerencias.length > 0 ? `
                <div class="mb-4 bg-blue-900 bg-opacity-40 border-l-4 border-blue-500 p-4 rounded">
                    <h4 class="font-bold text-blue-300 mb-2 flex items-center gap-2">
                        <i class="fas fa-lightbulb"></i>
                        Acciones Sugeridas (${resultado.sugerencias.length})
                    </h4>
                    <ul class="space-y-2">
                        ${resultado.sugerencias.map(sugerencia => `
                            <li class="text-sm text-gray-200 flex items-start gap-2">
                                <i class="fas fa-arrow-right text-blue-400 mt-0.5"></i>
                                <span>${sugerencia}</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}
            
            <!-- Análisis con IA -->
            ${resultado.validacion_ia ? `
                <div class="bg-purple-900 bg-opacity-40 border-l-4 border-purple-500 p-4 rounded">
                    <h4 class="font-bold text-purple-300 mb-2 flex items-center gap-2">
                        <i class="fas fa-robot"></i>
                        Análisis con Inteligencia Artificial
                    </h4>
                    <p class="text-sm text-gray-200 mb-2">
                        <strong>Coherencia general:</strong> 
                        ${resultado.validacion_ia.coherente === true 
                            ? '<span class="text-green-400">✅ Coherente</span>' 
                            : resultado.validacion_ia.coherente === false
                                ? '<span class="text-yellow-400">⚠️ Posibles inconsistencias</span>'
                                : '<span class="text-gray-400">⚙️ No analizado</span>'}
                    </p>
                    ${resultado.validacion_ia.problemas_detectados && resultado.validacion_ia.problemas_detectados.length > 0 ? `
                        <div class="mt-2">
                            <p class="text-sm font-semibold text-purple-300 mb-1">Problemas detectados por IA:</p>
                            <ul class="list-disc list-inside text-sm text-gray-200 space-y-1">
                                ${resultado.validacion_ia.problemas_detectados.map(p => `<li>${p}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            ` : ''}
        </div>
    `;
}


// ==================== FUNCIONES AUXILIARES ====================

/**
 * Muestra un mensaje de error en el UI
 */
function mostrarError(mensaje) {
    document.getElementById('resultados').innerHTML = `
        <div class="bg-red-900 bg-opacity-50 border-l-4 border-red-500 rounded-lg p-6 shadow-lg">
            <div class="flex items-center gap-3">
                <i class="fas fa-exclamation-circle text-red-400 text-4xl"></i>
                <div>
                    <h3 class="font-bold text-red-300 text-lg">Error de Validación</h3>
                    <p class="text-red-200 text-sm mt-1">${mensaje}</p>
                </div>
            </div>
        </div>
    `;
}


/**
 * Muestra un mensaje toast temporal
 */
function mostrarMensaje(mensaje, tipo = 'info') {
    const colores = {
        success: { bg: 'bg-green-900', border: 'border-green-500', text: 'text-green-300', icono: 'check-circle' },
        error: { bg: 'bg-red-900', border: 'border-red-500', text: 'text-red-300', icono: 'times-circle' },
        info: { bg: 'bg-blue-900', border: 'border-blue-500', text: 'text-blue-300', icono: 'info-circle' }
    };
    
    const color = colores[tipo] || colores.info;
    
    const div = document.createElement('div');
    div.className = `fixed top-4 right-4 ${color.bg} bg-opacity-90 border-l-4 ${color.border} ${color.text} p-4 rounded-lg shadow-2xl z-50 max-w-sm animate-slide-in`;
    div.innerHTML = `
        <div class="flex items-center gap-3">
            <i class="fas fa-${color.icono} text-xl"></i>
            <p class="font-semibold text-sm">${mensaje}</p>
        </div>
    `;
    
    document.body.appendChild(div);
    
    setTimeout(() => {
        div.classList.add('animate-slide-out');
        setTimeout(() => div.remove(), 300);
    }, 3000);
}


// ==================== ESTILOS CSS ADICIONALES ====================

const style = document.createElement('style');
style.textContent = `
    @keyframes slide-in {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slide-out {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    @keyframes fade-in {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .animate-slide-in {
        animation: slide-in 0.3s ease-out;
    }
    
    .animate-slide-out {
        animation: slide-out 0.3s ease-in;
    }
    
    .animate-fade-in {
        animation: fade-in 0.5s ease-out;
    }
`;
document.head.appendChild(style);
