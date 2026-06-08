import os
import re

html_path = r'app\ui\app.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Add Modal before closing body tag
modal_html = """
    <!-- Historical Analysis Modal -->
    <div id="analysisModal" class="fixed inset-0 z-[200] hidden">
        <div class="absolute inset-0 bg-black/80 backdrop-blur-md" onclick="closeAnalysisModal()"></div>
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-5xl bg-surface border border-cream/10 rounded-3xl p-8 shadow-2xl flex flex-col max-h-[90vh]">
            <div class="flex justify-between items-center mb-6 border-b border-cream/10 pb-4">
                <h2 class="text-2xl font-bold text-cream tracking-wide flex items-center gap-2 font-headline">
                    <span class="material-symbols-outlined text-accent">analytics</span>
                    Reporte de Análisis Crediticio
                </h2>
                <div class="flex items-center gap-4">
                    <button id="btnModalPDF" class="bg-accent/20 hover:bg-accent/30 text-accent px-4 py-2 rounded-xl border border-accent/30 transition-all flex items-center gap-2 font-bold shadow-md" type="button">
                        <span class="material-symbols-outlined text-[18px]">picture_as_pdf</span>
                        Exportar PDF
                    </button>
                    <button type="button" class="text-cream/50 hover:text-cream transition-colors" onclick="closeAnalysisModal()">
                        <span class="material-symbols-outlined text-2xl">close</span>
                    </button>
                </div>
            </div>
            
            <div id="modalExportContent" class="flex-1 overflow-y-auto pr-4 custom-scrollbar text-cream bg-surface p-2 rounded-xl">
                
                <div class="hidden" id="modalPdfHeader" style="margin-bottom: 2rem; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 1rem;">
                    <h2 style="font-size: 24px; font-weight: bold; margin-bottom: 5px;">Reporte Histórico SCOREIA</h2>
                    <p style="font-size: 12px; color: #888;">Auditoría de Inferencia de Riesgo Crediticio</p>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <!-- Data Columns -->
                    <div class="col-span-1 md:col-span-2 glass-panel-premium rounded-2xl p-6 border-l-4 border-accent">
                        <h3 class="text-xs text-cream/50 uppercase tracking-widest font-bold mb-4">Datos del Cliente y Solicitud</h3>
                        <div class="grid grid-cols-2 gap-4 text-sm" id="modalClientData">
                            <!-- Populated by JS -->
                        </div>
                    </div>
                    <!-- Result Column -->
                    <div class="col-span-1 glass-panel-premium rounded-2xl p-6 flex flex-col items-center justify-center text-center">
                        <h3 class="text-xs text-cream/50 uppercase tracking-widest font-bold mb-4">Resultado del Motor</h3>
                        <div id="modalDecisionBadge" class="px-6 py-2 rounded-full font-bold tracking-wide mb-3"></div>
                        <div class="text-4xl font-bold font-headline mb-1 text-accent" id="modalPdValue"></div>
                        <div class="text-xs text-cream/50 uppercase tracking-widest">Probabilidad de Impago</div>
                    </div>
                </div>
                
                <div class="glass-panel-premium rounded-2xl p-6">
                    <h3 class="text-sm font-medium text-cream tracking-wide mb-4 flex items-center gap-2">
                        <span class="material-symbols-outlined text-accent">waterfall_chart</span>
                        Descomposición de Factores (SHAP)
                    </h3>
                    <div id="modalShapChartContainer" class="w-full min-h-[300px] flex items-center justify-center bg-black/40 rounded-xl p-4">
                        <div id="modalShapChart" class="w-full h-full"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>"""

if "<!-- Historical Analysis Modal -->" not in html:
    html = html.replace("</body>", modal_html)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Injected Modal into app.html")

js_path = r'app\ui\app.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Refactor viewHistoricalAnalysis
old_view = """    window.viewHistoricalAnalysis = function(id) {
        const item = window.historyCache[id];
        if(!item) return;
        
        const reqData = JSON.parse(item.request_data);
        const shapData = JSON.parse(item.shap_data);
        
        latestFormData = reqData;
        
        const resultMock = {
            pd: item.pd_value,
            riesgo: item.riesgo,
            decision: item.decision,
            shap_data: shapData
        };
        
        // Switch to eval view
        setActiveNav(navEval, evalView);
        
        // Display
        displayResults(resultMock, false);
    };"""

new_view = """    window.closeAnalysisModal = function() {
        document.getElementById('analysisModal').classList.add('hidden');
    };

    window.viewHistoricalAnalysis = function(id) {
        const item = window.historyCache[id];
        if(!item) return;
        
        const reqData = JSON.parse(item.request_data);
        const shapData = JSON.parse(item.shap_data);
        
        // Populate Data
        const clientName = item.client_name || reqData.client_name || 'Sin Nombre';
        const clientId = item.client_id || reqData.client_id || 'N/A';
        
        const dateObj = new Date(item.timestamp + 'Z');
        const dateStr = dateObj.toLocaleString('es-ES', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
        
        let clientDataHtml = `
            <div><span class="text-cream/50 block text-[10px] uppercase">Nombre</span><span class="font-medium">${clientName}</span></div>
            <div><span class="text-cream/50 block text-[10px] uppercase">Cédula</span><span class="font-medium">${clientId}</span></div>
            <div><span class="text-cream/50 block text-[10px] uppercase">Monto Solicitado</span><span class="font-medium font-mono">$${Number(item.monto_solicitado).toLocaleString()}</span></div>
            <div><span class="text-cream/50 block text-[10px] uppercase">Plazo</span><span class="font-medium">${item.plazo_meses} Meses</span></div>
            <div><span class="text-cream/50 block text-[10px] uppercase">Score Buró</span><span class="font-medium">${reqData.score_buro || '--'}</span></div>
            <div><span class="text-cream/50 block text-[10px] uppercase">Ingreso Mensual</span><span class="font-medium font-mono">$${Number(reqData.ingreso_mensual || 0).toLocaleString()}</span></div>
            <div class="col-span-2 mt-2 pt-2 border-t border-cream/10"><span class="text-cream/50 block text-[10px] uppercase">Fecha de Evaluación</span><span class="font-medium">${dateStr}</span></div>
        `;
        document.getElementById('modalClientData').innerHTML = clientDataHtml;
        
        // Result
        const isApproved = item.decision === 'Aprobado';
        const badge = document.getElementById('modalDecisionBadge');
        badge.className = `px-6 py-2 rounded-full font-bold tracking-wide mb-3 ${isApproved ? 'bg-[#398a48]/20 text-[#398a48] border border-[#398a48]/30' : 'bg-error/20 text-error border border-error/30'}`;
        badge.innerText = item.decision.toUpperCase();
        
        document.getElementById('modalPdValue').innerText = (item.pd_value * 100).toFixed(1) + '%';
        
        // Show Modal
        document.getElementById('analysisModal').classList.remove('hidden');
        
        // Draw SHAP
        setTimeout(() => {
            // Re-use drawShapWaterfall by passing the target container ID
            drawShapWaterfallModal(shapData, 'modalShapChart');
        }, 100);
        
        // Setup PDF button
        document.getElementById('btnModalPDF').onclick = () => {
            const el = document.getElementById('modalExportContent');
            const pdfHeader = document.getElementById('modalPdfHeader');
            pdfHeader.classList.remove('hidden');
            
            const opt = {
                margin:       0.5,
                filename:     `Reporte_SCOREIA_Historial_${clientId}.pdf`,
                image:        { type: 'jpeg', quality: 0.98 },
                html2canvas:  { scale: 2, useCORS: true, logging: false },
                jsPDF:        { unit: 'in', format: 'a4', orientation: 'portrait' }
            };
            
            html2pdf().set(opt).from(el).save().then(() => {
                pdfHeader.classList.add('hidden');
            });
        };
    };

    function drawShapWaterfallModal(shapDict, targetId) {
        if (!shapDict || !shapDict.features) return;
        const baseValue = shapDict.expected_value || 0.05;
        const features = shapDict.features;
        
        let sortedFeatures = features.slice().sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value));
        const topFeatures = sortedFeatures.slice(0, 10);
        
        let yLabels = [];
        let xStarts = [];
        let xEnds = [];
        let textValues = [];
        let colors = [];
        let hoverTexts = [];

        let currentValue = baseValue;

        for (let i = topFeatures.length - 1; i >= 0; i--) {
            const f = topFeatures[i];
            const start = currentValue;
            const end = currentValue + f.shap_value;
            currentValue = end;

            yLabels.push(f.name);
            xStarts.push(start);
            xEnds.push(f.shap_value); 
            
            const isPositiveRisk = f.shap_value > 0;
            colors.push(isPositiveRisk ? '#ef4444' : '#398a48');
            textValues.push((f.shap_value > 0 ? '+' : '') + f.shap_value.toFixed(3));
            hoverTexts.push(`Valor original: ${f.original_value}`);
        }

        const trace = {
            type: 'waterfall',
            orientation: 'h',
            measure: Array(topFeatures.length).fill('relative'),
            y: yLabels,
            x: xEnds,
            base: baseValue,
            textposition: "outside",
            text: textValues,
            hoverinfo: "y+text+name",
            hovertext: hoverTexts,
            name: "Impacto",
            decreasing: { marker: { color: '#398a48' } },
            increasing: { marker: { color: '#ef4444' } },
            connector: { line: { color: 'rgba(255,255,255,0.1)', width: 1, dash: 'dot' } }
        };

        const layout = {
            margin: { l: 150, r: 40, t: 20, b: 40 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#e5e7eb', family: 'Inter, sans-serif' },
            xaxis: {
                title: 'Probabilidad Base vs Final',
                gridcolor: 'rgba(255,255,255,0.1)',
                zerolinecolor: 'rgba(255,255,255,0.2)',
                tickformat: '.2%'
            },
            yaxis: {
                gridcolor: 'rgba(255,255,255,0.05)'
            },
            showlegend: false
        };

        Plotly.newPlot(targetId, [trace], layout, {responsive: true, displayModeBar: false});
    }"""

if old_view in js:
    js = js.replace(old_view, new_view)
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js)
    print("Updated app.js")
else:
    print("Error: Could not find old viewHistoricalAnalysis function")
