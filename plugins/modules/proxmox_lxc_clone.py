#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_lxc_clone
short_description: Clone an LXC container on Proxmox VE
version_added: "1.0.0"
description:
  - Clone an existing LXC container to a new container on Proxmox VE.
  - If the target container ID already exists, the module will not attempt to clone again (idempotent).
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node on which the source container resides.
    type: str
    required: true
  vmid:
    description:
      - The unique ID of the source container to clone.
    type: int
    required: true
  newid:
    description:
      - The unique ID for the new cloned container.
    type: int
    required: true
  hostname:
    description:
      - Hostname for the new container.
    type: str
  description:
    description:
      - Description for the new container.
    type: str
  target:
    description:
      - Target node for the clone. Defaults to the source node if not specified.
    type: str
  full:
    description:
      - Create a full copy of all disks. If false, a linked clone is created.
    type: bool
  storage:
    description:
      - Target storage for the full clone.
    type: str
  pool:
    description:
      - Resource pool to add the new container to.
    type: str
extends_documentation_fragment:
  - sfulmer.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Clone container 100 to 200
  sfulmer.proxmox.proxmox_lxc_clone:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    newid: 200
    hostname: clone-webserver
    full: true
    storage: local-lvm

- name: Linked clone to another node
  sfulmer.proxmox.proxmox_lxc_clone:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    newid: 201
    target: pve2
'''

RETURN = r'''
vmid:
  description: The source container ID.
  returned: always
  type: int
  sample: 100
newid:
  description: The new container ID.
  returned: always
  type: int
  sample: 200
task_id:
  description: The Proxmox task ID for the clone operation.
  returned: on change
  type: str
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            vmid=dict(type='int', required=True),
            newid=dict(type='int', required=True),
            hostname=dict(type='str'),
            description=dict(type='str'),
            target=dict(type='str'),
            full=dict(type='bool'),
            storage=dict(type='str'),
            pool=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    vmid = module.params['vmid']
    newid = module.params['newid']

    proxmox = module.proxmox_api()

    # Check if the target container already exists on any node
    try:
        resources = proxmox.cluster.resources.get(type='vm')
        for resource in resources:
            if int(resource.get('vmid', 0)) == newid:
                module.exit_json(changed=False, vmid=vmid, newid=newid,
                                 msg="Container {0} already exists".format(newid))
    except Exception as e:
        module.fail_json(msg="Failed to query cluster resources: {0}".format(str(e)))

    if module.check_mode:
        module.exit_json(changed=True, vmid=vmid, newid=newid)

    clone_params = dict(newid=newid)
    optional_params = ['hostname', 'description', 'target', 'full', 'storage', 'pool']
    for param in optional_params:
        value = module.params[param]
        if value is not None:
            if isinstance(value, bool):
                clone_params[param] = 1 if value else 0
            else:
                clone_params[param] = value

    try:
        task_id = proxmox.nodes(node).lxc(vmid).clone.post(**clone_params)
    except Exception as e:
        module.fail_json(msg="Failed to clone container {0} to {1}: {2}".format(vmid, newid, str(e)))

    module.exit_json(changed=True, vmid=vmid, newid=newid, task_id=task_id)


if __name__ == '__main__':
    main()
