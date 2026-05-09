from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from models.device import Device

network_map_bp = Blueprint('network_map', __name__, url_prefix='/network-map')


@network_map_bp.route('/')
@login_required
def index():
    """Network topology visualization page."""
    return render_template('network_map.html')


@network_map_bp.route('/api/nodes')
@login_required
def get_nodes():
    """
    Return network nodes and links for map visualization.
    Uses device data from DB + static topology for demo.
    """
    devices = Device.query.all()

    # If devices exist in DB, use them; otherwise provide demo data
    if devices:
        nodes = []
        for d in devices:
            nodes.append({
                'id': d.id,
                'name': d.name,
                'ip': d.ip_address,
                'status': d.status,
                'lat': -7.2575 + (d.id * 0.008),
                'lng': 112.7521 + (d.id * 0.005),
                'type': 'router',
            })
    else:
        # Demo topology matching the PDF visualization
        nodes = [
            {'id': 1, 'name': 'MikroTik Office', 'ip': '192.168.88.1', 'status': 'online',
             'lat': -7.2575, 'lng': 112.7521, 'type': 'central'},
            {'id': 2, 'name': 'Branch-SOL_West', 'ip': '192.168.88.10', 'status': 'online',
             'lat': -7.2700, 'lng': 112.7350, 'type': 'router'},
            {'id': 3, 'name': 'Branch-MDG', 'ip': '192.168.88.3', 'status': 'online',
             'lat': -7.2400, 'lng': 112.7400, 'type': 'router'},
            {'id': 4, 'name': 'Branch-Ban-Haitaah', 'ip': '192.168.200.1', 'status': 'online',
             'lat': -7.2350, 'lng': 112.7650, 'type': 'router'},
            {'id': 5, 'name': 'Branch-W1', 'ip': '192.168.100.2', 'status': 'online',
             'lat': -7.2750, 'lng': 112.7650, 'type': 'router'},
            {'id': 6, 'name': 'Branch-W2', 'ip': '192.168.100.3', 'status': 'offline',
             'lat': -7.2800, 'lng': 112.7550, 'type': 'router'},
            {'id': 7, 'name': 'Branch-MDN', 'ip': '192.168.88.4', 'status': 'online',
             'lat': -7.2450, 'lng': 112.7700, 'type': 'router'},
            {'id': 8, 'name': 'Branch-SUB', 'ip': '192.168.88.5', 'status': 'online',
             'lat': -7.2650, 'lng': 112.7750, 'type': 'router'},
            {'id': 9, 'name': 'Hub-South_SDA', 'ip': '192.168.89.1', 'status': 'online',
             'lat': -7.2850, 'lng': 112.7450, 'type': 'hub'},
            {'id': 10, 'name': 'Branch-SDA1', 'ip': '192.168.89.2', 'status': 'online',
             'lat': -7.2950, 'lng': 112.7350, 'type': 'router'},
            {'id': 11, 'name': 'Branch-SDA2', 'ip': '192.168.89.3', 'status': 'online',
             'lat': -7.2950, 'lng': 112.7550, 'type': 'router'},
        ]

    # Links — connect branches to central office
    links = [
        {'source': 1, 'target': 2},
        {'source': 1, 'target': 3},
        {'source': 1, 'target': 4},
        {'source': 1, 'target': 5},
        {'source': 1, 'target': 6},
        {'source': 1, 'target': 7},
        {'source': 1, 'target': 8},
        {'source': 1, 'target': 9},
        {'source': 9, 'target': 10},
        {'source': 9, 'target': 11},
    ]

    return jsonify({'nodes': nodes, 'links': links})
