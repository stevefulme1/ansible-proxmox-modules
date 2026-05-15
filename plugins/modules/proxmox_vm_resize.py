#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_resize
short_description: Resize a VM disk in Proxmox VE
description:
  - Resize (grow) a virtual machine disk in Proxmox VE.
  - Supports both relative sizes (e.g. C(+10G)) and absolute sizes (e.g. C(50G)).
  - Only growing disks is supported by the Proxmox API; shrinking is not allowed.
  - The disk must already exist on the VM.
version_added: "1.1.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node the VM resides on.
    type: str
    required: true
  vmid:
    description:
      - The numeric ID of the virtual machine.
    type: int
    required: true
  disk:
    description:
      - The disk identifier to resize (e.g. C(scsi0), C(virtio0), C(ide0), C(sata0)).
    type: str
    required: true
  size:
    description:
      - The new size or size increment.
      - Use a C(+) prefix for relative growth (e.g. C(+10G), C(+512M)).
      - Use an absolute value to set the total size (e.g. C(50G)).
      - The Proxmox API only supports growing disks, not shrinking.
    type: str
    required: true
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Grow a SCSI disk by 10GB
  stevefulme1.proxmox.proxmox_vm_resize:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    disk: scsi0
    size: "+10G"

- name: Set disk to an absolute size of 50GB
  stevefulme1.proxmox.proxmox_vm_resize:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    vmid: 100
    disk: virtio0
    size: "50G"
'''

RETURN = r'''
vmid:
  description: The VM ID that was resized.
  type: int
  returned: always
  sample: 100
disk:
  description: The disk that was resized.
  type: str
  returned: always
  sample: scsi0
size:
  description: The size parameter that was applied.
  type: str
  returned: always
  sample: "+10G"
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "Disk scsi0 on VM 100 resized successfully."
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            vmid=dict(type='int', required=True),
            disk=dict(type='str', required=True),
            size=dict(type='str', required=True),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    vmid = module.params['vmid']
    disk = module.params['disk']
    size = module.params['size']

    api = module.get_api()

    # Verify the disk exists on the VM
    try:
        config = api.nodes(node).qemu(vmid).config.get()
    except Exception as e:
        module.fail_json(msg="Failed to get VM {0} config on node '{1}': {2}".format(vmid, node, e))

    if disk not in config:
        module.fail_json(
            msg="Disk '{0}' does not exist on VM {1}. Available disks: {2}".format(
                disk, vmid, ', '.join(sorted(k for k in config if k.startswith(('scsi', 'virtio', 'ide', 'sata'))))
            )
        )

    if module.check_mode:
        module.exit_json(changed=True, vmid=vmid, disk=disk, size=size, msg="Disk {0} on VM {1} would be resized.".format(disk, vmid))

    try:
        api.nodes(node).qemu(vmid).resize.put(disk=disk, size=size)
    except Exception as e:
        module.fail_json(msg="Failed to resize disk '{0}' on VM {1}: {2}".format(disk, vmid, e))

    module.exit_json(
        changed=True,
        vmid=vmid,
        disk=disk,
        size=size,
        msg="Disk {0} on VM {1} resized successfully.".format(disk, vmid),
    )


if __name__ == '__main__':
    main()
