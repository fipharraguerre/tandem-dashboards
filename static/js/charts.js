const historyData = {{ history_data|tojson }};
console.log('Raw history data:', historyData);

const uniqueDates = [...new Set(historyData.map(item => item.datetime))].sort();
const descriptors = [...new Set(historyData.map(item => item.descriptor))].filter(d => /^(HDD:|Repo:)/.test(d));

const datasets = descriptors.map((descriptor, index) => {
    const dataPoints = uniqueDates.map(date => {
        const dataPoint = historyData.find(item => item.datetime === date && item.descriptor === descriptor);
        return dataPoint ? parseFloat(dataPoint.value) : null;
    });
    const colors = ['#FF6384','#36A2EB','#FFCE56','#4BC0C0','#9966FF','#FF9F40','#28a745','#dc3545'];
    return {
        label: descriptor,
        data: dataPoints,
        borderColor: colors[index % colors.length],
        backgroundColor: colors[index % colors.length] + '33',
        fill: false,
        tension: 0.1,
        pointRadius: 4,
        pointHoverRadius: 6,
        spanGaps: true
    };
});

const data = { labels: uniqueDates, datasets: datasets };

const options = {
    responsive: true,
    maintainAspectRatio: true,
    scales: {
        x: { type: 'category', title: { display: true, text: 'Fecha' }, ticks: { maxTicksLimit: 8 } },
        y: { type: 'linear', position: 'left', title: { display: true, text: 'Porcentaje de Uso (%)' }, min: 0, max: 100 }
    },
    plugins: {
        legend: { display: false },
        tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
                title: ctx => 'Fecha: ' + ctx[0].label,
                label: ctx => ctx.dataset.label + ': ' + ctx.parsed.y + '%'
            }
        }
    },
    interaction: { mode: 'nearest', axis: 'x', intersect: false }
};

new Chart(document.getElementById('historyChart').getContext('2d'), {
    type: 'line',
    data: data,
    options: options
});

const dailyData = historyData.filter(item => item.descriptor === "dailyResultBackups");
const dailyDataset = {
    label: 'Tasa de éxito de backups',
    data: dailyData.map(item => item.value),
    borderColor: 'green',
    pointBackgroundColor: dailyData.map(item => item.value < 1 ? 'orange' : 'green'),
    fill: false
};

new Chart(document.getElementById('anotherChart').getContext('2d'), {
    type: 'line',
    data: { labels: dailyData.map(item => item.datetime), datasets: [dailyDataset] },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
            x: { type: 'category', title: { display: true, text: 'Fecha' }, ticks: { maxTicksLimit: 4 } },
            y: { type: 'linear', position: 'left', title: { display: true, text: 'Tasa de Éxito (0-1)' }, min: 0, max: 1 }
        }
    }
});
