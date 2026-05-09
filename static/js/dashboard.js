/**
 * NETSIBLE — Dashboard JavaScript
 * IP Address CRUD operations
 */
document.addEventListener('DOMContentLoaded', () => {
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
