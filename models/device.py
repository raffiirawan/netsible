from datetime import datetime, timezone
from extensions import db


class Device(db.Model):
    """Network device (Mikrotik router) managed by NETSIBLE."""
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    interface = db.Column(db.String(50), default='ether1')
    model = db.Column(db.String(100), default='')
    serial_number = db.Column(db.String(100), default='')
    mac_address = db.Column(db.String(17), default='')
    routeros_version = db.Column(db.String(20), default='')
    status = db.Column(db.String(10), default='offline')  # online / offline
    uptime = db.Column(db.String(50), default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    ip_addresses = db.relationship('IPAddress', backref='device', lazy=True,
                                   cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ip_address': self.ip_address,
            'interface': self.interface,
            'model': self.model,
            'serial_number': self.serial_number,
            'mac_address': self.mac_address,
            'routeros_version': self.routeros_version,
            'status': self.status,
            'uptime': self.uptime,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<Device {self.name} ({self.ip_address})>'
