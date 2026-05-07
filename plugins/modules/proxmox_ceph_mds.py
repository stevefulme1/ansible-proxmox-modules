#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_ceph_mds
short_description: Manage Ceph MDS daemons on Proxmox VE
description:
  - Create or remove Ceph Metadata Server (MDS) daemons on a Proxmox VE node.
  - Uses the Proxmox VE API at C(/nodes/{node}/ceph/mds/{name}).
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node on which to manage the MDS daemon.
    type: str
    required: true
  name:
    description:
      - Name of the MDS daemon.
    type: str
    required: true
  hotstandby:
    description:
      - Whether this MDS should be configured as a hot standby.
    type: bool
  state:
    description:
      - Whether the MDS daemon should be present or absent.
    type: str
    choices: [ present, absent ]
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create a Ceph MDS daemon
  stevefulme1.proxmox.proxmox_ceph_mds:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    node: pve1
    name: mds0
    hotstandby: true
    state: present

- name: Remove a Ceph MDS daemon
  stevefulme1.proxmox.proxmox_ceph_mds:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    node: pve1
    name: mds0
    state: absent
'''

RETURN = r'''
mds:
  description: The MDS daemon information returned by the API.
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
            name=dict(type='str', required=True),
            hotstandby=dict(type='bool'),
            state=dict(
                type='str',
                choices=['present', 'absent'],
                default='present',
            ),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    name = module.params['name']
    hotstandby = module.params['hotstandby']
    state = module.params['state']

    # List existing MDS daemons
    existing = module.proxmox_api_call(
        'GET', '/nodes/{node}/ceph/mds', node=node
    )

    current = None
    if existing is not None:
        for mds in existing:
            if mds.get('name') == name:
                current = mds
                break

    if state == 'present':
        if current is not None:
            module.exit_json(changed=False, mds=current)

        if module.check_mode:
            module.exit_json(changed=True)

        params = {}
        if hotstandby is not None:
            params['hotstandby'] = int(hotstandby)

        result = module.proxmox_api_call(
            'POST', '/nodes/{node}/ceph/mds/{name}',
            node=node, name=name, **params
        )
        module.exit_json(changed=True, mds=result)

    else:  # absent
        if current is None:
            module.exit_json(changed=False)

        if module.check_mode:
            module.exit_json(changed=True)

        module.proxmox_api_call(
            'DELETE', '/nodes/{node}/ceph/mds/{name}',
            node=node, name=name,
        )
        module.exit_json(changed=True)


if __name__ == '__main__':
    main()
