"""
Monitoring blueprint — Fase 2: Real-time monitoring via RouterOS API.

Endpoints:
  GET /monitoring/<device_id>                 — HTML monitoring detail page
  GET /monitoring/<device_id>/interface       — HTML interface visualization page
  GET /monitoring/api/<device_id>/realtime    — JSON real-time snapshot
  GET /monitoring/api/<device_id>/history     — JSON historical metrics (last N points)
  GET /monitoring/api/<device_id>/interfaces  — JSON full interface list
  POST /monitoring/api/<device_id>/test       — JSON connectivity test
  GET /monitoring/api/<device_id>/ping        — JSON ping from router to target
"""

import logging
from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required

from extensions import db
from models.device import Device
from models.monitoring_history import MonitoringHistory
from services.mikrotik_api import MikrotikAPIClient

log = logging.getLogger(__name__)

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

# How many history points to return by default
_DEFAULT_HISTORY_LIMIT = 60  # last 60 snapshots ≈ 1 hour at 1-min polling


# ──────────────────────────────────────────────────────────────────────
# HTML pages
# ──────────────────────────────────────────────────────────────────────

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


# ──────────────────────────────────────────────────────────────────────
# JSON API — Real-time snapshot
# ──────────────────────────────────────────────────────────────────────

@monitoring_bp.route('/api/<int:device_id>/realtime')
@login_required
def get_realtime_data(device_id):
    """
    Fetch a real-time snapshot from the router via RouterOS API.

    Response JSON:
    {
        "success"      : bool,
        "device_id"    : int,
        "device_name"  : str,
        "ip_address"   : str,
        "cpu"          : int,          # percent
        "memory_used"  : int,          # bytes
        "memory_total" : int,          # bytes
        "memory_pct"   : float,        # percent
        "disk_used"    : int,          # bytes
        "disk_total"   : int,          # bytes
        "disk_pct"     : float,        # percent
        "temperature"  : float,        # °C
        "uptime"       : str,
        "uptime_seconds" : int,
        "connections"  : int,
        "tx_rate"      : int,          # bytes (cumulative)
        "rx_rate"      : int,          # bytes (cumulative)
        "interfaces"   : list,
        "version"      : str,
        "board"        : str,
        "timestamp"    : str (ISO-8601)
    }
    """
    device = Device.query.get_or_404(device_id)

    client = MikrotikAPIClient(
        host=device.ip_address,
        username='admin',
        password='',
    )

    resource = client.get_system_resource()
    interfaces = client.get_interfaces()
    connections = client.get_active_connections()
    client.disconnect()

    # Aggregate TX / RX totals from all interfaces
    tx_total = sum(i.get('tx_byte', 0) for i in interfaces)
    rx_total = sum(i.get('rx_byte', 0) for i in interfaces)

    # Persist snapshot to history (fire-and-forget, ignore errors)
    _persist_snapshot(device_id, resource, connections)

    # Update device status + uptime in DB if we got live data
    if resource.get('success'):
        try:
            device.status = 'online'
            device.uptime = resource.get('uptime', device.uptime)
            if resource.get('version'):
                device.routeros_version = resource['version']
            db.session.commit()
        except Exception:
            db.session.rollback()

    payload = {
        'success': resource.get('success', False),
        'device_id': device.id,
        'device_name': device.name,
        'ip_address': device.ip_address,
        # Resources
        'cpu': resource.get('cpu_load', 0),
        'memory_used': resource.get('memory_used', 0),
        'memory_total': resource.get('memory_total', 0),
        'memory_pct': resource.get('memory_percent', 0.0),
        'disk_used': resource.get('disk_used', 0),
        'disk_total': resource.get('disk_total', 0),
        'disk_pct': resource.get('disk_percent', 0.0),
        'temperature': resource.get('temperature', 0.0),
        'uptime': resource.get('uptime', device.uptime or 'N/A'),
        'uptime_seconds': resource.get('uptime_seconds', 0),
        # Network
        'connections': connections,
        'tx_rate': tx_total,
        'rx_rate': rx_total,
        # Interface list (compact)
        'interfaces': [
            {
                'name': i['name'],
                'running': i['running'],
                'disabled': i['disabled'],
                'tx_byte': i.get('tx_byte', 0),
                'rx_byte': i.get('rx_byte', 0),
            }
            for i in interfaces
        ],
        # Device info
        'version': resource.get('version', device.routeros_version or ''),
        'board': resource.get('board_name', device.model or ''),
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }

    return jsonify(payload)


# ──────────────────────────────────────────────────────────────────────
# JSON API — Historical data
# ──────────────────────────────────────────────────────────────────────

@monitoring_bp.route('/api/<int:device_id>/history')
@login_required
def get_history(device_id):
    """
    Return saved monitoring history for a device.

    Query params:
        limit  (int)  — number of points, default 60
        hours  (int)  — only return records from last N hours (optional)

    Response JSON:
    {
        "device_id" : int,
        "count"     : int,
        "history"   : [ {cpu_load, memory_used, memory_total, disk_used,
                         temperature, active_connections, uptime_raw,
                         recorded_at}, ... ]
    }
    """
    device = Device.query.get_or_404(device_id)

    limit = min(request.args.get('limit', _DEFAULT_HISTORY_LIMIT, type=int), 1440)
    hours = request.args.get('hours', None, type=int)

    query = MonitoringHistory.query.filter_by(device_id=device.id)

    if hours:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        query = query.filter(MonitoringHistory.recorded_at >= since)

    records = (
        query
        .order_by(MonitoringHistory.recorded_at.desc())
        .limit(limit)
        .all()
    )
    records.reverse()  # chronological order

    return jsonify({
        'device_id': device.id,
        'count': len(records),
        'history': [r.to_dict() for r in records],
    })


# ──────────────────────────────────────────────────────────────────────
# JSON API — Full interface list
# ──────────────────────────────────────────────────────────────────────

@monitoring_bp.route('/api/<int:device_id>/interfaces')
@login_required
def get_interfaces(device_id):
    """
    Return full interface details including traffic bytes.

    Response JSON:
    {
        "success"    : bool,
        "device_id"  : int,
        "interfaces" : [ {name, type, mtu, mac_address, running,
                          disabled, comment, rx_byte, tx_byte,
                          rx_packet, tx_packet, rx_error, tx_error}, ... ]
    }
    """
    device = Device.query.get_or_404(device_id)

    with MikrotikAPIClient(device.ip_address, 'admin', '') as client:
        interfaces = client.get_interfaces()

    return jsonify({
        'success': len(interfaces) > 0,
        'device_id': device.id,
        'interfaces': interfaces,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })


# ──────────────────────────────────────────────────────────────────────
# JSON API — Connectivity test
# ──────────────────────────────────────────────────────────────────────

@monitoring_bp.route('/api/<int:device_id>/test', methods=['POST'])
@login_required
def test_connection(device_id):
    """
    Quick connectivity test: connect → read resource → disconnect.

    Response JSON:
    { "success": bool, "message": str, "latency_ms": int, "board": str, "version": str }
    """
    device = Device.query.get_or_404(device_id)

    client = MikrotikAPIClient(device.ip_address, 'admin', '')
    result = client.test_connection()

    # Reflect status in DB
    try:
        device.status = 'online' if result['success'] else 'offline'
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify({**result, 'device_id': device.id})


# ──────────────────────────────────────────────────────────────────────
# JSON API — Ping from router to target
# ──────────────────────────────────────────────────────────────────────

@monitoring_bp.route('/api/<int:device_id>/ping')
@login_required
def router_ping(device_id):
    """
    Send ICMP ping from the router to a target IP.

    Query params:
        target  (str)  — IP to ping (default: 8.8.8.8)
        count   (int)  — ping count (default: 3, max: 10)

    Response JSON:
    { "success": bool, "avg_rtt": int, "packet_loss": int,
      "sent": int, "received": int }
    """
    device = Device.query.get_or_404(device_id)

    target = request.args.get('target', '8.8.8.8')
    count = min(request.args.get('count', 3, type=int), 10)

    with MikrotikAPIClient(device.ip_address, 'admin', '') as client:
        result = client.ping(target_ip=target, count=count)

    return jsonify({**result, 'device_id': device.id, 'target': target})


# ──────────────────────────────────────────────────────────────────────
# Internal helper
# ──────────────────────────────────────────────────────────────────────

def _persist_snapshot(device_id: int, resource: dict, connections: int):
    """Save a monitoring snapshot to the database (silent failure)."""
    if not resource.get('success'):
        return
    try:
        snap = MonitoringHistory(
            device_id=device_id,
            cpu_load=resource.get('cpu_load', 0),
            memory_used=resource.get('memory_used', 0),
            memory_total=resource.get('memory_total', 0),
            disk_used=resource.get('disk_percent', 0),
            temperature=resource.get('temperature', 0.0),
            active_connections=connections,
            uptime_raw=resource.get('uptime', ''),
            recorded_at=datetime.now(timezone.utc),
        )
        db.session.add(snap)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        log.warning('Failed to persist monitoring snapshot: %s', exc)
