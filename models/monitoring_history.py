"""
MonitoringHistory — stores periodic metrics snapshots for each device.
Used for charts / trend analysis in the monitoring UI.
"""
from datetime import datetime, timezone
from extensions import db


class MonitoringHistory(db.Model):
    """Periodic snapshot of device resource metrics."""
    __tablename__ = 'monitoring_history'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(
        db.Integer,
        db.ForeignKey('devices.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )

    # Resource metrics
    cpu_load = db.Column(db.Integer, default=0)          # percent  0-100
    memory_used = db.Column(db.Integer, default=0)       # bytes
    memory_total = db.Column(db.Integer, default=0)      # bytes
    disk_used = db.Column(db.Integer, default=0)         # percent  0-100
    temperature = db.Column(db.Float, default=0.0)       # °C
    active_connections = db.Column(db.Integer, default=0)
    uptime_raw = db.Column(db.String(100), default='')   # e.g. "2d3h4m5s"

    # Timestamp
    recorded_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationship (read-only back-ref)
    device = db.relationship('Device', backref=db.backref(
        'monitoring_history', lazy='dynamic', passive_deletes=True
    ))

    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'cpu_load': self.cpu_load,
            'memory_used': self.memory_used,
            'memory_total': self.memory_total,
            'disk_used': self.disk_used,
            'temperature': self.temperature,
            'active_connections': self.active_connections,
            'uptime_raw': self.uptime_raw,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
        }

    def __repr__(self):
        return (
            f'<MonitoringHistory device={self.device_id} '
            f'cpu={self.cpu_load}% at {self.recorded_at}>'
        )
