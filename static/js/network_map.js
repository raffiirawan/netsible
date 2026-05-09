/**
 * NETSIBLE — Network Map (Leaflet.js)
 */
document.addEventListener('DOMContentLoaded', () => {
    const mapEl = document.getElementById('network-map');
    if (!mapEl) return;

    const map = L.map('network-map').setView([-7.2575, 112.7521], 13);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap © CARTO', maxZoom: 19,
    }).addTo(map);

    fetch('/network-map/api/nodes')
        .then(r => r.json())
        .then(data => {
            const markers = {};
            data.nodes.forEach(n => {
                const color = n.status === 'online' ? '#2ecc40' : '#e74c3c';
                const icon = L.divIcon({
                    className: 'map-node',
                    html: `<div style="background:${color};width:14px;height:14px;border-radius:50%;border:3px solid #fff;box-shadow:0 0 8px ${color}"></div>`,
                    iconSize: [20, 20], iconAnchor: [10, 10],
                });
                const m = L.marker([n.lat, n.lng], { icon })
                    .addTo(map)
                    .bindPopup(`<strong>${n.name}</strong><br>IP: ${n.ip}<br>Status: ${n.status}`);
                markers[n.id] = [n.lat, n.lng];
            });
            data.links.forEach(l => {
                const a = markers[l.source], b = markers[l.target];
                if (a && b) {
                    L.polyline([a, b], { color: '#5b9fbf', weight: 2, opacity: 0.7, dashArray: '6 4' }).addTo(map);
                }
            });
        }).catch(() => {});
});
