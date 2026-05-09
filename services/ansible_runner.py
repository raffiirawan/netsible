"""
Ansible Runner service.
Wraps ansible-runner to execute playbooks against Mikrotik routers.
"""
import os
import json


def run_playbook(playbook_name, extra_vars=None, inventory='hosts.yml'):
    """
    Execute an Ansible playbook.

    Args:
        playbook_name: Name of the playbook file (e.g. 'gather_facts.yml')
        extra_vars:    Dictionary of extra variables to pass
        inventory:     Inventory filename

    Returns:
        dict with 'status', 'stdout', and 'stderr'
    """
    try:
        import ansible_runner

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ansible'))
        playbook_path = os.path.join(base_dir, 'playbooks', playbook_name)
        inventory_path = os.path.join(base_dir, 'inventory', inventory)

        result = ansible_runner.run(
            playbook=playbook_path,
            inventory=inventory_path,
            extravars=extra_vars or {},
            quiet=True,
        )

        return {
            'status': result.status,         # 'successful', 'failed', etc.
            'rc': result.rc,
            'stdout': result.stdout.read() if result.stdout else '',
            'stats': result.stats,
        }
    except ImportError:
        return {
            'status': 'error',
            'rc': -1,
            'stdout': 'ansible-runner is not installed.',
            'stats': {},
        }
    except Exception as e:
        return {
            'status': 'error',
            'rc': -1,
            'stdout': str(e),
            'stats': {},
        }
