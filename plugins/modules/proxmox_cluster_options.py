#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_cluster_options
short_description: Manage Proxmox VE cluster-wide options
description:
  - Manage cluster-wide datacenter options in Proxmox VE.
  - Uses the C(/cluster/options) API endpoint to read and update settings.
version_added: "1.0.0"
author:
  - sfulmer
options:
  migration:
    description:
      - Migration type for the cluster.
    type: str
    choices: ['secure', 'insecure']
  migration_network:
    description:
      - CIDR network for migration traffic.
    type: str
  console:
    description:
      - Default console viewer type.
    type: str
    choices: ['applet', 'vv', 'html5', 'xtermjs']
  description:
    description:
      - Datacenter description.
    type: str
  email_from:
    description:
      - Email address used as the sender for cluster notifications.
    type: str
  fencing:
    description:
      - Fencing mode for the cluster.
    type: str
    choices: ['watchdog', 'hardware', 'both']
  ha:
    description:
      - HA manager settings as a dictionary.
      - Supports C(shutdown_policy) key with values such as C(freeze), C(failover), C(migrate), or C(conditional).
    type: dict
  keyboard:
    description:
      - Default keyboard layout for VNC sessions.
    type: str
  language:
    description:
      - Default GUI language.
    type: str
  max_workers:
    description:
      - Maximum number of parallel worker processes.
    type: int
  state:
    description:
      - The desired state of the cluster options.
    type: str
    choices: ['present']
    default: present
extends_documentation_fragment:
  - sfulmer.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Set cluster console and migration options
  sfulmer.proxmox.proxmox_cluster_options:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    console: html5
    migration: secure
    migration_network: 10.0.0.0/24

- name: Set email and HA settings
  sfulmer.proxmox.proxmox_cluster_options:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    email_from: admin@example.com
    ha:
      shutdown_policy: migrate
    max_workers: 4
'''

RETURN = r'''
options:
  description: The current cluster options after changes.
  type: dict
  returned: always
diff:
  description: Dictionary of changed settings showing before and after values.
  type: dict
  returned: changed
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def _format_ha(ha_dict):
    """Format HA dictionary into the colon-separated string Proxmox expects."""
    if not ha_dict:
        return None
    parts = []
    for key, value in sorted(ha_dict.items()):
        parts.append("{0}={1}".format(key, value))
    return ','.join(parts)


def _parse_ha(ha_string):
    """Parse a Proxmox HA string back into a dictionary."""
    if not ha_string:
        return {}
    result = {}
    for part in ha_string.split(','):
        if '=' in part:
            k, v = part.split('=', 1)
            result[k.strip()] = v.strip()
    return result


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            migration=dict(type='str', choices=['secure', 'insecure']),
            migration_network=dict(type='str'),
            console=dict(type='str', choices=['applet', 'vv', 'html5', 'xtermjs']),
            description=dict(type='str'),
            email_from=dict(type='str'),
            fencing=dict(type='str', choices=['watchdog', 'hardware', 'both']),
            ha=dict(type='dict'),
            keyboard=dict(type='str'),
            language=dict(type='str'),
            max_workers=dict(type='int'),
            state=dict(type='str', choices=['present'], default='present'),
        ),
        supports_check_mode=True,
    )

    try:
        current = module.proxmox_api.cluster.options.get()
    except Exception as e:
        module.fail_json(msg="Failed to get cluster options: {0}".format(e))

    simple_keys = [
        'migration', 'migration_network', 'console', 'description',
        'email_from', 'fencing', 'keyboard', 'language', 'max_workers',
    ]

    changes = {}
    for key in simple_keys:
        desired_value = module.params.get(key)
        if desired_value is not None:
            current_value = current.get(key)
            if current_value is None:
                current_value = ''
            if str(desired_value) != str(current_value):
                changes[key] = desired_value

    # Handle HA dict specially
    desired_ha = module.params.get('ha')
    if desired_ha is not None:
        current_ha_raw = current.get('ha', '')
        if isinstance(current_ha_raw, dict):
            current_ha = current_ha_raw
        else:
            current_ha = _parse_ha(current_ha_raw)
        if desired_ha != current_ha:
            changes['ha'] = _format_ha(desired_ha)

    if not changes:
        module.exit_json(changed=False, options=current)

    diff = {}
    for key in changes:
        if key == 'ha':
            diff[key] = {'before': current.get('ha', ''), 'after': changes[key]}
        else:
            diff[key] = {'before': current.get(key, ''), 'after': changes[key]}

    if module.check_mode:
        module.exit_json(changed=True, options=current, diff=diff)

    try:
        module.proxmox_api.cluster.options.put(**changes)
        updated = module.proxmox_api.cluster.options.get()
    except Exception as e:
        module.fail_json(msg="Failed to update cluster options: {0}".format(e))

    module.exit_json(changed=True, options=updated, diff=diff)


if __name__ == '__main__':
    main()
