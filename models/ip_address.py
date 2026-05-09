from extensions import db


class IPAddress(db.Model):
    """IP address assigned to a device interface."""
    __tablename__ = 'ip_addresses'

    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(45), nullable=False)
    network = db.Column(db.String(45), default='')
    interface = db.Column(db.String(50), default='')
    setting = db.Column(db.String(100), default='')
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'address': self.address,
            'network': self.network,
            'interface': self.interface,
            'setting': self.setting,
            'device_id': self.device_id,
        }

    def __repr__(self):
        return f'<IPAddress {self.address}>'
