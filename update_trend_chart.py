import os
import re

html_path = r'app\ui\app.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

trend_html = """            </div>
        </div>

        <div class="mt-8 glass-panel-premium p-6 rounded-3xl min-h-[400px] flex flex-col">
            <h3 class="text-lg font-medium text-cream tracking-wide mb-6 font-headline">Tendencia de Evaluaciones (Últimos 14 días)</h3>
            <div id="chartTrend" class="flex-1 w-full flex items-center justify-center"></div>
        </div>
    </div> 
    
    
    <div id="config-view" """

if "Tendencia de Evaluaciones" not in html:
    html = html.replace("""            </div>
        </div>
    </div> 
    
    
    <div id="config-view" """, trend_html)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated app.html")

js_path = r'app\ui\app.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

old_chart_js = """                dataLabels: { enabled: true, style: { colors: ['#f5f5dc'] } },
                plotOptions: {
                    pie: {
                        donut: { size: '65%' }
                    }
                },
                legend: { position: 'bottom', labels: { colors: '#e0e4db' } }
            };
            chartDecisionsInstance = new ApexCharts(document.querySelector("#chartDecisions"), options);
            chartDecisionsInstance.render();

        } catch (e) {
            console.error(e);
        }
    }"""

new_chart_js = """                dataLabels: { enabled: true, style: { colors: ['#f5f5dc'] } },
                plotOptions: {
                    pie: {
                        donut: { size: '65%' }
                    }
                },
                legend: { position: 'bottom', labels: { colors: '#e0e4db' } }
            };
            chartDecisionsInstance = new ApexCharts(document.querySelector("#chartDecisions"), options);
            chartDecisionsInstance.render();

            // Trend Chart
            if (window.chartTrendInstance) {
                window.chartTrendInstance.destroy();
            }
            
            // Format dates simply if available
            const datesFormatted = data.history_dates ? data.history_dates.map(d => {
                const parts = d.split('-');
                if(parts.length===3) return `${parts[2]}/${parts[1]}`;
                return d;
            }) : [];
            
            const trendOptions = {
                series: [{
                    name: 'Aprobados',
                    data: data.history_aprobados || []
                }, {
                    name: 'Rechazados',
                    data: data.history_rechazados || []
                }],
                chart: {
                    type: 'area',
                    height: 320,
                    background: 'transparent',
                    toolbar: { show: false },
                    animations: { enabled: true, easing: 'easeinout', speed: 800 }
                },
                colors: ['#398a48', '#d65d5d'],
                fill: {
                    type: 'gradient',
                    gradient: {
                        shadeIntensity: 1,
                        opacityFrom: 0.4,
                        opacityTo: 0.05,
                        stops: [0, 90, 100]
                    }
                },
                dataLabels: { enabled: false },
                stroke: { curve: 'smooth', width: 2 },
                xaxis: {
                    categories: datesFormatted,
                    labels: { style: { colors: '#e0e4db' } },
                    axisBorder: { show: false },
                    axisTicks: { show: false }
                },
                yaxis: {
                    labels: { style: { colors: '#e0e4db' } },
                },
                grid: {
                    borderColor: 'rgba(245, 245, 220, 0.05)',
                    strokeDashArray: 4
                },
                theme: { mode: 'dark' },
                legend: { position: 'top', horizontalAlign: 'right', labels: { colors: '#e0e4db' } }
            };
            window.chartTrendInstance = new ApexCharts(document.querySelector("#chartTrend"), trendOptions);
            window.chartTrendInstance.render();

        } catch (e) {
            console.error(e);
        }
    }"""

if "window.chartTrendInstance" not in js:
    js = js.replace(old_chart_js, new_chart_js)
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js)
    print("Updated app.js")
