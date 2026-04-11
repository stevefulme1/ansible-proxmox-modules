#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_firewall
short_description: Manage per-VM firewall options in Proxmox VE
description:
  - Configure firewall options for a specific virtual machine in Proxmox VE.
  - Compares current settings and only applies changes when needed.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox node the VM resides on.
    type: str
    required: true
  vmid:
    description:
      - The VM ID.
    type: int
    required: true
  enable:
    description:
      - Enable or disable the firewall for this VM.
    type: bool
  dhcp:
    description:
      - Enable DHCP packets to pass through the firewall.
    type: bool
  ipfilter:
    description:
      - Enable IP filter for the VM.
    type: bool
  log_level_in:
    description:
      - Log level for incoming traffic.
    type: str
    choices:
      - emerg
      - alert
      - crit
      - err
      - warning
      - notice
      - info
      - debug
      - nolog
  log_level_out:
    description:
      - Log level for outgoing traffic.
    type: str
    choices:
      - emerg
      - alert
      - crit
      - err
      - warning
      - notice
      - info
      - debug
      - nolog
  macfilter:
    description:
      - Enable MAC address filter.
    type: bool
  ndp:
    description:
      - Enable NDP (Neighbor Discovery Protocol).
    type: bool
  policy_in:
    description:
      - Default policy for incoming traffic.
    type: str
    choices:
      - ACCEPT
      - REJECT
      - DROP
  policy_out:
    description:
      - Default policy for outgoing traffic.
    type: str
    choices:
      - ACCEPT
      - REJECT
      - DROP
  radv:
    description:
      - Enable Router Advertisement.
    type: bool
  state:
    description:
      - Only C(present) is supported for firewall options.
    type: str
    default: present
    choices:
      - present
extends_documentation_fragment:
  - sfulmer.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Enable firewall with DROP policy for incoming
  sfulmer.proxmox.proxmox_vm_firewall:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    enable: true
    policy_in: DROP
    policy_out: ACCEPT
    state: present

- name: Configure logging and MAC filter
  sfulmer.proxmox.proxmox_vm_firewall:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    log_level_in: info
    log_level_out: warning
    macfilter: true
    state: present
'''

RETURN = r'''
vmid:
  description: The VM ID whose firewall was configured.
  type: int
  returned: always
  sample: 100
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "Firewall options updated for VM 100."
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


LOG_CHOICES = [
    'emerg', 'alert', 'crit', 'err', 'warning',
    'notice', 'info', 'debug', 'nolog',
]

FIREWALL_PARAMS = [
    'enable', 'dhcp', 'ipfilter', 'log_level_in', 'log_level_out',
    'macfilter', 'ndp', 'policy_in', 'policy_out', 'radv',
]

PARAM_API_MAP = {
    'log_level_in': 'log_level_in',
    'log_level_out': 'log_level_out',
}


def _build_desired(module):
    """Build desired config from module params, skipping None values."""
    desired = {}
    for key in FIREWALL_PARAMS:
        value = module.params.get(key)
        if value is None:
            continue
        api_key = PARAM_API_MAP.get(key, key)
        if isinstance(value, bool):
            desired[api_key] = int(value)
        else:
            desired[api_key] = value
    return desired


def _needs_update(current, desired):
    """Return True if any desired value differs from current."""
    for key, value in desired.items():
        current_value = current.get(key)
        if current_value is None and value is not None:
            return True
        if str(current_value) != str(value):
            return True
    return False


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            vmid=dict(type='int', required=True),
            enable=dict(type='bool'),
            dhcp=dict(type='bool'),
            ipfilter=dict(type='bool'),
            log_level_in=dict(type='str', choices=LOG_CHOICES),
            log_level_out=dict(type='str', choices=LOG_CHOICES),
            macfilter=dict(type='bool'),
            ndp=dict(type='bool'),
            policy_in=dict(
                type='str', choices=['ACCEPT', 'REJECT', 'DROP'],
            ),
            policy_out=dict(
                type='str', choices=['ACCEPT', 'REJECT', 'DROP'],
            ),
            radv=dict(type='bool'),
            state=dict(type='str', default='present', choices=['present']),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    vmid = module.params['vmid']

    api_path = 'nodes/{0}/qemu/{1}/firewall/options'.format(node, vmid)

    current = module.proxmox_request('GET', api_path)
    desired = _build_desired(module)

    if not desired:
        module.exit_json(
            changed=False, vmid=vmid,
            msg="No firewall options specified to change.",
        )

    changed = _needs_update(current, desired)

    if changed and not module.check_mode:
        module.proxmox_request('PUT', api_path, data=desired)

    msg = (
        "Firewall options updated for VM {0}.".format(vmid)
        if changed
        else "Firewall options already up to date for VM {0}.".format(vmid)
    )

    module.exit_json(changed=changed, vmid=vmid, msg=msg)


if __name__ == '__main__':
    main()
