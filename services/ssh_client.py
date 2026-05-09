"""
SSH Client service for direct command execution on GNS3 routers.
Wraps Paramiko for SSH connections.
"""


class SSHClient:
    """SSH client for connecting to network devices."""

    def __init__(self, host, username='admin', password='', port=22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.client = None

    def connect(self):
        """Establish SSH connection."""
        try:
            import paramiko
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10,
            )
            return True
        except Exception as e:
            print(f'SSH connection error: {e}')
            return False

    def execute(self, command):
        """Execute a command over SSH and return the output."""
        if not self.client:
            if not self.connect():
                return {'success': False, 'output': 'Connection failed'}

        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=15)
            output = stdout.read().decode('utf-8', errors='replace')
            error = stderr.read().decode('utf-8', errors='replace')
            return {
                'success': True,
                'output': output,
                'error': error,
            }
        except Exception as e:
            return {'success': False, 'output': str(e)}

    def disconnect(self):
        """Close the SSH connection."""
        if self.client:
            self.client.close()
            self.client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
