"""
SSH Client service — enhanced for NETSIBLE Fase 2.

Features:
  - SSHClient class with context manager
  - execute() for single commands
  - execute_batch() for multiple commands in one session
  - parse_mikrotik_output() for structured RouterOS CLI parsing
  - test_ssh() quick reachability check
"""

import logging
import re

log = logging.getLogger(__name__)


class SSHClient:
    """
    SSH client for connecting to RouterOS (or any Linux) devices.
    Wraps Paramiko for connection management.

    Usage:
        with SSHClient('192.168.88.1', 'admin', '') as ssh:
            result = ssh.execute('/system resource print')
            if result['success']:
                data = parse_mikrotik_output(result['output'])
    """

    def __init__(self, host: str, username: str = 'admin',
                 password: str = '', port: int = 22,
                 connect_timeout: int = 10, exec_timeout: int = 15):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.connect_timeout = connect_timeout
        self.exec_timeout = exec_timeout
        self.client = None

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Establish SSH connection. Returns True on success."""
        try:
            import paramiko

            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.connect_timeout,
                look_for_keys=False,
                allow_agent=False,
            )
            log.info('SSH connected to %s', self.host)
            return True
        except ImportError:
            log.error('paramiko not installed. Run: pip install paramiko')
            return False
        except Exception as exc:
            log.warning('SSH connect failed [%s]: %s', self.host, exc)
            return False

    def disconnect(self):
        """Close the SSH connection."""
        try:
            if self.client:
                self.client.close()
        except Exception:
            pass
        finally:
            self.client = None

    def _ensure_connected(self) -> bool:
        if self.client is None:
            return self.connect()
        return True

    # Context manager
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()

    # ------------------------------------------------------------------
    # Command execution
    # ------------------------------------------------------------------

    def execute(self, command: str) -> dict:
        """
        Execute a single command and return structured result.

        Returns:
            {
                'success' : bool,
                'output'  : str,
                'error'   : str,
                'exit_code': int,
            }
        """
        if not self._ensure_connected():
            return {'success': False, 'output': '', 'error': 'Connection failed', 'exit_code': -1}

        try:
            stdin, stdout, stderr = self.client.exec_command(
                command, timeout=self.exec_timeout
            )
            output = stdout.read().decode('utf-8', errors='replace').strip()
            error = stderr.read().decode('utf-8', errors='replace').strip()
            exit_code = stdout.channel.recv_exit_status()

            return {
                'success': exit_code == 0,
                'output': output,
                'error': error,
                'exit_code': exit_code,
            }
        except Exception as exc:
            log.error('SSH execute [%s] `%s`: %s', self.host, command, exc)
            return {'success': False, 'output': '', 'error': str(exc), 'exit_code': -1}

    def execute_batch(self, commands: list) -> list:
        """
        Execute a list of commands in the same SSH session.

        Returns:
            List of result dicts (one per command).
        """
        if not self._ensure_connected():
            return [{'success': False, 'output': '', 'error': 'Connection failed', 'exit_code': -1}
                    for _ in commands]
        return [self.execute(cmd) for cmd in commands]


# ──────────────────────────────────────────────────────────────────────
# RouterOS output parsers
# ──────────────────────────────────────────────────────────────────────

def parse_mikrotik_output(raw: str) -> list:
    """
    Parse RouterOS 'print' command output into a list of dicts.

    RouterOS prints records like:
        0   name="ether1" type="ether" running=yes disabled=no
        1   name="ether2" type="ether" running=no  disabled=no

    Returns:
        List of dicts, one per record block.
    """
    if not raw:
        return []

    # Split by numbered lines (0 name=..., 1 name=...)
    blocks = re.split(r'\n\s*\d+\s+', '\n' + raw.strip())
    results = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        record = {}
        # Match key=value or key="value with spaces"
        for match in re.finditer(r'(\S+)=("(?:[^"\\]|\\.)*"|\S+)', block):
            key = match.group(1)
            value = match.group(2).strip('"')
            record[key] = value
        if record:
            results.append(record)

    return results


def parse_system_resource(raw: str) -> dict:
    """
    Parse '/system resource print' output into a metric dict.

    Returns:
        {cpu_load, memory_total, memory_free, uptime, version, board_name, ...}
    """
    result = {}
    for line in raw.splitlines():
        line = line.strip()
        if ':' in line:
            key, _, value = line.partition(':')
            result[key.strip().lower().replace(' ', '_')] = value.strip()
        elif '=' in line:
            for match in re.finditer(r'(\S+)=("(?:[^"\\]|\\.)*"|\S+)', line):
                k = match.group(1).replace('-', '_')
                v = match.group(2).strip('"')
                result[k] = v
    return result


# ──────────────────────────────────────────────────────────────────────
# Convenience functions
# ──────────────────────────────────────────────────────────────────────

def test_ssh(host: str, username: str = 'admin',
             password: str = '', port: int = 22) -> dict:
    """
    Quick SSH reachability test.

    Returns:
        {'success': bool, 'message': str, 'latency_ms': int}
    """
    import time
    start = time.monotonic()
    client = SSHClient(host, username, password, port, connect_timeout=5)
    connected = client.connect()
    elapsed = round((time.monotonic() - start) * 1000)
    client.disconnect()

    return {
        'success': connected,
        'message': f'SSH reachable at {host}:{port}' if connected
                   else f'SSH unreachable at {host}:{port}',
        'latency_ms': elapsed,
    }


def get_mikrotik_resource_via_ssh(host: str, username: str = 'admin',
                                   password: str = '') -> dict:
    """
    Retrieve system resources from a Mikrotik router using SSH as fallback.
    Useful when RouterOS API (port 8728) is disabled.
    """
    with SSHClient(host, username, password) as ssh:
        result = ssh.execute('/system resource print')

    if not result['success']:
        return {'success': False, 'cpu_load': 0, 'uptime': 'Offline'}

    parsed = parse_system_resource(result['output'])
    cpu = int(parsed.get('cpu_load', '0').rstrip('%'))

    raw_mem_total = parsed.get('total_memory', '0')
    raw_mem_free = parsed.get('free_memory', '0')

    def parse_mem(s):
        s = s.strip()
        if s.endswith('MiB'):
            return int(float(s[:-3]) * 1024 * 1024)
        if s.endswith('KiB'):
            return int(float(s[:-3]) * 1024)
        return int(s) if s.isdigit() else 0

    mem_total = parse_mem(raw_mem_total)
    mem_free = parse_mem(raw_mem_free)
    mem_used = mem_total - mem_free
    mem_pct = round(mem_used / mem_total * 100, 1) if mem_total else 0

    return {
        'success': True,
        'cpu_load': cpu,
        'memory_total': mem_total,
        'memory_free': mem_free,
        'memory_used': mem_used,
        'memory_percent': mem_pct,
        'uptime': parsed.get('uptime', ''),
        'version': parsed.get('version', ''),
        'board_name': parsed.get('board_name', ''),
    }
