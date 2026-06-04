document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('evaluationForm');
    const btnFillDummy = document.getElementById('btnFillDummy');
    const btnCalculate = document.getElementById('btn-evaluar');
    const evaluarText = document.getElementById('evaluar-text');
    const evaluarIcon = document.getElementById('evaluar-icon');
    
    // Results elements
    const emptyState = document.getElementById('empty-state');
    const resultsContent = document.getElementById('results-content');
    
    const pdValue = document.getElementById('pdValue');
    const pdGauge = document.getElementById('pdGauge');
    const riskBadge = document.getElementById('riskBadge');
    const decisionText = document.getElementById('decisionText');
    const shapImage = document.getElementById('shapImage');
    const shapPlaceholder = document.getElementById('shapPlaceholder');

    // Pre-fill with dummy data for testing
    btnFillDummy.addEventListener('click', () => {
        const dummyData = {
            client_id: "C-10023",
            edad: 35,
            estado_civil: "Casado",
            nivel_educativo: "Universidad",
            tipo_vivienda: "Propia",
            ingreso_mensual: 4500.00,
            antiguedad_laboral: 60,
            tipo_contrato: "Indefinido",
            score_buro: 720,
            tipo_prestamo: "Personal",
            monto_solicitado: 15000.00,
            plazo_meses: 36,
            meses_mora_maxima: 0,
            num_creditos_activos: 2,
            consultas_buro_6m: 1,
            ratio_deuda_ingreso: 0.30,
            utilizacion_credito: 0.45
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
        evaluarIcon.classList.add('hidden');
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

        try {
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

        } catch (error) {
            console.error('Error:', error);
            alert('Ocurrió un error al evaluar el riesgo: ' + error.message);
            emptyState.classList.remove('hidden');
        } finally {
            // Restore button
            evaluarText.innerHTML = originalText;
            evaluarIcon.classList.remove('hidden');
            btnCalculate.disabled = false;
            btnCalculate.classList.remove('opacity-80');
        }
    });

    function displayResults(data) {
        // Unhide results
        resultsContent.classList.remove('hidden');
        resultsContent.classList.add('flex', 'animate-in', 'fade-in', 'slide-in-from-bottom-4', 'duration-700');
        
        // Update PD
        const pdPercent = (data.pd * 100).toFixed(1);
        pdValue.textContent = `${pdPercent}%`;
        
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

        // Update SHAP Image
        if (data.shap_image_b64) {
            shapImage.src = `data:image/png;base64,${data.shap_image_b64}`;
            shapImage.classList.remove('hidden');
            shapPlaceholder.classList.add('hidden');
        } else {
            shapImage.classList.add('hidden');
            shapPlaceholder.classList.remove('hidden');
        }
    }
});
