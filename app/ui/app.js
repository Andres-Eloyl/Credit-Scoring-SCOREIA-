document.addEventListener('DOMContentLoaded', () => {

    const welcomeUser = document.getElementById('welcomeUser');
    const storedUser = localStorage.getItem('scoreia_user');

    if (storedUser && welcomeUser) {
        welcomeUser.innerText = storedUser;
    }

    if (localStorage.getItem('accentColor') === '#f97316') {
        localStorage.setItem('accentColor', '#398a48');
    }

    let inactivityTimer;
    let logoutWarningTimer;
    const INACTIVITY_LIMIT = 10 * 60 * 1000; // 10 minutes
    const WARNING_LIMIT = 60 * 1000; // 1 minute to respond
    
    const inactivityModal = document.getElementById('inactivityModal');
    const btnExtendSession = document.getElementById('btnExtendSession');
    const btnForceLogout = document.getElementById('btnForceLogout');
    const btnLogout = document.getElementById('nav-logout');

    function performLogout() {
        localStorage.removeItem('scoreia_user');
        localStorage.removeItem('scoreia_pass');
        window.location.href = '/login';
    }

    function showInactivityWarning() {
        if (inactivityModal) {
            inactivityModal.classList.remove('hidden');
            logoutWarningTimer = setTimeout(performLogout, WARNING_LIMIT);
        }
    }

    function resetInactivityTimer() {
        clearTimeout(inactivityTimer);
        clearTimeout(logoutWarningTimer);
        if (inactivityModal) inactivityModal.classList.add('hidden');
        inactivityTimer = setTimeout(showInactivityWarning, INACTIVITY_LIMIT);
    }

    ['mousemove', 'keydown', 'click', 'scroll'].forEach(evt => {
        document.addEventListener(evt, resetInactivityTimer);
    });

    resetInactivityTimer();

    if (btnExtendSession) btnExtendSession.addEventListener('click', resetInactivityTimer);
    if (btnForceLogout) btnForceLogout.addEventListener('click', performLogout);
    if (btnLogout) btnLogout.addEventListener('click', performLogout);

    const shapLabelMap = {
        'edad': 'Edad',
        'ingreso_mensual': 'Ingreso Mensual',
        'antiguedad_laboral': 'Antigüedad Laboral',
        'score_buro': 'Puntaje Buró',
        'monto_solicitado': 'Monto Solicitado',
        'plazo_meses': 'Plazo en Meses',
        'meses_mora_maxima': 'Meses en Mora Máxima',
        'num_creditos_activos': 'Créditos Activos',
        'consultas_buro_6m': 'Consultas Buró (6m)',
        'ratio_deuda_ingreso': 'Ratio Deuda/Ingreso',
        'utilizacion_credito': 'Utilización de Crédito',
        'estado_civil': 'Estado Civil',
        'nivel_educativo': 'Nivel Educativo',
        'tipo_vivienda': 'Tipo de Vivienda',
        'tipo_contrato': 'Tipo de Contrato',
        'tipo_prestamo': 'Tipo de Préstamo'
    };

    const form = document.getElementById('evaluationForm');
    const btnFillDummy = document.getElementById('btnFillDummy');
    const btnCalculate = document.getElementById('btn-evaluar');
    const evaluarText = document.getElementById('evaluar-text');

    const emptyState = document.getElementById('empty-state');
    const resultsContent = document.getElementById('results-content');
    
    const pdValue = document.getElementById('pdValue');
    const pdGauge = document.getElementById('pdGauge');
    const riskBadge = document.getElementById('riskBadge');
    const decisionText = document.getElementById('decisionText');
    const shapChartContainer = document.getElementById('shapChartContainer');
    const shapChart = document.getElementById('shapChart');
    const shapPlaceholder = document.getElementById('shapPlaceholder');

    const historyTableBody = document.getElementById('historyTableBody');
    const historyEmpty = document.getElementById('historyEmpty');
    

    const btnDownloadPDF = document.getElementById('btnDownloadPDF');
    const pdfHeader = document.getElementById('pdfHeader');
    const pdfDate = document.getElementById('pdfDate');
    const pdfClientId = document.getElementById('pdfClientId');

    const navEval = document.getElementById('nav-eval');
    const navHistory = document.getElementById('nav-history');
    const navDashboard = document.getElementById('nav-dashboard');
    const navConfig = document.getElementById('nav-config');
    const navSupport = document.getElementById('nav-support');
    const evalView = document.getElementById('eval-view');
    const historyView = document.getElementById('history-view');
    const dashboardView = document.getElementById('dashboard-view');
    const configView = document.getElementById('config-view');
    const supportView = document.getElementById('support-view');
    let chartDecisionsInstance = null;

    const btnThemeDark = document.getElementById('btn-theme-dark');
    const btnThemeLight = document.getElementById('btn-theme-light');
    const colorBtns = document.querySelectorAll('.color-btn');
    const riskThresholdSlider = document.getElementById('riskThresholdSlider');
    const thresholdValueText = document.getElementById('thresholdValueText');
    const btnSaveConfig = document.getElementById('btnSaveConfig');

    let currentConfig = {
        theme: localStorage.getItem('theme') || 'dark',
        accentColor: localStorage.getItem('accentColor') || '#398a48',
        riskThreshold: parseFloat(localStorage.getItem('riskThreshold')) || 60
    };

    const simMonto = document.getElementById('simMonto');
    const simMontoText = document.getElementById('simMontoText');
    const simPlazo = document.getElementById('simPlazo');
    const simPlazoText = document.getElementById('simPlazoText');
    
    let latestFormData = null;
    window.historyCache = {};
    let simTimeout = null;

    const randomItem = (arr) => arr[Math.floor(Math.random() * arr.length)];
    function getRandomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

        window.closeAnalysisModal = function() {
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
            <div><span class="text-cream/50 block text-[10px] uppercase">Puntaje Crediticio</span><span class="font-medium">${reqData.score_buro || '--'}</span></div>
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
            renderShapChart(shapData, '#modalShapChart');
        }, 100);
        
        // Setup PDF button
        document.getElementById('btnModalPDF').onclick = () => {
            const el = document.getElementById('modalExportContent');
            const pdfHeader = document.getElementById('modalPdfHeader');
            pdfHeader.classList.remove('hidden');
            
            // Prevent html2canvas from cropping overflow content
            el.classList.remove('overflow-y-auto', 'flex-1');
            el.style.maxHeight = 'none';
            
            const opt = {
                margin:       0.3,
                filename:     `Reporte_SCOREIA_Historial_${clientId}.pdf`,
                image:        { type: 'jpeg', quality: 0.98 },
                html2canvas:  { scale: 1.5, useCORS: true, backgroundColor: '#1e211d', scrollY: 0 },
                jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
            };
            
            html2pdf().set(opt).from(el).save().then(() => {
                pdfHeader.classList.add('hidden');
                el.classList.add('overflow-y-auto', 'flex-1');
                el.style.maxHeight = '';
            });
        };
    };



    async function fetchHistory() {
        if (!historyTableBody) return;
        try {
            const res = await fetch(window.location.origin + '/api/history?limit=15');
            if (!res.ok) return;
            const data = await res.json();
            
            if (data.length === 0) {
                historyTableBody.innerHTML = '';
                historyEmpty.classList.remove('hidden');
                return;
            }
            
            historyEmpty.classList.add('hidden');
            historyTableBody.innerHTML = '';
            
            data.forEach(item => {
                window.historyCache[item.id] = item;
                const tr = document.createElement('tr');
                tr.className = "hover:bg-cream/5 transition-colors group";
                const isApproved = item.decision === 'Aprobado';
                const dateObj = new Date(item.timestamp + 'Z');
                const dateStr = dateObj.toLocaleString('es-ES', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
                
                tr.innerHTML = `
                    <td class="py-4 pl-4 font-medium text-cream group-hover:text-accent transition-colors">${item.client_name || 'Sin Nombre'}</td>
                    <td class="py-4 font-mono text-xs opacity-80">${item.client_id}</td>
                    <td class="py-4 text-xs opacity-60">${dateStr}</td>
                    <td class="py-4 text-center">
                        <span class="px-3 py-1 rounded-full text-[10px] font-bold ${isApproved ? 'bg-accent/20 text-accent' : 'bg-error/20 text-error'}">
                            ${item.decision}
                        </span>
                    </td>
                    <td class="py-4 pr-4 text-right">
                        <button onclick="viewHistoricalAnalysis(${item.id})" class="px-3 py-1.5 rounded bg-surface border border-cream/10 text-xs font-medium hover:border-accent hover:text-accent transition-colors">
                            Ver Análisis
                        </button>
                    </td>
                `;
                historyTableBody.appendChild(tr);
            });
        } catch (err) {
            console.error("Error fetching history:", err);
        }
    }

    fetchHistory();

    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');
    const closeSidebarBtn = document.getElementById('closeSidebarBtn');

    function toggleSidebar() {
        if (sidebar) {
            sidebar.classList.toggle('-translate-x-full');
        }
    }

    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', toggleSidebar);
    }
    
    if (closeSidebarBtn) {
        closeSidebarBtn.addEventListener('click', toggleSidebar);
    }

    function setActiveNav(activeNav, activeView) {
        [navEval, navHistory, navDashboard, navConfig, navSupport].forEach(nav => {
            if (!nav) return;
            if (nav === activeNav) {
                nav.classList.add('nav-item-active', 'text-accent');
                nav.classList.remove('text-cream/50');
            } else {
                nav.classList.remove('nav-item-active', 'text-accent');
                nav.classList.add('text-cream/50');
            }
        });
        
        [evalView, historyView, dashboardView, configView, supportView].forEach(view => {
            if (!view) return;
            if (view === activeView) {
                view.classList.remove('hidden');
            } else {
                view.classList.add('hidden');
            }
        });

        if (sidebar && !sidebar.classList.contains('-translate-x-full')) {
            sidebar.classList.add('-translate-x-full');
        }
    }

    if (navEval && navHistory && navDashboard && navConfig && navSupport) {
        navEval.addEventListener('click', () => setActiveNav(navEval, evalView));
        navHistory.addEventListener('click', () => {
            setActiveNav(navHistory, historyView);
            fetchHistory();
        });
        navDashboard.addEventListener('click', () => {
            setActiveNav(navDashboard, dashboardView);
            fetchStats();
        });
        navConfig.addEventListener('click', () => {
            setActiveNav(navConfig, configView);
            syncConfigUI();
        });
        navSupport.addEventListener('click', () => {
            setActiveNav(navSupport, supportView);
        });
    }

    async function fetchStats() {
        try {
            const res = await fetch('/api/stats');
            if (!res.ok) return;
            const data = await res.json();

            document.getElementById('kpi-total').innerText = data.total;
            const pctAprobados = data.total > 0 ? ((data.aprobados / data.total) * 100).toFixed(1) : 0;
            const pctRechazados = data.total > 0 ? ((data.rechazados / data.total) * 100).toFixed(1) : 0;
            document.getElementById('kpi-aprobados').innerText = pctAprobados + '%';
            document.getElementById('kpi-rechazados').innerText = pctRechazados + '%';
            document.getElementById('kpi-monto').innerText = formatCurrency(data.monto_total);

            const pdPct = data.pd_promedio * 100;
            document.getElementById('kpi-pd-text').innerText = pdPct.toFixed(1) + '%';
            const offset = 552.92 - (552.92 * pdPct) / 100;
            document.getElementById('kpi-pd-circle').style.strokeDashoffset = offset;

            if (chartDecisionsInstance) {
                chartDecisionsInstance.destroy();
            }
            const options = {
                series: [data.aprobados, data.rechazados],
                chart: { type: 'donut', height: 320, background: 'transparent' },
                labels: ['Aprobados', 'Rechazados'],
                colors: ['#398a48', '#d65d5d'],
                stroke: { show: false },
                dataLabels: { enabled: true, style: { colors: ['#f5f5dc'] } },
                plotOptions: {
                    pie: {
                        donut: {
                            labels: {
                                show: true,
                                name: { color: '#f5f5dc' },
                                value: { color: '#f5f5dc', fontSize: '24px', fontWeight: 'bold' }
                            }
                        }
                    }
                },
                theme: { mode: 'dark' }
            };
            chartDecisionsInstance = new ApexCharts(document.querySelector("#chartDecisions"), options);
            chartDecisionsInstance.render();
            
        } catch (err) {
            console.error("Error fetching stats:", err);
        }
    }

    btnDownloadPDF.addEventListener('click', () => {
        if (!latestFormData) return;

        const element = document.getElementById('results-container');

        btnDownloadPDF.classList.add('hidden');

        pdfHeader.classList.remove('hidden');
        pdfHeader.classList.add('flex');
        pdfDate.innerText = new Date().toLocaleString('es-ES', { dateStyle: 'long', timeStyle: 'short' });
        pdfClientId.innerText = (latestFormData.client_name ? latestFormData.client_name + ' (V-' + latestFormData.client_id + ')' : latestFormData.client_id) || 'N/A';

        const opt = {
            margin:       0.5,
            filename:     'Reporte_SCOREIA_' + (latestFormData.client_id || 'Cliente') + '.pdf',
            image:        { type: 'jpeg', quality: 0.98 },
            html2canvas:  { scale: 2, useCORS: true, backgroundColor: '#1e211d' }, // match surface color
            jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
        };

        html2pdf().set(opt).from(element).save().then(() => {

            btnDownloadPDF.classList.remove('hidden');
            pdfHeader.classList.add('hidden');
            pdfHeader.classList.remove('flex');
        });
    });

    function hexToRgb(hex) {
        var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        if(!result) return { space: '57 138 72', comma: '57, 138, 72' };
        return {
            space: parseInt(result[1], 16) + ' ' + parseInt(result[2], 16) + ' ' + parseInt(result[3], 16),
            comma: parseInt(result[1], 16) + ', ' + parseInt(result[2], 16) + ', ' + parseInt(result[3], 16)
        };
    }

    function applyThemeConfig() {
        if (currentConfig.theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }

        const c = currentConfig.accentColor;
        const rgbVals = hexToRgb(c);
        
        document.documentElement.style.setProperty('--color-accent', rgbVals.space);
        document.documentElement.style.setProperty('--color-accent-comma', rgbVals.comma);
        
        let styleTag = document.getElementById('dynamic-accent-style');
        if (styleTag) {
            styleTag.remove();
        }
    }
    
    function syncConfigUI() {

        riskThresholdSlider.value = currentConfig.riskThreshold;
        thresholdValueText.innerText = currentConfig.riskThreshold + '%';

        if (currentConfig.theme === 'dark') {
            btnThemeDark.classList.add('border-accent', 'bg-accent/20');
            btnThemeDark.classList.remove('border-cream/20', 'bg-cream/5');
            btnThemeLight.classList.remove('border-accent', 'bg-accent/20');
            btnThemeLight.classList.add('border-cream/20', 'bg-cream/5');
        } else {
            btnThemeLight.classList.add('border-accent', 'bg-accent/20');
            btnThemeLight.classList.remove('border-cream/20', 'bg-cream/5');
            btnThemeDark.classList.remove('border-accent', 'bg-accent/20');
            btnThemeDark.classList.add('border-cream/20', 'bg-cream/5');
        }
    }

    applyThemeConfig();

    if (riskThresholdSlider) {
        riskThresholdSlider.addEventListener('input', (e) => {
            thresholdValueText.innerText = e.target.value + '%';
        });
    }
    
    if (btnThemeDark) {
        btnThemeDark.addEventListener('click', () => {
            currentConfig.theme = 'dark';
            syncConfigUI();
        });
    }
    
    if (btnThemeLight) {
        btnThemeLight.addEventListener('click', () => {
            currentConfig.theme = 'light';
            syncConfigUI();
        });
    }
    
    if (colorBtns) {
        colorBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                currentConfig.accentColor = e.target.dataset.color;

                colorBtns.forEach(b => b.classList.remove('ring-2', 'ring-white', 'ring-offset-2', 'ring-offset-[#1e211d]'));

                e.target.classList.add('ring-2', 'ring-white', 'ring-offset-2', 'ring-offset-[#1e211d]');
                
                // Apply instantly without reloading or saving
                applyThemeConfig();
            });
        });
    }
    
    if (btnSaveConfig) {
        btnSaveConfig.addEventListener('click', () => {
            currentConfig.riskThreshold = parseFloat(riskThresholdSlider.value);
            localStorage.setItem('theme', currentConfig.theme);
            localStorage.setItem('accentColor', currentConfig.accentColor);
            localStorage.setItem('riskThreshold', currentConfig.riskThreshold);
            applyThemeConfig();
            
            const originalText = btnSaveConfig.innerText;
            btnSaveConfig.innerText = '¡Guardado!';
            setTimeout(() => { btnSaveConfig.innerText = originalText; }, 2000);
        });
    }

    function formatCurrency(val) {
        return "$" + Number(val).toLocaleString('en-US');
    }

    function handleSimChange() {
        simMontoText.innerText = formatCurrency(simMonto.value);
        simPlazoText.innerText = simPlazo.value + " Meses";

        document.getElementById('monto_solicitado').value = simMonto.value;
        document.getElementById('plazo_meses').value = simPlazo.value;

        if (simTimeout) clearTimeout(simTimeout);
        simTimeout = setTimeout(async () => {
            if (!latestFormData) return;

            const simData = { ...latestFormData };
            simData.monto_solicitado = Number(simMonto.value);
            simData.plazo_meses = Number(simPlazo.value);
            
            try {

                riskBadge.textContent = "SIMULANDO...";
                riskBadge.className = 'px-6 py-2 rounded-full font-bold text-sm tracking-wide border bg-surface text-cream border-cream/20 animate-pulse';
                
                const apiUrl = window.location.origin + '/api/predict';
                const riskThreshold = currentConfig ? (currentConfig.riskThreshold / 100.0) : 0.60;
                const response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ...simData, risk_threshold: riskThreshold })
                });

                if (response.ok) {
                    const result = await response.json();
                    displayResults(result, true); // true = isSimulation
                    fetchHistory(); // Update history silently
                }
            } catch (err) {
                console.error("Simulation error:", err);
            }
        }, 500); // 500ms debounce
    }

    simMonto.addEventListener('input', handleSimChange);
    simPlazo.addEventListener('input', handleSimChange);

    const randomInt = (min, max) => Math.floor(Math.random() * (max - min + 1)) + min;
    const randomFloat = (min, max, decimals = 2) => Number((Math.random() * (max - min) + min).toFixed(decimals));

    btnFillDummy.addEventListener('click', () => {
        const dummyData = {
            client_id: String(randomInt(10000000, 29999999)),
            client_name: randomItem(["Juan", "Pedro", "María", "Ana", "Luis", "Carlos", "José", "Laura", "Carmen", "David"]),
            client_lastname: randomItem(["Pérez", "Gómez", "Rodríguez", "López", "Martínez", "García", "Fernández", "González", "Díaz", "Sánchez"]),
            edad: randomInt(18, 75),
            estado_civil: randomItem(["Soltero", "Casado", "Divorciado", "Viudo"]),
            nivel_educativo: randomItem(["Primaria", "Secundaria", "Universidad", "Posgrado"]),
            tipo_vivienda: randomItem(["Propia", "Arrendada", "Familiar"]),
            ingreso_mensual: randomFloat(800, 15000),
            antiguedad_laboral: randomInt(0, 240),
            tipo_contrato: randomItem(["Indefinido", "Temporal", "Independiente"]),
            score_buro: randomInt(300, 850),
            tipo_prestamo: randomItem(["Personal", "Hipotecario", "Automotriz", "Tarjeta"]),
            monto_solicitado: randomFloat(1000, 50000),
            plazo_meses: randomItem([6, 12, 24, 36, 48, 60, 72, 84]),
            meses_mora_maxima: randomInt(0, 6),
            num_creditos_activos: randomInt(0, 5),
            consultas_buro_6m: randomInt(0, 10),
            ratio_deuda_ingreso: randomFloat(0.05, 0.60),
            utilizacion_credito: randomFloat(0, 1)
        };

        for (const [key, value] of Object.entries(dummyData)) {
            const input = document.getElementById(key);
            if (input) {
                input.value = value;
            }
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const originalText = evaluarText.innerHTML;
        evaluarText.innerHTML = `
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-cream inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Analizando Perfil...
        `;
        btnCalculate.disabled = true;
        btnCalculate.classList.add('opacity-80');
        
        emptyState.classList.add('hidden');
        resultsContent.classList.add('hidden');
        resultsContent.classList.remove('flex');

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        if (data.client_name && data.client_lastname) {
            data.client_name = data.client_name.trim() + " " + data.client_lastname.trim();
            delete data.client_lastname;
        }

        const numberFields = [
            'edad', 'ingreso_mensual', 'antiguedad_laboral', 'score_buro',
            'monto_solicitado', 'plazo_meses', 'meses_mora_maxima',
            'num_creditos_activos', 'consultas_buro_6m', 'ratio_deuda_ingreso',
            'utilizacion_credito'
        ];
        
        numberFields.forEach(field => {
            if (data[field]) {
                data[field] = Number(data[field]);
            }
        });

        document.querySelectorAll('.premium-input-container').forEach(el => {
            el.classList.remove('!border-error', '!bg-error/10');
        });

        let isValid = true;
        let errors = [];

        if (data.edad < 18 || data.edad > 100) {
            isValid = false;
            document.getElementById('edad').closest('.premium-input-container').classList.add('!border-error', '!bg-error/10');
            errors.push('La edad debe estar entre 18 y 100 años.');
        }

        if (data.monto_solicitado <= 0) {
            isValid = false;
            document.getElementById('monto_solicitado').closest('.premium-input-container').classList.add('!border-error', '!bg-error/10');
            errors.push('El monto solicitado debe ser mayor a 0.');
        }

        if (data.ingreso_mensual <= 0) {
            isValid = false;
            document.getElementById('ingreso_mensual').closest('.premium-input-container').classList.add('!border-error', '!bg-error/10');
            errors.push('El ingreso mensual debe ser mayor a 0.');
        }

        if (!isValid) {
            alert("Por favor corrija los siguientes errores:\n" + errors.join('\n'));
            evaluarText.innerHTML = originalText;
            btnCalculate.disabled = false;
            btnCalculate.classList.remove('opacity-80');
            emptyState.classList.remove('hidden');
            return;
        }

        try {
            latestFormData = data; // Store for simulator

            const riskThreshold = currentConfig ? (currentConfig.riskThreshold / 100.0) : 0.60;

            const apiUrl = window.location.origin + '/api/predict';
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...data, risk_threshold: riskThreshold })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al procesar la solicitud');
            }

            const result = await response.json();
            displayResults(result);
            fetchHistory(); // Refresh history table

        } catch (error) {
            console.error('Error:', error);
            alert('Ocurrió un error al evaluar el riesgo: ' + error.message);
            emptyState.classList.remove('hidden');
        } finally {

            evaluarText.innerHTML = originalText;
            btnCalculate.disabled = false;
            btnCalculate.classList.remove('opacity-80');
        }
    });

    function displayResults(data, isSimulation = false) {

        resultsContent.classList.remove('hidden');
        btnDownloadPDF.classList.remove('hidden'); // Show PDF button
        
        if (!isSimulation) {
            resultsContent.classList.add('flex', 'animate-in', 'fade-in', 'slide-in-from-bottom-4', 'duration-700');
        } else {
            resultsContent.classList.add('flex');
        }

        if (!isSimulation && latestFormData) {
            simMonto.disabled = false;
            simPlazo.disabled = false;
            
            simMonto.value = latestFormData.monto_solicitado;
            simMontoText.innerText = "$" + Number(latestFormData.monto_solicitado).toLocaleString('en-US');
            
            simPlazo.value = latestFormData.plazo_meses;
            simPlazoText.innerText = latestFormData.plazo_meses + " Meses";
        }

        const targetPdPercent = data.pd * 100;
        animateValue(pdValue, 0, targetPdPercent, 1000, "%");

        let color = '#398a48'; // forest-green (low risk)
        if (data.pd >= 0.6) {
            color = '#ffb4ab'; // error red (high risk)
            pdValue.className = 'text-4xl font-extrabold text-error';
        } else if (data.pd >= 0.3) {
            color = '#f59e0b'; // amber (medium risk)
            pdValue.className = 'text-4xl font-extrabold text-[#f59e0b]';
        } else {
            pdValue.className = 'text-4xl font-extrabold text-accent';
        }

        setTimeout(() => {
            const degrees = (data.pd * 360).toFixed(0);
            pdGauge.style.background = `conic-gradient(from -90deg at 50% 50%, ${color} 0deg, ${color} ${degrees}deg, transparent ${degrees}deg, transparent 360deg)`;
        }, 100);

        riskBadge.textContent = `RIESGO ${data.riesgo.toUpperCase()}`;
        riskBadge.className = 'px-6 py-2 rounded-full font-bold text-sm tracking-wide border'; 
        
        if (data.riesgo === 'Bajo') {
            riskBadge.classList.add('bg-accent/20', 'text-accent', 'border-accent/30');
        } else if (data.riesgo === 'Medio') {
            riskBadge.classList.add('bg-[#f59e0b]/20', 'text-[#f59e0b]', 'border-[#f59e0b]/30');
        } else if (data.riesgo === 'Alto') {
            riskBadge.classList.add('bg-error/20', 'text-error', 'border-error/30');
        }

        decisionText.innerHTML = `Decisión Recomendada: <strong>${data.decision}</strong>`;
        if (data.decision === 'Aprobado') {
            decisionText.className = 'mt-4 text-sm font-semibold text-accent text-center';
        } else {
            decisionText.className = 'mt-4 text-sm font-semibold text-error text-center';
        }

        if (data.shap_data) {
            shapChart.classList.remove('hidden');
            shapPlaceholder.classList.add('hidden');
            renderShapChart(data.shap_data);
        } else {
            shapChart.classList.add('hidden');
            shapPlaceholder.classList.remove('hidden');
        }
    }

    function animateValue(obj, start, end, duration, suffix) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = (progress * (end - start) + start).toFixed(1) + `<span class="text-xl md:text-2xl ml-1 text-inherit opacity-70">${suffix}</span>`;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    let currentChart = null;
    let modalChart = null;
    function renderShapChart(shapData, targetId = "#shapChart") {

        const features = shapData.features.sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution)).slice(0, 10);
        
        const seriesData = features.map(f => {
            const label = shapLabelMap[f.name] || f.name;
            return {
                x: label,
                y: Number(f.contribution.toFixed(4)),
                fillColor: f.contribution > 0 ? '#ffb4ab' : (currentConfig.accentColor || '#398a48')
            };
        });

        const options = {
            series: [{
                name: 'Impacto SHAP',
                data: seriesData
            }],
            chart: {
                type: 'bar',
                height: '100%',
                parentHeightOffset: 0,
                toolbar: { show: false },
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800,
                    animateGradually: { enabled: true, delay: 150 },
                    dynamicAnimation: { enabled: true, speed: 350 }
                }
            },
            plotOptions: {
                bar: {
                    horizontal: true,
                    borderRadius: 4
                }
            },
            dataLabels: { enabled: false },
            yaxis: {
                labels: {
                    style: {
                        colors: '#e0e4db',
                        fontSize: '11px',
                        fontFamily: 'DM Sans, sans-serif'
                    }
                }
            },
            xaxis: {
                labels: { style: { colors: '#e0e4db' } },
                title: { text: 'Contribución al riesgo', style: { color: '#e0e4db', fontFamily: 'DM Sans, sans-serif', fontSize: '11px' } }
            },
            grid: {
                borderColor: 'rgba(245, 245, 220, 0.1)',
                strokeDashArray: 4
            },
            theme: { mode: 'dark' },
            tooltip: {
                theme: 'dark',
                y: {
                    formatter: function (val) {
                        const prefix = val > 0 ? 'Incrementa riesgo: +' : 'Reduce riesgo: ';
                        return prefix + val;
                    }
                }
            }
        };

        if (targetId === "#shapChart") {
            if (currentChart) currentChart.destroy();
            currentChart = new ApexCharts(document.querySelector(targetId), options);
            currentChart.render();
        } else {
            if (modalChart) modalChart.destroy();
            modalChart = new ApexCharts(document.querySelector(targetId), options);
            modalChart.render();
        }
    }
});


    // --- Health Check & Diagnostics ---
    const motorDot = document.getElementById('motorDot');
    const motorText = document.getElementById('motorText');
    const dbDot = document.getElementById('dbDot');
    const dbText = document.getElementById('dbText');
    const btnGenerateReport = document.getElementById('btnGenerateReport');
    
    let lastHealthStatus = { motor: 'unknown', db: 'unknown' };

    async function checkHealth() {
        if (!motorDot) return;
        try {
            const res = await fetch('/api/health');
            if (res.ok) {
                const data = await res.json();
                lastHealthStatus = data;
                
                if (data.motor === 'ok') {
                    motorDot.className = "w-2 h-2 rounded-full bg-[#398a48] shadow-[0_0_8px_rgba(57,138,72,0.8)] animate-pulse";
                    motorText.className = "text-xs font-bold text-[#398a48] tracking-widest uppercase";
                    motorText.innerText = "Operativo";
                } else {
                    motorDot.className = "w-2 h-2 rounded-full bg-error shadow-[0_0_8px_rgba(239,68,68,0.8)] animate-pulse";
                    motorText.className = "text-xs font-bold text-error tracking-widest uppercase";
                    motorText.innerText = "Error";
                }
                
                if (data.db === 'ok') {
                    dbDot.className = "w-2 h-2 rounded-full bg-[#398a48] shadow-[0_0_8px_rgba(57,138,72,0.8)] animate-pulse";
                    dbText.className = "text-xs font-bold text-[#398a48] tracking-widest uppercase";
                    dbText.innerText = "En Línea";
                } else {
                    dbDot.className = "w-2 h-2 rounded-full bg-error shadow-[0_0_8px_rgba(239,68,68,0.8)] animate-pulse";
                    dbText.className = "text-xs font-bold text-error tracking-widest uppercase";
                    dbText.innerText = "Desconectada";
                }
            }
        } catch(e) {
            motorDot.className = "w-2 h-2 rounded-full bg-error shadow-[0_0_8px_rgba(239,68,68,0.8)] animate-pulse";
            motorText.className = "text-xs font-bold text-error tracking-widest uppercase";
            motorText.innerText = "Fuera de Línea";
            dbDot.className = "w-2 h-2 rounded-full bg-error shadow-[0_0_8px_rgba(239,68,68,0.8)] animate-pulse";
            dbText.className = "text-xs font-bold text-error tracking-widest uppercase";
            dbText.innerText = "Fuera de Línea";
        }
    }
    
    // Check health every 30 seconds
    setInterval(checkHealth, 30000);
    // Initial check
    setTimeout(checkHealth, 1000);

    if (btnGenerateReport) {
        btnGenerateReport.addEventListener('click', () => {
            const dateStr = new Date().toLocaleString('es-ES');
            const ua = navigator.userAgent;
            const content = `===========================================
REPORTE DE DIAGNÓSTICO SCOREIA
===========================================
Fecha de Generación : ${dateStr}
Agente de Usuario   : ${ua}
Pantalla            : ${window.innerWidth}x${window.innerHeight}

ESTADO DE SERVICIOS:
Motor Predictivo    : ${lastHealthStatus.motor.toUpperCase()}
Base de Datos       : ${lastHealthStatus.db.toUpperCase()}

Si experimenta problemas, por favor adjunte 
este archivo al contactar a soporte@scoreia.com
===========================================
`;
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Diagnostico_SCOREIA_${Date.now()}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }
