/**
 * NETSIBLE — Dashboard JavaScript
 * Device Management & IP Address CRUD operations
 */
document.addEventListener('DOMContentLoaded', () => {
    // ========== DEVICE MANAGEMENT ==========
    
    // Add device form
    const addDeviceForm = document.getElementById('add-device-form');
    if (addDeviceForm) {
        addDeviceForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                name: document.getElementById('dev-name').value,
                ip_address: document.getElementById('dev-ip').value,
                interface: document.getElementById('dev-interface').value,
                model: document.getElementById('dev-model').value,
                serial_number: document.getElementById('dev-serial').value,
            };
            try {
                await apiFetch('/devices/', { method: 'POST', body: JSON.stringify(data) });
                location.reload();
            } catch (err) { alert('Gagal menambahkan perangkat: ' + err.message); }
        });
    }

    // Edit device button - load data into modal
    document.querySelectorAll('.btn-edit-device').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = btn.dataset.id;
            try {
                const device = await apiFetch(`/devices/${id}`);
                
                // Populate edit form
                document.getElementById('edit-dev-id').value = device.id;
                document.getElementById('edit-dev-name').value = device.name;
                document.getElementById('edit-dev-ip').value = device.ip_address;
                document.getElementById('edit-dev-interface').value = device.interface;
                document.getElementById('edit-dev-model').value = device.model || '';
                document.getElementById('edit-dev-serial').value = device.serial_number || '';
                document.getElementById('edit-dev-mac').value = device.mac_address || '';
                document.getElementById('edit-dev-version').value = device.routeros_version || '';
                document.getElementById('edit-dev-status').value = device.status || 'offline';
                
                // Show modal
                const editModal = new bootstrap.Modal(document.getElementById('editDeviceModal'));
                editModal.show();
            } catch (err) { 
                alert('Gagal memuat data perangkat: ' + err.message); 
            }
        });
    });

    // Edit device form submit
    const editDeviceForm = document.getElementById('edit-device-form');
    if (editDeviceForm) {
        editDeviceForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = document.getElementById('edit-dev-id').value;
            const data = {
                name: document.getElementById('edit-dev-name').value,
                ip_address: document.getElementById('edit-dev-ip').value,
                interface: document.getElementById('edit-dev-interface').value,
                model: document.getElementById('edit-dev-model').value,
                serial_number: document.getElementById('edit-dev-serial').value,
                mac_address: document.getElementById('edit-dev-mac').value,
                routeros_version: document.getElementById('edit-dev-version').value,
                status: document.getElementById('edit-dev-status').value,
            };
            try {
                await apiFetch(`/devices/${id}`, { method: 'PUT', body: JSON.stringify(data) });
                location.reload();
            } catch (err) { alert('Gagal mengupdate perangkat: ' + err.message); }
        });
    }

    // Expand device detail
    document.querySelectorAll('.btn-detail').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = btn.dataset.id;
            const row = btn.closest('tr');
            const existing = row.nextElementSibling;
            
            // Toggle: close if already open
            if (existing && existing.classList.contains('detail-row')) {
                existing.remove(); 
                return;
            }
            
            try {
                const d = await apiFetch(`/devices/${id}`);
                const detailTr = document.createElement('tr');
                detailTr.classList.add('detail-row');
                detailTr.innerHTML = `<td colspan="5">
                    <div class="detail-card">
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                            <div><strong>Model:</strong> ${d.model || '-'}</div>
                            <div><strong>RouterOS:</strong> ${d.routeros_version || '-'}</div>
                            <div><strong>IP Address:</strong> ${d.ip_address}</div>
                            <div><strong>Serial Number:</strong> ${d.serial_number || '-'}</div>
                            <div><strong>MAC Address:</strong> ${d.mac_address || '-'}</div>
                            <div><strong>Uptime:</strong> ${d.uptime || '-'}</div>
                        </div>
                        <div style="margin-top:16px;display:flex;gap:8px">
                            <a href="/monitoring/${d.id}" class="btn-netsible btn-secondary-n btn-sm">Monitoring</a>
                            <a href="/monitoring/${d.id}/interface" class="btn-netsible btn-primary-n btn-sm">Interface</a>
                        </div>
                    </div></td>`;
                row.after(detailTr);
            } catch (err) { alert('Gagal memuat detail perangkat'); }
        });
    });

    // Delete device
    document.querySelectorAll('.btn-delete-device').forEach(btn => {
        btn.addEventListener('click', async () => {
            if (!confirm('Hapus perangkat ini?')) return;
            try {
                await apiFetch(`/devices/${btn.dataset.id}`, { method: 'DELETE' });
                location.reload();
            } catch (err) { alert('Gagal menghapus perangkat: ' + err.message); }
        });
    });

    // ========== IP ADDRESS MANAGEMENT ==========
    
    const ipTableBody = document.getElementById('ip-table-body');
    if (!ipTableBody) return;

    const addIpForm = document.getElementById('add-ip-form');
    if (addIpForm) {
        addIpForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                address: document.getElementById('ip-address').value,
                network: document.getElementById('ip-network').value,
                interface: document.getElementById('ip-interface').value,
                setting: document.getElementById('ip-setting').value,
            };
            try {
                const ip = await apiFetch('/api/ip', {
                    method: 'POST', body: JSON.stringify(data)
                });
                location.reload();
            } catch (err) { alert('Gagal menambahkan IP: ' + err.message); }
        });
    }

    ipTableBody.addEventListener('click', async (e) => {
        const btn = e.target.closest('.btn-delete-ip');
        if (!btn) return;
        if (!confirm('Hapus IP address ini?')) return;
        try {
            await apiFetch(`/api/ip/${btn.dataset.id}`, { method: 'DELETE' });
            btn.closest('tr').remove();
        } catch (err) { alert('Gagal menghapus: ' + err.message); }
    });
});
