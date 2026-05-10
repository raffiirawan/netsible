/**
 * NETSIBLE — IP Management JavaScript
 * IP Address CRUD operations
 */
document.addEventListener('DOMContentLoaded', () => {
    // ========== IP ADDRESS MANAGEMENT ==========
    
    // Add IP form
    const addIpForm = document.getElementById('add-ip-form');
    if (addIpForm) {
        addIpForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const deviceId = document.getElementById('ip-device').value;
            const data = {
                address: document.getElementById('ip-address').value,
                network: document.getElementById('ip-network').value,
                interface: document.getElementById('ip-interface').value,
                setting: document.getElementById('ip-setting').value,
                device_id: deviceId ? parseInt(deviceId) : null,
            };
            try {
                await apiFetch('/api/ip', {
                    method: 'POST', 
                    body: JSON.stringify(data)
                });
                location.reload();
            } catch (err) { 
                alert('Gagal menambahkan IP: ' + err.message); 
            }
        });
    }

    // Edit IP button - load data into modal
    document.querySelectorAll('.btn-edit-ip').forEach(btn => {
        btn.addEventListener('click', async () => {
            const id = btn.dataset.id;
            try {
                const ip = await apiFetch(`/api/ip/${id}`);
                
                // Populate edit form
                document.getElementById('edit-ip-id').value = ip.id;
                document.getElementById('edit-ip-address').value = ip.address;
                document.getElementById('edit-ip-network').value = ip.network || '';
                document.getElementById('edit-ip-interface').value = ip.interface || '';
                document.getElementById('edit-ip-setting').value = ip.setting || 'Static';
                document.getElementById('edit-ip-device').value = ip.device_id || '';
                
                // Show modal
                const editModal = new bootstrap.Modal(document.getElementById('editIpModal'));
                editModal.show();
            } catch (err) { 
                alert('Gagal memuat data IP: ' + err.message); 
            }
        });
    });

    // Edit IP form submit
    const editIpForm = document.getElementById('edit-ip-form');
    if (editIpForm) {
        editIpForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = document.getElementById('edit-ip-id').value;
            const deviceId = document.getElementById('edit-ip-device').value;
            const data = {
                address: document.getElementById('edit-ip-address').value,
                network: document.getElementById('edit-ip-network').value,
                interface: document.getElementById('edit-ip-interface').value,
                setting: document.getElementById('edit-ip-setting').value,
                device_id: deviceId ? parseInt(deviceId) : null,
            };
            try {
                await apiFetch(`/api/ip/${id}`, { 
                    method: 'PUT', 
                    body: JSON.stringify(data) 
                });
                location.reload();
            } catch (err) { 
                alert('Gagal mengupdate IP: ' + err.message); 
            }
        });
    }

    // Delete IP
    document.querySelectorAll('.btn-delete-ip').forEach(btn => {
        btn.addEventListener('click', async () => {
            if (!confirm('Hapus IP address ini?')) return;
            try {
                await apiFetch(`/api/ip/${btn.dataset.id}`, { method: 'DELETE' });
                btn.closest('tr').remove();
            } catch (err) { 
                alert('Gagal menghapus IP: ' + err.message); 
            }
        });
    });
});
