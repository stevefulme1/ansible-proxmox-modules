#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_ceph_fs
short_description: Manage CephFS filesystems on Proxmox VE
description:
  - Create or remove CephFS filesystems on a Proxmox VE node.
  - Uses the Proxmox VE API at C(/nodes/{node}/ceph/fs).
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node on which to manage the CephFS filesystem.
    type: str
    required: true
  name:
    description:
      - Name of the CephFS filesystem.
    type: str
    required: true
  pg_num:
    description:
      - Number of placement groups for the CephFS data pool.
    type: int
  add_storage:
    description:
      - Whether to add the CephFS as a Proxmox storage entry automatically.
    type: bool
  state:
    description:
      - Whether the CephFS filesystem should be present or absent.
    type: str
    choices: [ present, absent ]
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create a CephFS filesystem
  stevefulme1.proxmox.proxmox_ceph_fs:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    node: pve1
    name: myfs
    pg_num: 64
    add_storage: true
    state: present

- name: Remove a CephFS filesystem
  stevefulme1.proxmox.proxmox_ceph_fs:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    node: pve1
    name: myfs
    state: absent
'''

RETURN = r'''
filesystem:
  description: The CephFS filesystem information returned by the API.
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
            pg_num=dict(type='int'),
            add_storage=dict(type='bool'),
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
    pg_num = module.params['pg_num']
    add_storage = module.params['add_storage']
    state = module.params['state']

    # Fetch existing CephFS filesystems
    existing = module.proxmox_api_call(
        'GET', '/nodes/{node}/ceph/fs', node=node
    )

    current = None
    if existing is not None:
        for fs in existing:
            if fs.get('name') == name:
                current = fs
                break

    if state == 'present':
        if current is not None:
            module.exit_json(changed=False, filesystem=current)

        if module.check_mode:
            module.exit_json(changed=True)

        params = {'name': name}
        if pg_num is not None:
            params['pg_num'] = pg_num
        if add_storage is not None:
            params['add-storage'] = int(add_storage)

        result = module.proxmox_api_call(
            'POST', '/nodes/{node}/ceph/fs', node=node, **params
        )
        module.exit_json(changed=True, filesystem=result)

    else:  # absent
        if current is None:
            module.exit_json(changed=False)

        if module.check_mode:
            module.exit_json(changed=True)

        module.proxmox_api_call(
            'DELETE', '/nodes/{node}/ceph/fs/{name}',
            node=node, name=name,
        )
        module.exit_json(changed=True)


if __name__ == '__main__':
    main()
