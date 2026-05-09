"""
NETSIBLE — Network Management & Automation Platform
Flask application factory and entry point.
"""
import os
from flask import Flask
from config import config_by_name
from extensions import db, login_manager


def create_app(config_name=None):
    """Application factory."""
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.devices import devices_bp
    from blueprints.monitoring import monitoring_bp
    from blueprints.network_map import network_map_bp
    from blueprints.backup import backup_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(network_map_bp)
    app.register_blueprint(backup_bp)

    # Create database tables
    with app.app_context():
        import models  # noqa: F401 — ensures models are registered
        db.create_all()
        _seed_demo_data(app)

    return app


def _seed_demo_data(app):
    """Insert demo data if the database is empty."""
    from models.user import User
    from models.device import Device
    from models.ip_address import IPAddress

    if User.query.first() is not None:
        return  # Already seeded

    # Demo user
    admin = User(username='admin', email='admin@netsible.local')
    admin.set_password('admin123')
    db.session.add(admin)

    # Demo devices
    devices_data = [
        {'name': 'Router-GW', 'ip_address': '192.168.88.1', 'interface': 'ether1',
         'model': 'RB750GR3', 'serial_number': 'HBW08RLT3V0',
         'mac_address': 'E4:8D:8C:26:A0:01', 'routeros_version': '7.15.2',
         'status': 'online', 'uptime': '10d 4h 30m'},
        {'name': 'Router-Branch1', 'ip_address': '192.168.88.10', 'interface': 'ether1',
         'model': 'RB941-2nD', 'serial_number': 'CC3D0BFE1234',
         'mac_address': 'E4:8D:8C:26:B0:02', 'routeros_version': '7.14.3',
         'status': 'online', 'uptime': '5d 12h 15m'},
        {'name': 'Router-Branch2', 'ip_address': '192.168.88.3', 'interface': 'ether1',
         'model': 'hEX S', 'serial_number': 'ABC123DEF456',
         'mac_address': 'E4:8D:8C:26:C0:03', 'routeros_version': '7.15.2',
         'status': 'offline', 'uptime': ''},
        {'name': 'Router-Lab', 'ip_address': '192.168.100.1', 'interface': 'ether1',
         'model': 'CCR1009-7G', 'serial_number': 'HBW09XYZ5678',
         'mac_address': 'E4:8D:8C:26:D0:04', 'routeros_version': '7.13.5',
         'status': 'online', 'uptime': '30d 2h 10m'},
        {'name': 'AP-Office', 'ip_address': '192.168.88.5', 'interface': 'wlan1',
         'model': 'cAP ac', 'serial_number': 'WAP00112233',
         'mac_address': 'E4:8D:8C:26:E0:05', 'routeros_version': '7.15.2',
         'status': 'online', 'uptime': '15d 8h 45m'},
    ]
    devices = []
    for dd in devices_data:
        d = Device(**dd)
        db.session.add(d)
        devices.append(d)

    db.session.flush()  # Assign IDs

    # Demo IP addresses
    ips_data = [
        {'address': '192.168.88.1/24', 'network': '192.168.88.0', 'interface': 'ether1',
         'setting': 'Static', 'device_id': devices[0].id},
        {'address': '10.10.10.1/30', 'network': '10.10.10.0', 'interface': 'ether2',
         'setting': 'Static', 'device_id': devices[0].id},
        {'address': '192.168.88.10/24', 'network': '192.168.88.0', 'interface': 'ether1',
         'setting': 'DHCP', 'device_id': devices[1].id},
        {'address': '192.168.100.1/24', 'network': '192.168.100.0', 'interface': 'ether1',
         'setting': 'Static', 'device_id': devices[3].id},
        {'address': '172.16.0.1/16', 'network': '172.16.0.0', 'interface': 'ether3',
         'setting': 'Static', 'device_id': devices[0].id},
    ]
    for ip in ips_data:
        db.session.add(IPAddress(**ip))

    db.session.commit()


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
