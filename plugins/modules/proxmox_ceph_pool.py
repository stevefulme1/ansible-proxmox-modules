#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_ceph_pool
short_description: Manage Proxmox VE Ceph pools
description:
  - Create, update, and destroy Ceph pools on Proxmox VE nodes.
  - Uses the C(/nodes/{node}/ceph/pool) API endpoints.
  - Compares existing pool configuration to desired state for idempotency.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The name of the Proxmox VE node to manage Ceph pools on.
    type: str
    required: true
  name:
    description:
      - The name of the Ceph pool.
    type: str
    required: true
  size:
    description:
      - Number of replicas per object.
    type: int
  min_size:
    description:
      - Minimum number of replicas required for I/O.
    type: int
  pg_num:
    description:
      - Number of placement groups for the pool.
    type: int
  pg_autoscale_mode:
    description:
      - PG autoscale mode.
    type: str
    choices: ['on', 'off', 'warn']
  crush_rule:
    description:
      - The CRUSH rule to use for the pool.
    type: str
  application:
    description:
      - The application tag for the pool.
    type: str
    choices: ['rbd', 'cephfs', 'rgw']
  add_storages:
    description:
      - Whether to automatically add the pool as a Proxmox storage.
    type: bool
  state:
    description:
      - Whether the Ceph pool should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create a Ceph pool with 3 replicas
  stevefulme1.proxmox.proxmox_ceph_pool:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    name: mypool
    size: 3
    min_size: 2
    pg_autoscale_mode: "on"
    application: rbd

- name: Update pool settings
  stevefulme1.proxmox.proxmox_ceph_pool:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    name: mypool
    size: 2
    min_size: 1

- name: Remove a Ceph pool
  stevefulme1.proxmox.proxmox_ceph_pool:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    name: mypool
    state: absent
'''

RETURN = r'''
name:
  description: The name of the Ceph pool.
  type: str
  returned: always
pool:
  description: The pool configuration after changes.
  type: dict
  returned: success and state is present
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            name=dict(type='str', required=True),
            size=dict(type='int'),
            min_size=dict(type='int'),
            pg_num=dict(type='int'),
            pg_autoscale_mode=dict(type='str', choices=['on', 'off', 'warn']),
            crush_rule=dict(type='str'),
            application=dict(type='str', choices=['rbd', 'cephfs', 'rgw']),
            add_storages=dict(type='bool'),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    name = module.params['name']
    state = module.params['state']

    # Get list of existing pools
    try:
        pools = module.proxmox_api.nodes(node).ceph.pool.get()
    except Exception as e:
        module.fail_json(msg="Failed to list Ceph pools on node '{0}': {1}".format(node, e))

    current = None
    for pool in pools:
        if pool.get('pool_name') == name or pool.get('name') == name:
            current = pool
            break

    if state == 'absent':
        if current is None:
            module.exit_json(changed=False, name=name)

        if module.check_mode:
            module.exit_json(changed=True, name=name)

        try:
            module.proxmox_api.nodes(node).ceph.pool(name).delete()
        except Exception as e:
            module.fail_json(
                msg="Failed to delete Ceph pool '{0}' on node '{1}': {2}".format(name, node, e)
            )

        module.exit_json(changed=True, name=name)

    # state == present
    config_map = {
        'size': 'size',
        'min_size': 'min_size',
        'pg_num': 'pg_num',
        'pg_autoscale_mode': 'pg_autoscale_mode',
        'crush_rule': 'crush_rule',
        'application': 'application',
    }

    if current is not None:
        # Pool exists, check if update is needed
        changes = {}
        for param_key, api_key in config_map.items():
            desired_value = module.params.get(param_key)
            if desired_value is not None:
                current_value = current.get(api_key)
                if current_value is None:
                    current_value = current.get(param_key)
                if current_value is not None:
                    if str(desired_value) != str(current_value):
                        changes[api_key] = desired_value
                else:
                    changes[api_key] = desired_value

        if not changes:
            module.exit_json(changed=False, name=name, pool=current)

        if module.check_mode:
            module.exit_json(changed=True, name=name, pool=current)

        try:
            module.proxmox_api.nodes(node).ceph.pool(name).put(**changes)
        except Exception as e:
            module.fail_json(
                msg="Failed to update Ceph pool '{0}' on node '{1}': {2}".format(name, node, e)
            )
    else:
        # Create new pool
        if module.check_mode:
            module.exit_json(changed=True, name=name)

        create_params = {'name': name}
        for param_key, api_key in config_map.items():
            value = module.params.get(param_key)
            if value is not None:
                create_params[api_key] = value

        if module.params.get('add_storages') is not None:
            create_params['add_storages'] = int(module.params['add_storages'])

        try:
            module.proxmox_api.nodes(node).ceph.pool.post(**create_params)
        except Exception as e:
            module.fail_json(
                msg="Failed to create Ceph pool '{0}' on node '{1}': {2}".format(name, node, e)
            )

    # Fetch updated pool info
    try:
        pools = module.proxmox_api.nodes(node).ceph.pool.get()
        updated = None
        for pool in pools:
            if pool.get('pool_name') == name or pool.get('name') == name:
                updated = pool
                break
    except Exception:
        updated = None

    module.exit_json(changed=True, name=name, pool=updated)


if __name__ == '__main__':
    main()
