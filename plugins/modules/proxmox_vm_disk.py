#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_disk
short_description: Manage individual VM disks in Proxmox VE
description:
  - Resize, move, or import disks for a virtual machine in Proxmox VE.
  - This is an action module; idempotency depends on the specific action.
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
  disk:
    description:
      - The disk identifier (e.g. C(scsi0), C(virtio0), C(ide2)).
    type: str
    required: true
  action:
    description:
      - The disk operation to perform.
    type: str
    required: true
    choices:
      - resize
      - move
      - import
  size:
    description:
      - The new size or size increment for the C(resize) action.
      - Use C(+10G) to add 10 GiB or C(50G) for an absolute size.
    type: str
  storage:
    description:
      - Target storage for the C(move) action.
    type: str
  source:
    description:
      - Path to the disk image file for the C(import) action.
    type: str
  format:
    description:
      - Disk image format.
    type: str
    choices:
      - raw
      - qcow2
      - vmdk
  delete:
    description:
      - Whether to delete the source disk after a C(move) operation.
    type: bool
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Resize a disk by 10G
  stevefulme1.proxmox.proxmox_vm_disk:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    disk: scsi0
    action: resize
    size: "+10G"

- name: Move a disk to different storage
  stevefulme1.proxmox.proxmox_vm_disk:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    disk: scsi0
    action: move
    storage: local-lvm
    delete: true

- name: Import a disk image
  stevefulme1.proxmox.proxmox_vm_disk:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    disk: scsi1
    action: import
    source: /var/lib/vz/images/focal-server-cloudimg-amd64.img
    storage: local-lvm
    format: raw
'''

RETURN = r'''
vmid:
  description: The VM ID whose disk was managed.
  type: int
  returned: always
  sample: 100
disk:
  description: The disk identifier that was managed.
  type: str
  returned: always
  sample: scsi0
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "Disk 'scsi0' resized successfully on VM 100."
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


def _do_resize(module, node, vmid, disk, size):
    """Resize a VM disk."""
    api_path = 'nodes/{0}/qemu/{1}/resize'.format(node, vmid)
    data = {'disk': disk, 'size': size}
    module.proxmox_request('PUT', api_path, data=data)
    return "Disk '{0}' resized successfully on VM {1}.".format(disk, vmid)


def _do_move(module, node, vmid, disk, storage, delete_source):
    """Move a VM disk to another storage."""
    api_path = 'nodes/{0}/qemu/{1}/move_disk'.format(node, vmid)
    data = {'disk': disk, 'storage': storage}
    if delete_source:
        data['delete'] = 1
    module.proxmox_request('POST', api_path, data=data)
    return "Disk '{0}' moved to storage '{1}' on VM {2}.".format(
        disk, storage, vmid,
    )


def _do_import(module, node, vmid, disk, source, storage, fmt):
    """Import an external disk image."""
    api_path = 'nodes/{0}/qemu/{1}/config'.format(node, vmid)
    import_str = '{0}:0,import-from={1}'.format(storage, source)
    if fmt:
        import_str += ',format={0}'.format(fmt)
    data = {disk: import_str}
    module.proxmox_request('PUT', api_path, data=data)
    return "Disk image imported to '{0}' on VM {1}.".format(disk, vmid)


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            vmid=dict(type='int', required=True),
            disk=dict(type='str', required=True),
            action=dict(
                type='str', required=True,
                choices=['resize', 'move', 'import'],
            ),
            size=dict(type='str'),
            storage=dict(type='str'),
            source=dict(type='str'),
            format=dict(type='str', choices=['raw', 'qcow2', 'vmdk']),
            delete=dict(type='bool'),
        ),
        required_if=[
            ('action', 'resize', ['size']),
            ('action', 'move', ['storage']),
            ('action', 'import', ['source', 'storage']),
        ],
        supports_check_mode=True,
    )

    node = module.params['node']
    vmid = module.params['vmid']
    disk = module.params['disk']
    action = module.params['action']

    if module.check_mode:
        module.exit_json(
            changed=True, vmid=vmid, disk=disk,
            msg="Disk '{0}' {1} would be performed on VM {2}.".format(
                disk, action, vmid,
            ),
        )

    if action == 'resize':
        msg = _do_resize(module, node, vmid, disk, module.params['size'])
    elif action == 'move':
        msg = _do_move(
            module, node, vmid, disk,
            module.params['storage'],
            module.params.get('delete', False),
        )
    elif action == 'import':
        msg = _do_import(
            module, node, vmid, disk,
            module.params['source'],
            module.params['storage'],
            module.params.get('format'),
        )

    module.exit_json(changed=True, vmid=vmid, disk=disk, msg=msg)


if __name__ == '__main__':
    main()
