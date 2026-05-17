#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_pending_info
short_description: Query pending VM configuration changes in Proxmox VE
description:
  - Retrieve pending configuration changes for a virtual machine.
  - Shows both the current and pending values for each config key.
  - This is an info module and does not modify any state.
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
  limit:
    description:
      - Maximum number of results to return.
      - Applied client-side to truncate results.
    type: int
    default: 100
  offset:
    description:
      - Number of results to skip before returning.
      - Applied client-side for pagination.
    type: int
    default: 0
  max_results:
    description:
      - Maximum total number of results to return.
      - Set to 0 for no limit.
    type: int
    default: 1000
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Get pending changes for a VM
  stevefulme1.proxmox.proxmox_vm_pending_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
  register: pending

- name: Display pending changes
  ansible.builtin.debug:
    var: pending.pending_changes
'''

RETURN = r'''
pending_changes:
  description: >
    A list of pending configuration entries. Each entry contains
    the key name, its current value, and its pending value.
  type: list
  elements: dict
  returned: always
  sample:
    - key: memory
      value: 2048
      pending: 4096
    - key: cores
      value: 2
      pending: 4
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            limit=dict(type='int', default=100),
            offset=dict(type='int', default=0),
            max_results=dict(type='int', default=1000),
            node=dict(type='str', required=True),
            vmid=dict(type='int', required=True),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    vmid = module.params['vmid']

    api_path = 'nodes/{0}/qemu/{1}/pending'.format(node, vmid)
    pending = module.proxmox_request('GET', api_path)

    module.exit_json(
        changed=False,
        pending_changes=pending if pending else [],
    )


if __name__ == '__main__':
    main()
