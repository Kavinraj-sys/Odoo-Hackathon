document.addEventListener('DOMContentLoaded', function() {
    // Dashboard Charts
    const utilChart = document.getElementById('utilChart');
    if (utilChart) {
        new Chart(utilChart, {
            type: 'doughnut',
            data: {
                labels: ['Available', 'Allocated', 'Maintenance'],
                datasets: [{
                    data: [45, 35, 12],
                    backgroundColor: ['#22c55e', '#eab308', '#f97316'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    // Maintenance Chart (Reports page)
    const maintChart = document.getElementById('maintChart');
    if (maintChart) {
        new Chart(maintChart, {
            type: 'bar',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Maintenance Requests',
                    data: [8, 12, 5, 15, 9, 11],
                    backgroundColor: '#a855f7'
                }]
            },
            options: {
                responsive: true,
                scales: { y: { beginAtZero: true } }
            }
        });
    }

    console.log('%cAssetFlow Frontend Loaded ✅', 'color: #a855f7; font-weight: bold');
});