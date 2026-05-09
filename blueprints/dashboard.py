from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from models.device import Device
from models.ip_address import IPAddress
from extensions import db

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='')


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard with summary cards and IP management."""
    total_devices = Device.query.count()
    online_devices = Device.query.filter_by(status='online').count()
    error_devices = Device.query.filter_by(status='offline').count()
    ip_addresses = IPAddress.query.all()

    return render_template('dashboard.html',
                           total_devices=total_devices,
                           online_devices=online_devices,
                           error_devices=error_devices,
                           ip_addresses=ip_addresses)


# ----- IP Address CRUD API -----

@dashboard_bp.route('/api/ip', methods=['POST'])
@login_required
def add_ip():
    """Add a new IP address entry."""
    data = request.get_json()
    ip = IPAddress(
        address=data.get('address', ''),
        network=data.get('network', ''),
        interface=data.get('interface', ''),
        setting=data.get('setting', ''),
        device_id=data.get('device_id'),
    )
    db.session.add(ip)
    db.session.commit()
    return jsonify(ip.to_dict()), 201


@dashboard_bp.route('/api/ip/<int:ip_id>', methods=['PUT'])
@login_required
def update_ip(ip_id):
    """Update an existing IP address entry."""
    ip = IPAddress.query.get_or_404(ip_id)
    data = request.get_json()
    ip.address = data.get('address', ip.address)
    ip.network = data.get('network', ip.network)
    ip.interface = data.get('interface', ip.interface)
    ip.setting = data.get('setting', ip.setting)
    db.session.commit()
    return jsonify(ip.to_dict())


@dashboard_bp.route('/api/ip/<int:ip_id>', methods=['DELETE'])
@login_required
def delete_ip(ip_id):
    """Delete an IP address entry."""
    ip = IPAddress.query.get_or_404(ip_id)
    db.session.delete(ip)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200
