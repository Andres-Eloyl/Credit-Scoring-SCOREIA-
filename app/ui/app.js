document.addEventListener('DOMContentLoaded', () => {
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
                const response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(simData)
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
            const apiUrl = window.location.origin + '/api/predict';
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
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
            return {
                x: f.name,
                y: Number(f.contribution.toFixed(4)),
                fillColor: f.contribution > 0 ? '#ffb4ab' : '#398a48'
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
                    borderRadius: 2
                }
            },
            dataLabels: { enabled: false },
            yaxis: {
                labels: {
                    style: {
                        colors: '#e0e4db',
                        fontSize: '11px',
                        fontFamily: 'Inter, sans-serif'
                    }
                }
            },
            xaxis: {
                labels: { style: { colors: '#e0e4db' } }
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
                        return val > 0 ? "+" + val : val;
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
