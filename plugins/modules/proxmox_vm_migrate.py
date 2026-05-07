#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_migrate
short_description: Migrate a VM to another node in Proxmox VE
description:
  - Perform live or offline migration of a QEMU/KVM virtual machine in Proxmox VE.
  - Uses the C(/nodes/{node}/qemu/{vmid}/migrate) API endpoint.
  - Checks current node location for idempotency. If the VM is already on the target node, no action is taken.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The current Proxmox VE node name where the VM resides.
    type: str
    required: true
  vmid:
    description:
      - The VM ID number.
    type: int
    required: true
  target:
    description:
      - The target node name to migrate the VM to.
    type: str
    required: true
  online:
    description:
      - Whether to perform a live (online) migration.
      - If C(true), the VM remains running during migration.
    type: bool
    default: false
  force:
    description:
      - Allow migration even with local resources (e.g. local disks).
    type: bool
    default: false
  with_local_disks:
    description:
      - Enable live storage migration for local disks.
    type: bool
    default: false
  targetstorage:
    description:
      - Mapping of source storage to target storage for disk migration.
      - Use a single storage name to map all disks to that storage.
    type: str
'''

EXAMPLES = r'''
- name: Live migrate a VM
  stevefulme1.proxmox.proxmox_vm_migrate:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    target: pve2
    online: true

- name: Offline migrate with local disks
  stevefulme1.proxmox.proxmox_vm_migrate:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    target: pve2
    with_local_disks: true
    targetstorage: local-lvm

- name: Force migration
  stevefulme1.proxmox.proxmox_vm_migrate:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    target: pve3
    force: true
'''

RETURN = r'''
vmid:
  description: The VM ID that was migrated.
  returned: success
  type: int
  sample: 100
target:
  description: The target node.
  returned: success
  type: str
  sample: "pve2"
upid:
  description: The task UPID for the migration operation.
  returned: when migration is performed
  type: str
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        node=dict(type='str', required=True),
        vmid=dict(type='int', required=True),
        target=dict(type='str', required=True),
        online=dict(type='bool', default=False),
        force=dict(type='bool', default=False),
        with_local_disks=dict(type='bool', default=False),
        targetstorage=dict(type='str'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    node = params['node']
    vmid = params['vmid']
    target = params['target']
    result = dict(vmid=vmid, target=target)

    # Check if VM is already on the target node
    try:
        vm_status = api.nodes(node).qemu(vmid).status.current.get()
    except Exception:
        # If we cannot find the VM on the specified node, check if it is already on the target
        try:
            vm_status = api.nodes(target).qemu(vmid).status.current.get()
            # VM is already on the target node
            module.exit_json(changed=False, msg="VM %d is already on node '%s'." % (vmid, target), **result)
        except Exception as e:
            module.fail_json(msg="Failed to find VM %d on node '%s' or '%s': %s" % (vmid, node, target, str(e)))

    # If source and target are the same node, no migration needed
    if node == target:
        module.exit_json(changed=False, msg="VM %d is already on node '%s'." % (vmid, target), **result)

    if module.check_mode:
        module.exit_json(changed=True, **result)

    migrate_params = dict(target=target)
    if params['online']:
        migrate_params['online'] = 1
    if params['force']:
        migrate_params['force'] = 1
    if params['with_local_disks']:
        migrate_params['with-local-disks'] = 1
    if params.get('targetstorage'):
        migrate_params['targetstorage'] = params['targetstorage']

    try:
        upid = api.nodes(node).qemu(vmid).migrate.post(**migrate_params)
        result['upid'] = upid
    except Exception as e:
        module.fail_json(msg="Failed to migrate VM %d to node '%s': %s" % (vmid, target, str(e)))

    module.exit_json(changed=True, **result)


if __name__ == '__main__':
    main()
