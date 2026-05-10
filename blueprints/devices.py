from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from models.device import Device
from models.ip_address import IPAddress
from extensions import db

devices_bp = Blueprint('devices', __name__, url_prefix='/devices')


@devices_bp.route('/')
@login_required
def device_list():
    """IP Address Management page."""
    ip_addresses = IPAddress.query.all()
    devices = Device.query.order_by(Device.name).all()
    return render_template('devices/list.html', ip_addresses=ip_addresses, devices=devices)


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


# ──────────────────────────────────────────────────────────────────────
# FASE 2 — Connectivity & Sync endpoints
# ──────────────────────────────────────────────────────────────────────

@devices_bp.route('/<int:device_id>/test', methods=['POST'])
@login_required
def test_device_connectivity(device_id):
    """
    Test connectivity to a device via RouterOS API.
    Updates device.status in DB based on result.

    Response JSON:
    { "success": bool, "message": str, "latency_ms": int,
      "board": str, "version": str, "method": "api" }
    """
    device = Device.query.get_or_404(device_id)

    from services.mikrotik_api import MikrotikAPIClient
    client = MikrotikAPIClient(device.ip_address, 'admin', '')
    result = client.test_connection()

    # Update status in DB
    try:
        device.status = 'online' if result['success'] else 'offline'
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify({**result, 'device_id': device.id, 'method': 'api'})


@devices_bp.route('/<int:device_id>/test-ssh', methods=['POST'])
@login_required
def test_device_ssh(device_id):
    """
    Test SSH connectivity to a device.
    Useful as fallback when RouterOS API is disabled.

    Response JSON:
    { "success": bool, "message": str, "latency_ms": int, "method": "ssh" }
    """
    device = Device.query.get_or_404(device_id)

    from services.ssh_client import test_ssh
    result = test_ssh(device.ip_address, 'admin', '', port=22)

    try:
        if result['success']:
            device.status = 'online'
            db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify({**result, 'device_id': device.id, 'method': 'ssh'})


@devices_bp.route('/<int:device_id>/sync', methods=['POST'])
@login_required
def sync_device_info(device_id):
    """
    Pull live info from the router via RouterOS API and update DB fields:
    model, serial_number, mac_address, routeros_version, status, uptime.

    Response JSON:
    { "success": bool, "message": str, "device": {...} }
    """
    device = Device.query.get_or_404(device_id)

    from services.mikrotik_api import MikrotikAPIClient

    client = MikrotikAPIClient(device.ip_address, 'admin', '')
    resource = client.get_system_resource()
    interfaces = client.get_interfaces()
    client.disconnect()

    if not resource.get('success'):
        return jsonify({
            'success': False,
            'message': f'Cannot reach {device.ip_address} via RouterOS API',
            'device': device.to_dict(),
        }), 503

    # Update device fields
    try:
        if resource.get('board_name'):
            device.model = resource['board_name']
        if resource.get('version'):
            device.routeros_version = resource['version']
        if resource.get('uptime'):
            device.uptime = resource['uptime']
        device.status = 'online'

        # Get MAC from ether1 if available
        ether1 = next((i for i in interfaces if i['name'] == 'ether1'), None)
        if ether1 and ether1.get('mac_address'):
            device.mac_address = ether1['mac_address']

        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(exc)}), 500

    return jsonify({
        'success': True,
        'message': f'Device {device.name} synced successfully',
        'device': device.to_dict(),
    })


@devices_bp.route('/bulk-test', methods=['POST'])
@login_required
def bulk_test_connectivity():
    """
    Test connectivity for multiple devices concurrently.

    Request JSON:
        { "device_ids": [1, 2, 3] }
        or omit device_ids to test ALL devices.

    Response JSON:
        { "results": [ {device_id, device_name, success, latency_ms}, ... ] }
    """
    import concurrent.futures
    from services.mikrotik_api import MikrotikAPIClient

    data = request.get_json() or {}
    device_ids = data.get('device_ids', None)

    if device_ids:
        devices = Device.query.filter(Device.id.in_(device_ids)).all()
    else:
        devices = Device.query.all()

    def _test_one(dev):
        client = MikrotikAPIClient(dev.ip_address, 'admin', '')
        res = client.test_connection()
        # Update DB status
        try:
            dev.status = 'online' if res['success'] else 'offline'
            db.session.commit()
        except Exception:
            db.session.rollback()
        return {
            'device_id': dev.id,
            'device_name': dev.name,
            'ip_address': dev.ip_address,
            'success': res['success'],
            'latency_ms': res.get('latency_ms', 0),
            'message': res.get('message', ''),
        }

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_test_one, dev): dev for dev in devices}
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                dev = futures[future]
                results.append({
                    'device_id': dev.id,
                    'device_name': dev.name,
                    'ip_address': dev.ip_address,
                    'success': False,
                    'latency_ms': 0,
                    'message': str(exc),
                })

    return jsonify({
        'total': len(results),
        'online': sum(1 for r in results if r['success']),
        'offline': sum(1 for r in results if not r['success']),
        'results': results,
    })
