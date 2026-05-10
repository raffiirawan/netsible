"""
Ansible Runner service — enhanced for NETSIBLE Fase 2.

Features:
  - run_playbook()             : Run any playbook from ansible/playbooks/
  - generate_inventory()       : Build dynamic INI inventory from DB devices
  - generate_inventory_file()  : Write dynamic inventory to a temp file
"""
import os
import json
import logging
import tempfile

log = logging.getLogger(__name__)

# Absolute path to the ansible/ directory (sibling of services/)
_ANSIBLE_BASE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'ansible')
)


# ──────────────────────────────────────────────────────────────────────
# Core playbook runner
# ──────────────────────────────────────────────────────────────────────

def run_playbook(playbook_name: str, extra_vars: dict = None,
                 inventory: str = 'hosts.yml',
                 dynamic_hosts: list = None) -> dict:
    """
    Execute an Ansible playbook.

    Args:
        playbook_name  : Filename inside ansible/playbooks/ (e.g. 'gather_facts.yml')
        extra_vars     : Dict of extra variables passed to ansible-runner
        inventory      : Static inventory filename inside ansible/inventory/
                         (ignored when dynamic_hosts is provided)
        dynamic_hosts  : List of dicts [{name, ip, username, password}]
                         When provided, a temporary INI inventory is generated
                         instead of using the static file.

    Returns:
        {
            'status' : str   ('successful' | 'failed' | 'error')
            'rc'     : int
            'stdout' : str
            'stderr' : str
            'stats'  : dict
        }
    """
    try:
        import ansible_runner  # pip install ansible-runner

        playbook_path = os.path.join(_ANSIBLE_BASE, 'playbooks', playbook_name)

        # Choose inventory source
        if dynamic_hosts:
            inv_content = generate_inventory(dynamic_hosts)
            # Write to temp file that ansible-runner can consume
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.ini', delete=False, prefix='netsible_inv_'
            ) as tmp:
                tmp.write(inv_content)
                inventory_path = tmp.name
        else:
            inventory_path = os.path.join(_ANSIBLE_BASE, 'inventory', inventory)

        log.info('Running playbook: %s | inventory: %s', playbook_name, inventory_path)

        result = ansible_runner.run(
            playbook=playbook_path,
            inventory=inventory_path,
            extravars=extra_vars or {},
            quiet=True,
        )

        stdout = ''
        try:
            stdout = result.stdout.read() if result.stdout else ''
        except Exception:
            pass

        return {
            'status': result.status,   # 'successful', 'failed', 'canceled'
            'rc': result.rc,
            'stdout': stdout,
            'stderr': '',
            'stats': result.stats or {},
        }

    except ImportError:
        msg = 'ansible-runner is not installed. Run: pip install ansible-runner'
        log.error(msg)
        return {'status': 'error', 'rc': -1, 'stdout': msg, 'stderr': '', 'stats': {}}

    except Exception as exc:
        log.error('run_playbook [%s] failed: %s', playbook_name, exc)
        return {
            'status': 'error', 'rc': -1,
            'stdout': str(exc), 'stderr': '', 'stats': {},
        }

    finally:
        # Clean up temp inventory file
        if dynamic_hosts and 'inventory_path' in locals():
            try:
                os.unlink(inventory_path)
            except Exception:
                pass


# ──────────────────────────────────────────────────────────────────────
# Dynamic inventory generator
# ──────────────────────────────────────────────────────────────────────

def generate_inventory(devices: list) -> str:
    """
    Generate an Ansible INI-format inventory string from a list of device dicts.

    Each device dict must have:
        ip        : str  — device IP address
        username  : str  — SSH / API username (default: 'admin')
        password  : str  — password (default: '')
        name      : str  — used as Ansible host alias

    Returns:
        Multi-line INI string, e.g.:
            [mikrotik_routers]
            Router-Gateway ansible_host=192.168.88.1 ansible_user=admin ...
    """
    lines = ['[mikrotik_routers]']
    for dev in devices:
        alias = (dev.get('name') or dev.get('ip', 'device')).replace(' ', '_')
        ip = dev.get('ip') or dev.get('ip_address', '')
        username = dev.get('username', 'admin')
        password = dev.get('password', '')

        line = (
            f'{alias} '
            f'ansible_host={ip} '
            f'ansible_user={username} '
            f'ansible_password={password} '
            f'ansible_connection=network_cli '
            f'ansible_network_os=community.routeros.routeros'
        )
        lines.append(line)

    lines.append('')
    lines.append('[mikrotik_routers:vars]')
    lines.append('ansible_python_interpreter=/usr/bin/python3')

    return '\n'.join(lines) + '\n'


def generate_inventory_from_db() -> str:
    """
    Build a dynamic inventory from all Device records in the database.
    Must be called within an active Flask application context.
    """
    from models.device import Device

    devices = Device.query.all()
    device_dicts = [
        {
            'name': d.name,
            'ip': d.ip_address,
            'username': 'admin',
            'password': '',
        }
        for d in devices
    ]
    return generate_inventory(device_dicts)


def generate_inventory_file_from_db(filepath: str = None) -> str:
    """
    Write a dynamic inventory file from all DB devices and return the path.
    If filepath is None, a temporary file is created.
    """
    content = generate_inventory_from_db()

    if filepath is None:
        fd, filepath = tempfile.mkstemp(suffix='.ini', prefix='netsible_inv_')
        os.close(fd)

    with open(filepath, 'w') as f:
        f.write(content)

    log.info('Dynamic inventory written to %s', filepath)
    return filepath
