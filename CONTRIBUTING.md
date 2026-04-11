# Contributing to sfulmer.proxmox

Thank you for your interest in contributing to the Proxmox VE Ansible collection. This guide covers the development workflow, coding standards, and submission process.

## Development Setup

### Requirements

- Python >= 3.12
- Ansible >= 2.16
- [proxmoxer](https://pypi.org/project/proxmoxer/) >= 2.0
- [requests](https://pypi.org/project/requests/)
- Development tools: `pycodestyle`, `ansible-lint`, `ansible-test`

### Installation

```bash
git clone https://github.com/stevefulme1/ansible-proxmox-modules.git
cd ansible-proxmox-modules
pip install ansible-core>=2.16 ansible-lint>=24.2 pycodestyle>=2.11 proxmoxer requests
```

## Types of Contributions

### Module Development

New modules should target gaps in Proxmox VE or Proxmox Backup Server API coverage. Before starting:

1. Check existing modules and open issues to avoid duplication
2. Open an issue describing the proposed module
3. Reference the relevant [Proxmox API documentation](https://pve.proxmox.com/pve-docs/api-viewer/)

### Bug Fixes

1. Verify the bug by reproducing it
2. Reference the issue number in your PR
3. Include a test case that demonstrates the fix

### Documentation

Documentation improvements are always welcome, including:

- Module `DOCUMENTATION`, `EXAMPLES`, and `RETURN` docstrings
- README updates
- Usage examples and playbook patterns

## Module Standards

All modules must:

- **Use `ProxmoxModule` base class** from `plugins/module_utils/proxmox.py`
- **Include complete docstrings:** `DOCUMENTATION`, `EXAMPLES`, and `RETURN`
- **Support check mode** (`supports_check_mode=True`)
- **Be idempotent** — only report `changed=True` when actual changes are made
- **Handle errors gracefully** with descriptive `fail_json` messages
- **Set `version_added: "1.0.0"`** (or the appropriate upcoming version)
- **Support both auth methods** — password and API token

### Module Template

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_example
short_description: Short description here
description:
  - Detailed description.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - Your Name (@github_handle)
options:
  name:
    description: The name of the resource.
    type: str
    required: true
  state:
    description: Whether the resource should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create resource
  sfulmer.proxmox.proxmox_example:
    api_host: pve.example.com
    api_user: root@pam
    api_password: "{{ proxmox_password }}"
    name: myresource
    state: present
'''

RETURN = r'''
name:
  description: The resource name.
  returned: always
  type: str
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    api = proxmox.get_api()

    # Implementation here

    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
```

## Quality Assurance

### Code Style

```bash
# PEP 8 with 160-character line limit
pycodestyle --max-line-length=160 --ignore=E402 plugins/modules/*.py
```

### Ansible Lint

```bash
ansible-lint --profile production plugins/modules/*.py
```

### Sanity Tests

```bash
# Requires collection directory structure
mkdir -p /tmp/test/ansible_collections/sfulmer/proxmox
cp -r . /tmp/test/ansible_collections/sfulmer/proxmox/
cd /tmp/test/ansible_collections/sfulmer/proxmox
ansible-test sanity --python 3.12
```

## Submitting Changes

1. **Fork and branch** — create a descriptive branch name (e.g., `feat/proxmox-new-module`)
2. **Write clear commits** — follow [conventional commit](https://www.conventionalcommits.org/) format
3. **Add a changelog fragment** — place a YAML file in `changelogs/fragments/`:

   ```yaml
   # changelogs/fragments/add-proxmox-example.yml
   minor_changes:
     - proxmox_example - new module to manage example resources (https://github.com/stevefulme1/ansible-proxmox-modules/pull/XX).
   ```

4. **Ensure all checks pass** — pycodestyle, ansible-lint, ansible-test sanity
5. **Open a PR** with a clear description and link to any related issues
6. **Respond to reviews** in a timely manner

## Support

- [GitHub Issues](https://github.com/stevefulme1/ansible-proxmox-modules/issues)
- [Ansible Forum](https://forum.ansible.com/) — use the `proxmox` tag
- IRC: `#ansible` on [Libera.Chat](https://libera.chat/)
