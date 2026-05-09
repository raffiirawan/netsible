/**
 * NETSIBLE — Monitoring real-time polling
 */
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('monitoring-container');
    if (!container) return;
    const deviceId = container.dataset.deviceId;
    if (!deviceId) return;

    function update() {
        fetch(`/monitoring/api/${deviceId}/realtime`)
            .then(r => r.json())
            .then(d => {
                setText('mon-uptime', d.uptime);
                setText('mon-ros', d.routeros_version);
                setText('mon-model', d.model);
                setText('mon-cpu', d.cpu_load + '%');
                setText('mon-mem', d.memory_used + ' MB / ' + d.memory_total + ' MB');
                setText('mon-temp', d.temperature + '°C');
                setText('mon-disk', d.disk_used + ' MB / ' + d.disk_total + ' MB');
                setText('mon-users', d.total_users);
                setText('mon-conn', d.active_connections);
                // Update interface table
                const tbody = document.getElementById('intf-table-body');
                if (tbody && d.interfaces) {
                    tbody.innerHTML = d.interfaces.map(i => `<tr>
                        <td>${i.name}</td><td>${i.tx_rate}</td><td>${i.rx_rate}</td>
                        <td>${i.tx_bytes}</td><td>${i.rx_bytes}</td></tr>`).join('');
                }
            }).catch(() => {});
    }

    function setText(id, val) {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    }

    update();
    setInterval(update, 5000);
});
