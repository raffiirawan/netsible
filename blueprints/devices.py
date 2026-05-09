from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from models.device import Device
from extensions import db

devices_bp = Blueprint('devices', __name__, url_prefix='/devices')


@devices_bp.route('/')
@login_required
def device_list():
    """List all devices."""
    devices = Device.query.order_by(Device.created_at.desc()).all()
    return render_template('devices/list.html', devices=devices)


@devices_bp.route('/', methods=['POST'])
@login_required
def add_device():
    """Add a new device (AJAX)."""
    data = request.get_json()
    device = Device(
        name=data.get('name', ''),
        ip_address=data.get('ip_address', ''),
        interface=data.get('interface', 'ether1'),
        model=data.get('model', ''),
        serial_number=data.get('serial_number', ''),
    )
    db.session.add(device)
    db.session.commit()
    return jsonify(device.to_dict()), 201


@devices_bp.route('/<int:device_id>', methods=['GET'])
@login_required
def get_device(device_id):
    """Get single device detail (JSON)."""
    device = Device.query.get_or_404(device_id)
    return jsonify(device.to_dict())


@devices_bp.route('/<int:device_id>', methods=['PUT'])
@login_required
def update_device(device_id):
    """Update device details."""
    device = Device.query.get_or_404(device_id)
    data = request.get_json()
    device.name = data.get('name', device.name)
    device.ip_address = data.get('ip_address', device.ip_address)
    device.interface = data.get('interface', device.interface)
    device.model = data.get('model', device.model)
    device.serial_number = data.get('serial_number', device.serial_number)
    device.mac_address = data.get('mac_address', device.mac_address)
    device.routeros_version = data.get('routeros_version', device.routeros_version)
    device.status = data.get('status', device.status)
    device.uptime = data.get('uptime', device.uptime)
    db.session.commit()
    return jsonify(device.to_dict())


@devices_bp.route('/<int:device_id>', methods=['DELETE'])
@login_required
def delete_device(device_id):
    """Delete a device."""
    device = Device.query.get_or_404(device_id)
    db.session.delete(device)
    db.session.commit()
    return jsonify({'message': 'Device deleted'}), 200
