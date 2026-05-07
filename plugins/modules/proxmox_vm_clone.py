#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_clone
short_description: Clone a VM in Proxmox VE
description:
  - Clone an existing QEMU/KVM virtual machine in Proxmox VE.
  - Uses the C(/nodes/{node}/qemu/{vmid}/clone) API endpoint.
  - This module always reports C(changed=True) unless running in check mode.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node name where the source VM resides.
    type: str
    required: true
  vmid:
    description:
      - The source VM ID to clone from.
    type: int
    required: true
  newid:
    description:
      - The VM ID for the new cloned VM.
    type: int
    required: true
  name:
    description:
      - Name for the new cloned VM.
    type: str
  description:
    description:
      - Description for the new cloned VM.
    type: str
  target:
    description:
      - Target node for the clone. If not specified, the clone is created on the same node.
    type: str
  full:
    description:
      - Whether to create a full clone (C(true)) or a linked clone (C(false)).
      - Full clones are independent copies; linked clones share the base image.
    type: bool
  storage:
    description:
      - Target storage for the clone's disks.
    type: str
  pool:
    description:
      - Resource pool to add the cloned VM to.
    type: str
  format:
    description:
      - Target format for the cloned disk (e.g. C(qcow2), C(raw), C(vmdk)).
    type: str
    choices: ['qcow2', 'raw', 'vmdk']
'''

EXAMPLES = r'''
- name: Create a full clone
  stevefulme1.proxmox.proxmox_vm_clone:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    newid: 200
    name: webserver-clone
    full: true
    storage: local-lvm

- name: Create a linked clone
  stevefulme1.proxmox.proxmox_vm_clone:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    newid: 201
    name: webserver-linked
    full: false

- name: Clone to a different node
  stevefulme1.proxmox.proxmox_vm_clone:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    newid: 202
    target: pve2
    full: true
'''

RETURN = r'''
vmid:
  description: The source VM ID.
  returned: success
  type: int
  sample: 100
newid:
  description: The new cloned VM ID.
  returned: success
  type: int
  sample: 200
upid:
  description: The task UPID for the clone operation.
  returned: when not in check mode
  type: str
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        node=dict(type='str', required=True),
        vmid=dict(type='int', required=True),
        newid=dict(type='int', required=True),
        name=dict(type='str'),
        description=dict(type='str'),
        target=dict(type='str'),
        full=dict(type='bool'),
        storage=dict(type='str'),
        pool=dict(type='str'),
        format=dict(type='str', choices=['qcow2', 'raw', 'vmdk']),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    node = params['node']
    vmid = params['vmid']
    newid = params['newid']
    result = dict(vmid=vmid, newid=newid)

    if module.check_mode:
        module.exit_json(changed=True, **result)

    clone_params = dict(newid=newid)

    optional_keys = ['name', 'description', 'target', 'storage', 'pool', 'format']
    for key in optional_keys:
        if params.get(key) is not None:
            clone_params[key] = params[key]

    if params.get('full') is not None:
        clone_params['full'] = int(params['full'])

    try:
        upid = api.nodes(node).qemu(vmid).clone.post(**clone_params)
        result['upid'] = upid
    except Exception as e:
        module.fail_json(msg="Failed to clone VM %d to %d: %s" % (vmid, newid, str(e)))

    module.exit_json(changed=True, **result)


if __name__ == '__main__':
    main()
