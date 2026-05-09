/**
 * NETSIBLE — Devices JavaScript
 * Add device modal, detail expand/collapse, delete
 */
document.addEventListener('DOMContentLoaded', () => {
    // Add device form
    const addForm = document.getElementById('add-device-form');
    if (addForm) {
        addForm.addEventListener('submit', async (e) => {
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
            } catch (err) { alert('Gagal: ' + err.message); }
        });
    }

    // Expand detail
    document.querySelectorAll('.btn-detail').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = btn.dataset.id;
            const row = btn.closest('tr');
            const existing = row.nextElementSibling;
            if (existing && existing.classList.contains('detail-row')) {
                existing.remove(); return;
            }
            try {
                const d = await apiFetch(`/devices/${id}`);
                const detailTr = document.createElement('tr');
                detailTr.classList.add('detail-row');
                detailTr.innerHTML = `<td colspan="5">
                    <div class="detail-card">
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                            <div><strong>Model:</strong> ${d.model}</div>
                            <div><strong>RouterOS:</strong> ${d.routeros_version}</div>
                            <div><strong>IP Address:</strong> ${d.ip_address}</div>
                            <div><strong>Serial Number:</strong> ${d.serial_number}</div>
                            <div><strong>MAC Address:</strong> ${d.mac_address}</div>
                            <div><strong>Uptime:</strong> ${d.uptime || '-'}</div>
                        </div>
                        <div style="margin-top:16px;display:flex;gap:8px">
                            <a href="/monitoring/${d.id}" class="btn-netsible btn-secondary-n btn-sm">Monitoring</a>
                            <a href="/monitoring/${d.id}/interface" class="btn-netsible btn-primary-n btn-sm">Interface</a>
                        </div>
                    </div></td>`;
                row.after(detailTr);
            } catch (err) { alert('Gagal memuat detail'); }
        });
    });

    // Delete device
    document.querySelectorAll('.btn-delete-device').forEach(btn => {
        btn.addEventListener('click', async () => {
            if (!confirm('Hapus perangkat ini?')) return;
            try {
                await apiFetch(`/devices/${btn.dataset.id}`, { method: 'DELETE' });
                location.reload();
            } catch (err) { alert('Gagal menghapus'); }
        });
    });
});
