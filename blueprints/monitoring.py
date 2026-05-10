import random
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
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
def realtime_data(device_id):
    """
    Real-time monitoring data endpoint.
    Returns simulated data for scaffolding; replace with actual
    RouterOS API / Ansible data in production.
    """
    device = Device.query.get_or_404(device_id)
    
    # Determine port configuration based on device model
    model = device.model or 'RB750GR3'
    
    # Default port status for different models
    if 'CCR1009' in model:
        # CCR1009: 7 Gigabit + 1 SFP+
        port_status = {
            'wan': 'connected',
            'ether1': 'connected',
            'ether2': 'connected',
            'ether3': 'connected',
            'ether4': 'disconnected',
            'ether5': 'disconnected',
            'ether6': 'disconnected',
            'ether7': 'disconnected',
            'sfp-sfpplus1': 'disconnected',
        }
        interfaces = [
            {'name': f'ether{i}', 
             'tx_rate': f'{random.randint(100, 9999)} kbps',
             'rx_rate': f'{random.randint(100, 9999)} kbps',
             'tx_bytes': f'{random.randint(1, 500)} MB',
             'rx_bytes': f'{random.randint(1, 500)} MB'}
            for i in range(1, 8)
        ]
    elif 'cAP' in model or 'AP' in model.upper():
        # Wireless AP: 1 Ethernet + 2 WLAN
        port_status = {
            'ether1': 'connected',
            'wlan1': 'connected',
            'wlan2': 'connected',
        }
        interfaces = [
            {'name': 'ether1', 
             'tx_rate': f'{random.randint(100, 5000)} kbps',
             'rx_rate': f'{random.randint(100, 5000)} kbps',
             'tx_bytes': f'{random.randint(1, 200)} MB',
             'rx_bytes': f'{random.randint(1, 200)} MB'},
            {'name': 'wlan1 (2.4GHz)', 
             'tx_rate': f'{random.randint(500, 15000)} kbps',
             'rx_rate': f'{random.randint(500, 15000)} kbps',
             'tx_bytes': f'{random.randint(50, 1000)} MB',
             'rx_bytes': f'{random.randint(50, 1000)} MB'},
            {'name': 'wlan2 (5GHz)', 
             'tx_rate': f'{random.randint(1000, 30000)} kbps',
             'rx_rate': f'{random.randint(1000, 30000)} kbps',
             'tx_bytes': f'{random.randint(100, 2000)} MB',
             'rx_bytes': f'{random.randint(100, 2000)} MB'},
        ]
    elif 'hEX S' in model:
        # hEX S: 5 Ethernet + 1 SFP
        port_status = {
            'wan': 'connected',
            'ether1': 'connected',
            'ether2': 'connected',
            'ether3': 'disabled',
            'ether4': 'disconnected',
            'ether5': 'disconnected',
            'sfp1': 'disconnected',
        }
        interfaces = [
            {'name': f'ether{i}', 
             'tx_rate': f'{random.randint(100, 9999)} kbps',
             'rx_rate': f'{random.randint(100, 9999)} kbps',
             'tx_bytes': f'{random.randint(1, 500)} MB',
             'rx_bytes': f'{random.randint(1, 500)} MB'}
            for i in range(1, 6)
        ]
    else:
        # Default (RB750GR3, hEX, etc): 5 Ethernet ports
        port_status = {
            'wan': 'connected',
            'ether1': 'connected',
            'ether2': 'connected',
            'ether3': 'disabled',
            'ether4': 'disconnected',
            'ether5': 'disconnected',
        }
        interfaces = [
            {'name': f'ether{i}', 
             'tx_rate': f'{random.randint(100, 9999)} kbps',
             'rx_rate': f'{random.randint(100, 9999)} kbps',
             'tx_bytes': f'{random.randint(1, 500)} MB',
             'rx_bytes': f'{random.randint(1, 500)} MB'}
            for i in range(1, 6)
        ]

    # Simulated real-time data for demo purposes
    data = {
        'device_id': device.id,
        'device_name': device.name,
        'uptime': device.uptime or '10d 4h 30m',
        'routeros_version': device.routeros_version or '7.15.2',
        'model': device.model or 'RB750GR3',
        'cpu_load': random.randint(10, 60),
        'memory_used': random.randint(150, 400),
        'memory_total': 512,
        'temperature': random.randint(25, 50),
        'disk_used': random.randint(20, 80),
        'disk_total': 128,
        'total_users': random.randint(1, 20),
        'active_connections': random.randint(5, 50),
        'interfaces': interfaces,
        'port_status': port_status,
    }
    return jsonify(data)
