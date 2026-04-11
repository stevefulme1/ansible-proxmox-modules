#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_lxc_migrate
short_description: Migrate an LXC container to another node on Proxmox VE
version_added: "1.0.0"
description:
  - Migrate an LXC container from one Proxmox VE node to another.
  - Idempotent; if the container already resides on the target node, no action is taken.
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node on which the container currently resides.
    type: str
    required: true
  vmid:
    description:
      - The unique ID of the container to migrate.
    type: int
    required: true
  target:
    description:
      - The target Proxmox VE node to migrate the container to.
    type: str
    required: true
  online:
    description:
      - Perform an online (live) migration.
    type: bool
  restart:
    description:
      - Allow restart of the container during migration for local-bound containers.
    type: bool
  force:
    description:
      - Force migration even if the container has local resources that cannot be migrated.
    type: bool
  targetstorage:
    description:
      - Mapping of source storage to target storage. Format C(source:target) or a single storage name.
    type: str
extends_documentation_fragment:
  - sfulmer.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Migrate container to another node
  sfulmer.proxmox.proxmox_lxc_migrate:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    target: pve2

- name: Online migration with target storage
  sfulmer.proxmox.proxmox_lxc_migrate:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    target: pve2
    online: true
    targetstorage: local-lvm
'''

RETURN = r'''
vmid:
  description: The container ID that was migrated.
  returned: always
  type: int
  sample: 100
target:
  description: The target node.
  returned: always
  type: str
  sample: pve2
task_id:
  description: The Proxmox task ID for the migration.
  returned: on change
  type: str
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            vmid=dict(type='int', required=True),
            target=dict(type='str', required=True),
            online=dict(type='bool'),
            restart=dict(type='bool'),
            force=dict(type='bool'),
            targetstorage=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    vmid = module.params['vmid']
    target = module.params['target']

    proxmox = module.proxmox_api()

    # Check current location of the container for idempotency
    try:
        resources = proxmox.cluster.resources.get(type='vm')
        current_node = None
        for resource in resources:
            if int(resource.get('vmid', 0)) == vmid:
                current_node = resource.get('node')
                break
        if current_node is None:
            module.fail_json(msg="Container {0} not found in cluster".format(vmid))
    except Exception as e:
        module.fail_json(msg="Failed to query cluster resources: {0}".format(str(e)))

    if current_node == target:
        module.exit_json(changed=False, vmid=vmid, target=target,
                         msg="Container {0} is already on node {1}".format(vmid, target))

    if module.check_mode:
        module.exit_json(changed=True, vmid=vmid, target=target)

    migrate_params = dict(target=target)
    bool_params = ['online', 'restart', 'force']
    for param in bool_params:
        value = module.params[param]
        if value is not None:
            migrate_params[param] = 1 if value else 0

    if module.params['targetstorage'] is not None:
        migrate_params['targetstorage'] = module.params['targetstorage']

    try:
        task_id = proxmox.nodes(node).lxc(vmid).migrate.post(**migrate_params)
    except Exception as e:
        module.fail_json(msg="Failed to migrate container {0} to {1}: {2}".format(vmid, target, str(e)))

    module.exit_json(changed=True, vmid=vmid, target=target, task_id=task_id)


if __name__ == '__main__':
    main()
