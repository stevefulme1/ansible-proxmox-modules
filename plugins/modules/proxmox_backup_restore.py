#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_backup_restore
short_description: Restore a VM or container from a backup on Proxmox VE
version_added: "1.0.0"
description:
  - Restore a virtual machine or LXC container from a backup archive on Proxmox VE.
  - This is an action module that always reports C(changed=True) unless in check mode.
  - Uses C(POST /nodes/{node}/qemu) for VM restores and C(POST /nodes/{node}/lxc) for container restores.
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node to restore the backup on.
    type: str
    required: true
  vmid:
    description:
      - The target VM/container ID for the restored machine.
    type: int
    required: true
  archive:
    description:
      - The volume ID of the backup archive to restore from (e.g. C(local:backup/vzdump-qemu-100-2026_01_01-00_00_00.vma.zst)).
    type: str
    required: true
  storage:
    description:
      - Target storage for the restored disks.
    type: str
  force:
    description:
      - Overwrite an existing VM/container with the same VMID.
    type: bool
  restore_type:
    description:
      - Whether the backup is a VM or LXC container.
    type: str
    choices: ['vm', 'lxc']
    required: true
  pool:
    description:
      - Resource pool to add the restored VM/container to.
    type: str
  bwlimit:
    description:
      - Bandwidth limit in KiB/s for the restore operation. Use 0 for unlimited.
    type: int
extends_documentation_fragment:
  - sfulmer.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Restore a VM from backup
  sfulmer.proxmox.proxmox_backup_restore:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    archive: "local:backup/vzdump-qemu-100-2026_01_01-00_00_00.vma.zst"
    restore_type: vm
    storage: local-lvm
    force: true

- name: Restore an LXC container from backup
  sfulmer.proxmox.proxmox_backup_restore:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 200
    archive: "local:backup/vzdump-lxc-200-2026_01_01-00_00_00.tar.zst"
    restore_type: lxc
    storage: local-lvm
'''

RETURN = r'''
vmid:
  description: The VM/container ID that was restored.
  returned: always
  type: int
  sample: 100
task_id:
  description: The Proxmox task ID for the restore operation.
  returned: on change
  type: str
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            vmid=dict(type='int', required=True),
            archive=dict(type='str', required=True),
            storage=dict(type='str'),
            force=dict(type='bool'),
            restore_type=dict(type='str', required=True, choices=['vm', 'lxc']),
            pool=dict(type='str'),
            bwlimit=dict(type='int'),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    vmid = module.params['vmid']
    archive = module.params['archive']
    restore_type = module.params['restore_type']

    if module.check_mode:
        module.exit_json(changed=True, vmid=vmid)

    proxmox = module.proxmox_api()

    restore_params = dict(
        vmid=vmid,
        archive=archive,
    )

    optional_params = ['storage', 'pool', 'bwlimit']
    for param in optional_params:
        value = module.params[param]
        if value is not None:
            restore_params[param] = value

    if module.params['force'] is not None:
        restore_params['force'] = 1 if module.params['force'] else 0

    try:
        if restore_type == 'vm':
            task_id = proxmox.nodes(node).qemu.post(**restore_params)
        else:
            task_id = proxmox.nodes(node).lxc.post(**restore_params)
    except Exception as e:
        module.fail_json(
            msg="Failed to restore {0} {1} from archive '{2}': {3}".format(
                restore_type, vmid, archive, str(e)
            )
        )

    module.exit_json(changed=True, vmid=vmid, task_id=task_id)


if __name__ == '__main__':
    main()
