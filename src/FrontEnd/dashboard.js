window.onload = function() {
    const canvas = document.getElementById('followersChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['4/15/2026', '4/16/2026', '4/17/2026', '4/18/2026', '4/19/2026', '4/20/2026', '4/21/2026'],
            datasets: [{
                data: [17800, 18200, 18900, 18700, 19100, 18950, 19200],
                borderColor: '#4daf4f',
                borderWidth: 3,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#fff',
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#888' } },
                x: { grid: { display: false }, ticks: { color: '#888' } }
            }
        }
    });
};