document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('evaluationForm');
    const btnFillDummy = document.getElementById('btnFillDummy');
    const btnCalculate = document.getElementById('btnCalculate');
    const loadingSpinner = document.getElementById('loadingSpinner');
    
    // Results elements
    const resultsPanel = document.getElementById('resultsPanel');
    const emptyState = resultsPanel.querySelector('.empty-state');
    const resultsContent = document.getElementById('resultsContent');
    
    const pdValue = document.getElementById('pdValue');
    const pdFill = document.getElementById('pdFill');
    const riskBadge = document.getElementById('riskBadge');
    const decisionText = document.getElementById('decisionText');
    const shapImage = document.getElementById('shapImage');

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
            monto_prestamo: 15000.00,
            plazo_prestamo: 36,
            tasa_interes: 12.5,
            deuda_total: 5000.00,
            cuota_mensual: 450.00,
            retrasos_historicos: 0,
            ratio_uso_credito: 0.35
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
        btnCalculate.disabled = true;
        loadingSpinner.classList.remove('hidden');
        emptyState.classList.add('hidden');
        resultsContent.classList.add('hidden');
        
        // Gather data
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Convert number fields to correct types
        const numberFields = [
            'edad', 'ingreso_mensual', 'antiguedad_laboral', 'score_buro',
            'monto_prestamo', 'plazo_prestamo', 'tasa_interes', 'deuda_total',
            'cuota_mensual', 'retrasos_historicos', 'ratio_uso_credito'
        ];
        
        numberFields.forEach(field => {
            if (data[field]) {
                data[field] = Number(data[field]);
            }
        });

        try {
            // Determine host (works locally and if deployed)
            const apiUrl = window.location.origin + '/api/predict';
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
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
            btnCalculate.disabled = false;
            loadingSpinner.classList.add('hidden');
        }
    });

    function displayResults(data) {
        // Unhide results
        resultsContent.classList.remove('hidden');
        
        // Update PD
        const pdPercent = (data.pd * 100).toFixed(1);
        pdValue.textContent = `${pdPercent}%`;
        
        // Animate progress bar
        setTimeout(() => {
            pdFill.style.width = `${pdPercent}%`;
            
            // Set color based on risk
            if (data.pd < 0.3) pdFill.style.backgroundColor = 'var(--success)';
            else if (data.pd < 0.6) pdFill.style.backgroundColor = 'var(--warning)';
            else pdFill.style.backgroundColor = 'var(--error)';
        }, 100);

        // Update Risk Segment Badge
        riskBadge.textContent = `Riesgo ${data.riesgo}`;
        riskBadge.className = 'risk-badge'; // Reset classes
        
        if (data.riesgo === 'Bajo') riskBadge.classList.add('badge-low');
        else if (data.riesgo === 'Medio') riskBadge.classList.add('badge-medium');
        else if (data.riesgo === 'Alto') riskBadge.classList.add('badge-high');

        // Update Decision
        decisionText.innerHTML = `Decisión Recomendada: <strong>${data.decision}</strong>`;
        if (data.decision === 'Aprobado') {
            decisionText.style.color = 'var(--success)';
        } else {
            decisionText.style.color = 'var(--error)';
        }

        // Update SHAP Image
        if (data.shap_image_b64) {
            shapImage.src = `data:image/png;base64,${data.shap_image_b64}`;
            shapImage.classList.remove('hidden');
        } else {
            shapImage.classList.add('hidden');
        }
    }
});
