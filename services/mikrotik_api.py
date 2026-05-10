import routeros_api

class MikrotikAPIClient:
    def __init__(self, host, username, password='', port=8728):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.connection = None
        self.api = None

    def connect(self):
        """Membangun koneksi ke RouterOS API"""
        try:
            # Gunakan plaintext_login=True karena biasanya router GNS3 belum pakai SSL
            self.connection = routeros_api.RouterOsApiPool(
                self.host, 
                username=self.username, 
                password=self.password, 
                port=self.port, 
                plaintext_login=True
            )
            self.api = self.connection.get_api()
            return True
        except Exception as e:
            print(f"Gagal koneksi ke API Mikrotik {self.host}: {e}")
            return False

    def disconnect(self):
        """Memutus koneksi"""
        if self.connection:
            self.connection.disconnect()

    def get_system_resource(self):
        """Mengambil data asli CPU, RAM, dan Uptime"""
        if not self.api:
            sukses = self.connect()
            if not sukses:
                return {'cpu-load': 0, 'free-memory': 0, 'uptime': 'Offline'}
        
        try:
            # Mengambil array resource dari Mikrotik
            resource = self.api.get_resource('/system/resource').get()[0]
            
            # Format ulang datanya agar sesuai dengan kebutuhan Blueprint/UI
            return {
                'cpu-load': int(resource.get('cpu-load', 0)),
                'free-memory': int(resource.get('free-memory', 0)),
                'total-memory': int(resource.get('total-memory', 0)),
                'uptime': resource.get('uptime', '')
            }
        except Exception as e:
            print(f"Gagal baca resource: {e}")
            return {'cpu-load': 0, 'free-memory': 0, 'uptime': 'Error'}