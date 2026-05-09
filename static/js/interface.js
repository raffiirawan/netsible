/**
 * NETSIBLE — Interface (Port) Visualization
 */
document.addEventListener('DOMContentLoaded', () => {
    const chassis = document.getElementById('router-chassis');
    if (!chassis) return;
    const deviceId = chassis.dataset.deviceId;

    document.getElementById('btn-refresh-ports')?.addEventListener('click', refreshPorts);

    function refreshPorts() {
        fetch(`/monitoring/api/${deviceId}/realtime`)
            .then(r => r.json())
            .then(d => {
                if (!d.port_status) return;
                Object.entries(d.port_status).forEach(([port, status]) => {
                    const el = document.getElementById('port-' + port);
                    if (!el) return;
                    el.className = 'port port-' + status;
                });
            }).catch(() => {});
    }

    refreshPorts();
});
