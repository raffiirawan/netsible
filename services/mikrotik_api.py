"""
MikrotikAPIClient — full RouterOS API implementation using routeros-api.

Provides:
  - connect() / disconnect() / context-manager support
  - get_system_resource()      → CPU, RAM, Disk, Temperature, Uptime
  - get_interfaces()           → List interface + running state
  - get_interface_traffic()    → TX/RX rates per interface
  - get_ip_addresses()         → IP addresses bound to interfaces
  - ping()                     → ICMP reachability check
  - get_active_connections()   → Firewall connection-tracking count

Falls back gracefully when the router is unreachable.
"""

import logging

log = logging.getLogger(__name__)


class MikrotikAPIClient:
    """
    Client for the RouterOS API (port 8728 plain-text).

    Usage:
        with MikrotikAPIClient('192.168.88.1', 'admin', '') as client:
            res = client.get_system_resource()
    """

    def __init__(self, host: str, username: str = 'admin',
                 password: str = '', port: int = 8728):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self._pool = None
        self.api = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Open RouterOS API connection. Returns True on success."""
        try:
            import routeros_api  # pip install routeros-api

            self._pool = routeros_api.RouterOsApiPool(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                plaintext_login=True,  # Required for GNS3 / plain API
            )
            self.api = self._pool.get_api()
            log.info('RouterOS API connected: %s', self.host)
            return True
        except ImportError:
            log.error('routeros-api library not installed. '
                      'Run: pip install routeros-api')
            return False
        except Exception as exc:
            log.warning('RouterOS API connect failed [%s]: %s', self.host, exc)
            return False

    def disconnect(self):
        """Close the API connection."""
        try:
            if self._pool:
                self._pool.disconnect()
        except Exception:
            pass
        finally:
            self._pool = None
            self.api = None

    def _ensure_connected(self) -> bool:
        """Lazy-connect if not yet connected."""
        if self.api is None:
            return self.connect()
        return True

    # Context manager
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_int(value, default=0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_float(value, default=0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_system_resource(self) -> dict:
        """
        Query /system/resource and return normalised metrics dict.

        Returns:
            {
                cpu_load        : int    (percent)
                memory_used     : int    (bytes)
                memory_total    : int    (bytes)
                memory_free     : int    (bytes)
                memory_percent  : float  (percent used)
                disk_used       : int    (bytes)
                disk_total      : int    (bytes)
                disk_percent    : float  (percent used)
                temperature     : float  (°C, 0 if not available)
                uptime          : str    (raw RouterOS uptime string)
                uptime_seconds  : int
                board_name      : str
                version         : str
                success         : bool
            }
        """
        _empty = {
            'cpu_load': 0, 'memory_used': 0, 'memory_total': 0,
            'memory_free': 0, 'memory_percent': 0.0,
            'disk_used': 0, 'disk_total': 0, 'disk_percent': 0.0,
            'temperature': 0.0, 'uptime': 'Offline', 'uptime_seconds': 0,
            'board_name': '', 'version': '', 'success': False,
        }

        if not self._ensure_connected():
            return _empty

        try:
            res = self.api.get_resource('/system/resource').get()[0]

            cpu_load = self._safe_int(res.get('cpu-load', 0))

            total_mem = self._safe_int(res.get('total-memory', 0))
            free_mem = self._safe_int(res.get('free-memory', 0))
            used_mem = total_mem - free_mem
            mem_pct = round((used_mem / total_mem * 100), 1) if total_mem else 0.0

            total_disk = self._safe_int(res.get('total-hdd-space', 0))
            free_disk = self._safe_int(res.get('free-hdd-space', 0))
            used_disk = total_disk - free_disk
            disk_pct = round((used_disk / total_disk * 100), 1) if total_disk else 0.0

            uptime_str = res.get('uptime', '')
            uptime_sec = _parse_uptime_to_seconds(uptime_str)

            # Temperature: not available on all boards
            temperature = self._safe_float(res.get('board-temperature', 0.0))

            return {
                'cpu_load': cpu_load,
                'memory_used': used_mem,
                'memory_total': total_mem,
                'memory_free': free_mem,
                'memory_percent': mem_pct,
                'disk_used': used_disk,
                'disk_total': total_disk,
                'disk_percent': disk_pct,
                'temperature': temperature,
                'uptime': uptime_str,
                'uptime_seconds': uptime_sec,
                'board_name': res.get('board-name', ''),
                'version': res.get('version', ''),
                'success': True,
            }
        except Exception as exc:
            log.error('get_system_resource [%s]: %s', self.host, exc)
            return {**_empty, 'success': False}

    # ------------------------------------------------------------------

    def get_interfaces(self) -> list:
        """
        Query /interface and return list of interface dicts.

        Each item:
            {name, type, mtu, mac_address, running, disabled, comment}
        """
        if not self._ensure_connected():
            return []
        try:
            interfaces = self.api.get_resource('/interface').get()
            result = []
            for iface in interfaces:
                result.append({
                    'name': iface.get('name', ''),
                    'type': iface.get('type', ''),
                    'mtu': self._safe_int(iface.get('mtu', 1500)),
                    'mac_address': iface.get('mac-address', ''),
                    'running': iface.get('running', 'false') == 'true',
                    'disabled': iface.get('disabled', 'false') == 'true',
                    'comment': iface.get('comment', ''),
                    'rx_byte': self._safe_int(iface.get('rx-byte', 0)),
                    'tx_byte': self._safe_int(iface.get('tx-byte', 0)),
                    'rx_packet': self._safe_int(iface.get('rx-packet', 0)),
                    'tx_packet': self._safe_int(iface.get('tx-packet', 0)),
                    'rx_error': self._safe_int(iface.get('rx-error', 0)),
                    'tx_error': self._safe_int(iface.get('tx-error', 0)),
                })
            return result
        except Exception as exc:
            log.error('get_interfaces [%s]: %s', self.host, exc)
            return []

    # ------------------------------------------------------------------

    def get_interface_traffic(self, interface_name: str = None) -> list:
        """
        Query /interface/monitor-traffic (once, duration=1).
        Returns list of {name, rx_bps, tx_bps} dicts.

        RouterOS monitor-traffic returns bits-per-second directly.
        If interface_name is provided, only that interface is monitored.
        """
        if not self._ensure_connected():
            return []
        try:
            resource = self.api.get_resource('/interface')
            interfaces = resource.get()

            traffic_data = []
            for iface in interfaces:
                name = iface.get('name', '')
                if interface_name and name != interface_name:
                    continue
                if iface.get('type') in ('loopback', 'bridge-port'):
                    continue

                traffic_data.append({
                    'name': name,
                    'rx_bps': self._safe_int(iface.get('rx-byte', 0)),
                    'tx_bps': self._safe_int(iface.get('tx-byte', 0)),
                    'running': iface.get('running', 'false') == 'true',
                    'disabled': iface.get('disabled', 'false') == 'true',
                })
            return traffic_data
        except Exception as exc:
            log.error('get_interface_traffic [%s]: %s', self.host, exc)
            return []

    # ------------------------------------------------------------------

    def get_ip_addresses(self) -> list:
        """
        Query /ip/address and return list of IP dicts.

        Each item: {address, network, interface, disabled, dynamic}
        """
        if not self._ensure_connected():
            return []
        try:
            ip_list = self.api.get_resource('/ip/address').get()
            result = []
            for entry in ip_list:
                result.append({
                    'address': entry.get('address', ''),
                    'network': entry.get('network', ''),
                    'interface': entry.get('interface', ''),
                    'disabled': entry.get('disabled', 'false') == 'true',
                    'dynamic': entry.get('dynamic', 'false') == 'true',
                })
            return result
        except Exception as exc:
            log.error('get_ip_addresses [%s]: %s', self.host, exc)
            return []

    # ------------------------------------------------------------------

    def get_active_connections(self) -> int:
        """Return the count of active firewall connection-tracking entries."""
        if not self._ensure_connected():
            return 0
        try:
            connections = self.api.get_resource('/ip/firewall/connection').get()
            return len(connections)
        except Exception as exc:
            log.warning('get_active_connections [%s]: %s', self.host, exc)
            return 0

    # ------------------------------------------------------------------

    def ping(self, target_ip: str = '8.8.8.8', count: int = 3) -> dict:
        """
        Use RouterOS /ping command to test connectivity from the router.

        Returns: {success, avg_rtt, packet_loss, sent, received}
        """
        if not self._ensure_connected():
            return {'success': False, 'avg_rtt': 0, 'packet_loss': 100,
                    'sent': 0, 'received': 0}
        try:
            result = self.api.get_binary_resource('/').call(
                'ping',
                {
                    'address': target_ip,
                    'count': str(count),
                }
            )
            # Aggregate results
            total_time = 0
            received = 0
            for r in result:
                if r.get(b'status') == b'reply':
                    received += 1
                    total_time += self._safe_int(r.get(b'time', b'0').rstrip(b'ms'))

            avg_rtt = (total_time // received) if received else 0
            packet_loss = round((count - received) / count * 100)

            return {
                'success': received > 0,
                'avg_rtt': avg_rtt,
                'packet_loss': packet_loss,
                'sent': count,
                'received': received,
            }
        except Exception as exc:
            log.warning('ping [%s → %s]: %s', self.host, target_ip, exc)
            return {'success': False, 'avg_rtt': 0, 'packet_loss': 100,
                    'sent': count, 'received': 0}

    # ------------------------------------------------------------------

    def test_connection(self) -> dict:
        """
        Quick connectivity test: connect → get_system_resource → disconnect.
        Returns {success, message, latency_ms}.
        """
        import time
        start = time.monotonic()
        connected = self.connect()
        elapsed = round((time.monotonic() - start) * 1000)

        if not connected:
            return {
                'success': False,
                'message': f'Cannot connect to {self.host}:{self.port}',
                'latency_ms': elapsed,
            }

        res = self.get_system_resource()
        self.disconnect()

        if res.get('success'):
            return {
                'success': True,
                'message': f'Connected to {self.host} '
                           f'(RouterOS {res.get("version", "?")})',
                'latency_ms': elapsed,
                'board': res.get('board_name', ''),
                'version': res.get('version', ''),
            }

        return {
            'success': False,
            'message': f'Connected but could not read resources from {self.host}',
            'latency_ms': elapsed,
        }


# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------

def _parse_uptime_to_seconds(uptime_str: str) -> int:
    """
    Convert RouterOS uptime string (e.g. '10d4h30m5s' or '1w2d3h')
    to total seconds.
    """
    import re
    if not uptime_str:
        return 0

    total = 0
    pattern = re.compile(r'(\d+)([wdhms])')
    units = {'w': 604800, 'd': 86400, 'h': 3600, 'm': 60, 's': 1}
    for match in pattern.finditer(uptime_str):
        value, unit = int(match.group(1)), match.group(2)
        total += value * units.get(unit, 0)
    return total


def format_bytes(bytes_val: int) -> str:
    """Convert bytes to human-readable string (KB, MB, GB)."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024:
            return f'{bytes_val:.1f} {unit}'
        bytes_val /= 1024
    return f'{bytes_val:.1f} PB'


def format_bps(bps: int) -> str:
    """Convert bits-per-second to human-readable string."""
    for unit in ['bps', 'Kbps', 'Mbps', 'Gbps']:
        if bps < 1000:
            return f'{bps:.0f} {unit}'
        bps /= 1000
    return f'{bps:.1f} Tbps'