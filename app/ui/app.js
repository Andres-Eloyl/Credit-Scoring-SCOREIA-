document.addEventListener('DOMContentLoaded', () => {

    // --- LOGIN / REGISTRO ---
    const loginOverlay = document.getElementById('loginOverlay');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const loginNameInput = document.getElementById('loginName');
    const loginPassInput = document.getElementById('loginPass');
    const regNameInput = document.getElementById('regName');
    const regPassInput = document.getElementById('regPass');
    const regPassConfirm = document.getElementById('regPassConfirm');
    const loginError = document.getElementById('loginError');
    const regError = document.getElementById('regError');
    const welcomeUser = document.getElementById('welcomeUser');
    const btnShowRegister = document.getElementById('btnShowRegister');
    const btnShowLogin = document.getElementById('btnShowLogin');
    const loginPanel = document.getElementById('loginPanel');
    const registerPanel = document.getElementById('registerPanel');
    
    const storedUser = localStorage.getItem('scoreia_user');
    if (storedUser) {
        loginOverlay.classList.add('hidden');
        if (welcomeUser) welcomeUser.innerText = storedUser;
    }

    // Toggle entre Login y Registro
    if (btnShowRegister) {
        btnShowRegister.addEventListener('click', () => {
            loginPanel.classList.add('hidden');
            registerPanel.classList.remove('hidden');
        });
    }
    if (btnShowLogin) {
        btnShowLogin.addEventListener('click', () => {
            registerPanel.classList.add('hidden');
            loginPanel.classList.remove('hidden');
        });
    }

    // Registro
    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const name = regNameInput.value.trim();
            const pass = regPassInput.value;
            const passC = regPassConfirm.value;
            if (name.length < 2 || pass.length < 4) {
                regError.innerText = 'Nombre (min 2) y contraseña (min 4 caracteres).';
                regError.classList.remove('hidden');
                return;
            }
            if (pass !== passC) {
                regError.innerText = 'Las contraseñas no coinciden.';
                regError.classList.remove('hidden');
                return;
            }
            // Guardar credenciales
            localStorage.setItem('scoreia_user', name);
            localStorage.setItem('scoreia_pass', pass);
            // Iniciar sesión directo
            loginOverlay.classList.add('hidden');
            if (welcomeUser) welcomeUser.innerText = name;
        });
    }

    // Inicio de Sesión
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const name = loginNameInput.value.trim();
            const pass = loginPassInput.value;
            const savedName = localStorage.getItem('scoreia_user');
            const savedPass = localStorage.getItem('scoreia_pass');
            if (name === savedName && pass === savedPass) {
                loginOverlay.classList.add('hidden');
                if (welcomeUser) welcomeUser.innerText = name;
            } else {
                loginError.innerText = 'Credenciales incorrectas.';
                loginError.classList.remove('hidden');
            }
        });
    }

    // --- SHAP LABEL MAP ---
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
    
    // Results elements
    const emptyState = document.getElementById('empty-state');
    const resultsContent = document.getElementById('results-content');
    
    const pdValue = document.getElementById('pdValue');
    const pdGauge = document.getElementById('pdGauge');
    const riskBadge = document.getElementById('riskBadge');
    const decisionText = document.getElementById('decisionText');
    const shapChartContainer = document.getElementById('shapChartContainer');
    const shapChart = document.getElementById('shapChart');
    const shapPlaceholder = document.getElementById('shapPlaceholder');
    
    // History elements
    const historyTableBody = document.getElementById('historyTableBody');
    const historyEmpty = document.getElementById('historyEmpty');
    const btnHistory = document.getElementById('btnHistory');
    
    // PDF elements
    const btnDownloadPDF = document.getElementById('btnDownloadPDF');
    const pdfHeader = document.getElementById('pdfHeader');
    const pdfDate = document.getElementById('pdfDate');
    const pdfClientId = document.getElementById('pdfClientId');
    
    // Navigation & Views
    const navEval = document.getElementById('nav-eval');
    const navDashboard = document.getElementById('nav-dashboard');
    const navConfig = document.getElementById('nav-config');
    const evalView = document.getElementById('eval-view');
    const dashboardView = document.getElementById('dashboard-view');
    const configView = document.getElementById('config-view');
    let chartDecisionsInstance = null;
    
    // Config Elements
    const btnThemeDark = document.getElementById('btn-theme-dark');
    const btnThemeLight = document.getElementById('btn-theme-light');
    const colorBtns = document.querySelectorAll('.color-btn');
    const riskThresholdSlider = document.getElementById('riskThresholdSlider');
    const thresholdValueText = document.getElementById('thresholdValueText');
    const btnSaveConfig = document.getElementById('btnSaveConfig');
    
    // Global Config State
    let currentConfig = {
        theme: localStorage.getItem('theme') || 'dark',
        accentColor: localStorage.getItem('accentColor') || '#398a48',
        riskThreshold: parseFloat(localStorage.getItem('riskThreshold')) || 60
    };
    
    // Simulator elements
    const simMonto = document.getElementById('simMonto');
    const simMontoText = document.getElementById('simMontoText');
    const simPlazo = document.getElementById('simPlazo');
    const simPlazoText = document.getElementById('simPlazoText');
    
    let latestFormData = null;
    let simTimeout = null;

    const randomItem = (arr) => arr[Math.floor(Math.random() * arr.length)];
    function getRandomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    // --- History Logic ---
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
                const tr = document.createElement('tr');
                const isApproved = item.decision === 'Aprobado';
                const dateObj = new Date(item.timestamp + 'Z'); // parse UTC
                const dateStr = dateObj.toLocaleString('es-ES', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
                
                tr.innerHTML = `
                    <td class="py-4 text-xs">${dateStr}</td>
                    <td class="py-4 font-bold">$${Number(item.monto_solicitado).toLocaleString()}</td>
                    <td class="py-4">${item.plazo_meses}m</td>
                    <td class="py-4 text-center font-bold ${isApproved ? 'text-accent' : 'text-error'}">${(item.pd_value * 100).toFixed(1)}%</td>
                    <td class="py-4 text-center">
                        <span class="px-3 py-1 rounded-full text-[10px] font-bold ${isApproved ? 'bg-accent/20 text-accent' : 'bg-error/20 text-error'}">
                            ${item.decision}
                        </span>
                    </td>
                `;
                historyTableBody.appendChild(tr);
            });
        } catch (err) {
            console.error("Error fetching history:", err);
        }
    }
    
    // Initial fetch
    fetchHistory();

    // --- Navigation Logic ---
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');

    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('hidden');
            if (!sidebar.classList.contains('hidden')) {
                sidebar.classList.remove('md:flex');
                sidebar.classList.add('flex', 'w-full', 'z-50', 'bg-[#0a0e0a]');
            } else {
                sidebar.classList.remove('flex', 'w-full', 'z-50');
                sidebar.classList.add('md:flex');
            }
        });
    }

    function setActiveNav(activeNav, activeView) {
        [navEval, navDashboard, navConfig].forEach(nav => {
            if (!nav) return;
            if (nav === activeNav) {
                nav.classList.add('nav-item-active', 'text-accent');
                nav.classList.remove('text-cream/50');
            } else {
                nav.classList.remove('nav-item-active', 'text-accent');
                nav.classList.add('text-cream/50');
            }
        });
        
        [evalView, dashboardView, configView].forEach(view => {
            if (!view) return;
            if (view === activeView) {
                view.classList.remove('hidden');
            } else {
                view.classList.add('hidden');
            }
        });

        // Close sidebar on mobile after clicking
        if (window.innerWidth < 768 && sidebar && !sidebar.classList.contains('hidden')) {
            sidebar.classList.add('hidden');
            sidebar.classList.remove('flex', 'w-full', 'z-50');
            sidebar.classList.add('md:flex');
        }
    }

    if (navEval && navDashboard && navConfig) {
        navEval.addEventListener('click', () => setActiveNav(navEval, evalView));
        navDashboard.addEventListener('click', () => {
            setActiveNav(navDashboard, dashboardView);
            fetchStats();
        });
        navConfig.addEventListener('click', () => {
            setActiveNav(navConfig, configView);
            syncConfigUI();
        });
    }

    // --- Dashboard Logic ---
    async function fetchStats() {
        try {
            const res = await fetch('/api/stats');
            if (!res.ok) return;
            const data = await res.json();
            
            // Update KPIs
            document.getElementById('kpi-total').innerText = data.total;
            const pctAprobados = data.total > 0 ? ((data.aprobados / data.total) * 100).toFixed(1) : 0;
            const pctRechazados = data.total > 0 ? ((data.rechazados / data.total) * 100).toFixed(1) : 0;
            document.getElementById('kpi-aprobados').innerText = pctAprobados + '%';
            document.getElementById('kpi-rechazados').innerText = pctRechazados + '%';
            document.getElementById('kpi-monto').innerText = formatCurrency(data.monto_total);
            
            // Update PD Circle
            const pdPct = data.pd_promedio * 100;
            document.getElementById('kpi-pd-text').innerText = pdPct.toFixed(1) + '%';
            const offset = 552.92 - (552.92 * pdPct) / 100;
            document.getElementById('kpi-pd-circle').style.strokeDashoffset = offset;
            
            // Update Chart
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

    // --- PDF Logic ---
    btnDownloadPDF.addEventListener('click', () => {
        if (!latestFormData) return;
        
        // Prepare DOM for printing
        const element = document.getElementById('results-container');
        
        // Hide UI elements we don't want in PDF
        btnDownloadPDF.classList.add('hidden');
        
        // Show PDF header and fill data
        pdfHeader.classList.remove('hidden');
        pdfHeader.classList.add('flex');
        pdfDate.innerText = new Date().toLocaleString('es-ES', { dateStyle: 'long', timeStyle: 'short' });
        pdfClientId.innerText = latestFormData.client_id || 'N/A';
        
        // Configure html2pdf
        const opt = {
            margin:       0.5,
            filename:     'Reporte_SCOREIA_' + (latestFormData.client_id || 'Cliente') + '.pdf',
            image:        { type: 'jpeg', quality: 0.98 },
            html2canvas:  { scale: 2, useCORS: true, backgroundColor: '#1e211d' }, // match surface color
            jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
        };
        
        // Generate PDF
        html2pdf().set(opt).from(element).save().then(() => {
            // Restore UI
            btnDownloadPDF.classList.remove('hidden');
            pdfHeader.classList.add('hidden');
            pdfHeader.classList.remove('flex');
        });
    });

    // --- Config Logic ---
    function applyThemeConfig() {
        if (currentConfig.theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        
        // Color — inject with max specificity to beat Tailwind CDN
        let styleTag = document.getElementById('dynamic-accent-style');
        if (!styleTag) {
            styleTag = document.createElement('style');
            styleTag.id = 'dynamic-accent-style';
            document.head.appendChild(styleTag);
        }
        const c = currentConfig.accentColor;
        styleTag.innerHTML = 
            'html body .bg-accent, html body .bg-accent\\/20 { background-color: ' + c + ' !important; }' +
            'html body .text-accent { color: ' + c + ' !important; }' +
            'html body .border-accent { border-color: ' + c + ' !important; }' +
            'html body .accent-accent { accent-color: ' + c + ' !important; }' +
            'html body .fill-accent { fill: ' + c + ' !important; }' +
            'html body .shadow-accent\\/20 { --tw-shadow-color: ' + c + '33 !important; }' +
            'html body .nav-item-active { border-left-color: ' + c + ' !important; background: linear-gradient(90deg, ' + c + '26 0%, transparent 100%) !important; }' +
            ':root { --forest-green: ' + c + ' !important; }' +
            'html body .bg-accent\\/10 { background-color: ' + c + '1a !important; }' +
            'html body .bg-accent\\/20 { background-color: ' + c + '33 !important; }' +
            'html body .border-accent\\/20 { border-color: ' + c + '33 !important; }' +
            'html body .border-accent\\/30 { border-color: ' + c + '4d !important; }' +
            'html body .text-accent\\/80 { color: ' + c + 'cc !important; }';
    }
    
    function syncConfigUI() {
        // Slider
        riskThresholdSlider.value = currentConfig.riskThreshold;
        thresholdValueText.innerText = currentConfig.riskThreshold + '%';
        
        // Buttons Theme
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
    
    // Apply on load
    applyThemeConfig();
    
    // Listeners
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
                // remove ring from all
                colorBtns.forEach(b => b.classList.remove('ring-2', 'ring-white', 'ring-offset-2', 'ring-offset-[#1e211d]'));
                // add ring to clicked
                e.target.classList.add('ring-2', 'ring-white', 'ring-offset-2', 'ring-offset-[#1e211d]');
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

    // --- Simulator Logic ---
    function formatCurrency(val) {
        return "$" + Number(val).toLocaleString('en-US');
    }

    function handleSimChange() {
        simMontoText.innerText = formatCurrency(simMonto.value);
        simPlazoText.innerText = simPlazo.value + " Meses";
        
        // Sync with original form visually
        document.getElementById('monto_solicitado').value = simMonto.value;
        document.getElementById('plazo_meses').value = simPlazo.value;

        // Debounce API call
        if (simTimeout) clearTimeout(simTimeout);
        simTimeout = setTimeout(async () => {
            if (!latestFormData) return;
            
            // Create simulated data
            const simData = { ...latestFormData };
            simData.monto_solicitado = Number(simMonto.value);
            simData.plazo_meses = Number(simPlazo.value);
            
            try {
                // Add a visual cue that it's loading
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

    // Pre-fill with dummy data for testing
    btnFillDummy.addEventListener('click', () => {
        const dummyData = {
            client_id: "C-" + randomInt(10000, 99999),
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

    // Handle Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Show loading state
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
        
        // Gather data
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Convert number fields to correct types
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

        // Clear previous validations
        document.querySelectorAll('.premium-input-container').forEach(el => {
            el.classList.remove('!border-error', '!bg-error/10');
        });
        
        // Basic Validation
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
            // Restore button
            evaluarText.innerHTML = originalText;
            btnCalculate.disabled = false;
            btnCalculate.classList.remove('opacity-80');
        }
    });

    function displayResults(data, isSimulation = false) {
        // Unhide results
        resultsContent.classList.remove('hidden');
        btnDownloadPDF.classList.remove('hidden'); // Show PDF button
        
        if (!isSimulation) {
            resultsContent.classList.add('flex', 'animate-in', 'fade-in', 'slide-in-from-bottom-4', 'duration-700');
        } else {
            resultsContent.classList.add('flex');
        }
        
        // Initialize Simulator on first run
        if (!isSimulation && latestFormData) {
            simMonto.disabled = false;
            simPlazo.disabled = false;
            
            simMonto.value = latestFormData.monto_solicitado;
            simMontoText.innerText = "$" + Number(latestFormData.monto_solicitado).toLocaleString('en-US');
            
            simPlazo.value = latestFormData.plazo_meses;
            simPlazoText.innerText = latestFormData.plazo_meses + " Meses";
        }
        
        // Update PD with animation
        const targetPdPercent = data.pd * 100;
        animateValue(pdValue, 0, targetPdPercent, 1000, "%");
        
        // Gauge colors based on risk
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

        // Animate gauge
        setTimeout(() => {
            const degrees = (data.pd * 360).toFixed(0);
            pdGauge.style.background = `conic-gradient(from -90deg at 50% 50%, ${color} 0deg, ${color} ${degrees}deg, transparent ${degrees}deg, transparent 360deg)`;
        }, 100);

        // Update Risk Segment Badge
        riskBadge.textContent = `RIESGO ${data.riesgo.toUpperCase()}`;
        riskBadge.className = 'px-6 py-2 rounded-full font-bold text-sm tracking-wide border'; 
        
        if (data.riesgo === 'Bajo') {
            riskBadge.classList.add('bg-accent/20', 'text-accent', 'border-accent/30');
        } else if (data.riesgo === 'Medio') {
            riskBadge.classList.add('bg-[#f59e0b]/20', 'text-[#f59e0b]', 'border-[#f59e0b]/30');
        } else if (data.riesgo === 'Alto') {
            riskBadge.classList.add('bg-error/20', 'text-error', 'border-error/30');
        }

        // Update Decision
        decisionText.innerHTML = `Decisión Recomendada: <strong>${data.decision}</strong>`;
        if (data.decision === 'Aprobado') {
            decisionText.className = 'mt-4 text-sm font-semibold text-accent text-center';
        } else {
            decisionText.className = 'mt-4 text-sm font-semibold text-error text-center';
        }

        // Update SHAP Chart
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
            obj.innerHTML = (progress * (end - start) + start).toFixed(1) + suffix;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    let currentChart = null;
    function renderShapChart(shapData) {
        // Find top 10 features by absolute contribution magnitude
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

        if (currentChart) {
            currentChart.destroy();
        }
        
        currentChart = new ApexCharts(document.querySelector("#shapChart"), options);
        currentChart.render();
    }
});
