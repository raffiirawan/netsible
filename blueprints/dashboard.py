from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from models.device import Device
from models.ip_address import IPAddress
from extensions import db

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='')


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard with summary cards, device management, and IP management."""
    total_devices = Device.query.count()
    online_devices = Device.query.filter_by(status='online').count()
    error_devices = Device.query.filter_by(status='offline').count()
    devices = Device.query.order_by(Device.created_at.desc()).all()
    ip_addresses = IPAddress.query.all()

    return render_template('dashboard.html',
                           total_devices=total_devices,
                           online_devices=online_devices,
                           error_devices=error_devices,
                           devices=devices,
                           ip_addresses=ip_addresses)


# ----- IP Address CRUD API -----

@dashboard_bp.route('/api/ip/<int:ip_id>', methods=['GET'])
@login_required
def get_ip(ip_id):
    """Get single IP address detail (JSON)."""
    ip = IPAddress.query.get_or_404(ip_id)
    return jsonify(ip.to_dict())


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


# ──────────────────────────────────────────────────────────────────────
# FASE 2 — Dashboard real-time API
# ──────────────────────────────────────────────────────────────────────

@dashboard_bp.route('/api/dashboard/summary')
@login_required
def dashboard_summary():
    """
    Return live summary counts for the dashboard cards.

    Response JSON:
    {
        "total"   : int,
        "online"  : int,
        "offline" : int,
        "total_ips": int,
        "recent_history_count": int   # monitoring snapshots in last 24h
    }
    """
    from datetime import datetime, timezone, timedelta
    from models.monitoring_history import MonitoringHistory

    total = Device.query.count()
    online = Device.query.filter_by(status='online').count()
    offline = Device.query.filter_by(status='offline').count()
    total_ips = IPAddress.query.count()

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    history_count = MonitoringHistory.query.filter(
        MonitoringHistory.recorded_at >= since
    ).count()

    return jsonify({
        'total': total,
        'online': online,
        'offline': offline,
        'total_ips': total_ips,
        'recent_history_count': history_count,
    })


@dashboard_bp.route('/api/devices/status')
@login_required
def all_devices_status():
    """
    Return quick status list for all devices — used by dashboard table polling.

    Response JSON:
    {
        "devices": [
            { "id", "name", "ip_address", "status", "uptime", "model", "version" },
            ...
        ]
    }
    """
    devices = Device.query.order_by(Device.name).all()
    return jsonify({
        'devices': [
            {
                'id': d.id,
                'name': d.name,
                'ip_address': d.ip_address,
                'status': d.status,
                'uptime': d.uptime,
                'model': d.model,
                'routeros_version': d.routeros_version,
                'mac_address': d.mac_address,
            }
            for d in devices
        ]
    })


@dashboard_bp.route('/api/monitoring/overview')
@login_required
def monitoring_overview():
    """
    Return the latest monitoring snapshot for EVERY device.
    Useful for the dashboard overview cards / sparklines.

    Response JSON:
    {
        "snapshots": [
            {
                "device_id", "device_name", "cpu_load",
                "memory_percent", "disk_used", "temperature",
                "active_connections", "uptime_raw", "recorded_at"
            }, ...
        ]
    }
    """
    from models.monitoring_history import MonitoringHistory
    from sqlalchemy import func

    # Subquery: latest recorded_at per device
    latest_subq = (
        db.session.query(
            MonitoringHistory.device_id,
            func.max(MonitoringHistory.recorded_at).label('max_at'),
        )
        .group_by(MonitoringHistory.device_id)
        .subquery()
    )

    # Join back to get full rows
    latest_records = (
        db.session.query(MonitoringHistory, Device.name)
        .join(
            latest_subq,
            (MonitoringHistory.device_id == latest_subq.c.device_id) &
            (MonitoringHistory.recorded_at == latest_subq.c.max_at),
        )
        .join(Device, Device.id == MonitoringHistory.device_id)
        .all()
    )

    snapshots = []
    for record, device_name in latest_records:
        d = record.to_dict()
        d['device_name'] = device_name
        # Calculate memory percent on the fly if not stored
        if record.memory_total and record.memory_total > 0:
            d['memory_percent'] = round(record.memory_used / record.memory_total * 100, 1)
        else:
            d['memory_percent'] = 0.0
        snapshots.append(d)

    return jsonify({'snapshots': snapshots})
