import random
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from services.mikrotik_api import MikrotikAPIClient
from models.device import Device

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')


@monitoring_bp.route('/<int:device_id>')
@login_required
def detail(device_id):
    """Monitoring detail page for a specific device."""
    device = Device.query.get_or_404(device_id)
    return render_template('monitoring/detail.html', device=device)


@monitoring_bp.route('/<int:device_id>/interface')
@login_required
def interface_view(device_id):
    """Interface (port) visualization page."""
    device = Device.query.get_or_404(device_id)
    return render_template('monitoring/interface.html', device=device)


@monitoring_bp.route('/api/<int:device_id>/realtime')
@login_required
def get_realtime_data(device_id):
    # 1. Cari IP Mikrotik dari database
    device = Device.query.get_or_404(device_id)
    
    # 2. Buka koneksi API ke Mikrotik tersebut
    # (Asumsi user Mikrotik bawaan GNS3 adalah 'admin' tanpa password)
    api_client = MikrotikAPIClient(host=device.ip_address, username='admin', password='')
    
    # 3. Sedot datanya
    resource_data = api_client.get_system_resource()
    api_client.disconnect() # Tutup koneksi biar enteng

    # 4. Kirim ke web UI (Pastikan nama 'cpu' dan 'memory' sesuai dengan yang diminta JavaScript temanmu)
    return jsonify({
        'cpu': resource_data.get('cpu-load', 0),
        'memory': resource_data.get('free-memory', 0),
        'uptime': resource_data.get('uptime', 'Offline'),
        # Traffic interface sementara biarkan 0 atau random dulu sampai kita buat fungsinya
        'tx_rate': 0, 
        'rx_rate': 0
    })
