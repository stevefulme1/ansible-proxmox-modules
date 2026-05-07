#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_ceph_mgr
short_description: Manage Ceph manager daemons on Proxmox VE
description:
  - Create or remove Ceph manager (mgr) daemons on a Proxmox VE node.
  - Uses the Proxmox VE API at C(/nodes/{node}/ceph/mgr/{id}).
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node on which to manage the Ceph manager daemon.
    type: str
    required: true
  mgr_id:
    description:
      - ID of the manager daemon.
      - Defaults to the node name if not specified.
    type: str
  state:
    description:
      - Whether the manager daemon should be present or absent.
    type: str
    choices: [ present, absent ]
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create a Ceph manager daemon using node name as ID
  stevefulme1.proxmox.proxmox_ceph_mgr:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    node: pve1
    state: present

- name: Create a Ceph manager daemon with explicit ID
  stevefulme1.proxmox.proxmox_ceph_mgr:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    node: pve1
    mgr_id: mgr0
    state: present

- name: Remove a Ceph manager daemon
  stevefulme1.proxmox.proxmox_ceph_mgr:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    node: pve1
    mgr_id: mgr0
    state: absent
'''

RETURN = r'''
mgr:
  description: The Ceph manager daemon information returned by the API.
  type: dict
  returned: on success when state is present
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            mgr_id=dict(type='str'),
            state=dict(
                type='str',
                choices=['present', 'absent'],
                default='present',
            ),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    mgr_id = module.params['mgr_id'] or node
    state = module.params['state']

    # List existing manager daemons
    existing = module.proxmox_api_call(
        'GET', '/nodes/{node}/ceph/mgr', node=node
    )

    current = None
    if existing is not None:
        for mgr in existing:
            if mgr.get('name') == mgr_id or mgr.get('id') == mgr_id:
                current = mgr
                break

    if state == 'present':
        if current is not None:
            module.exit_json(changed=False, mgr=current)

        if module.check_mode:
            module.exit_json(changed=True)

        result = module.proxmox_api_call(
            'POST', '/nodes/{node}/ceph/mgr/{id}',
            node=node, id=mgr_id,
        )
        module.exit_json(changed=True, mgr=result)

    else:  # absent
        if current is None:
            module.exit_json(changed=False)

        if module.check_mode:
            module.exit_json(changed=True)

        module.proxmox_api_call(
            'DELETE', '/nodes/{node}/ceph/mgr/{id}',
            node=node, id=mgr_id,
        )
        module.exit_json(changed=True)


if __name__ == '__main__':
    main()
