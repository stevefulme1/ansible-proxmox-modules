#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_create
short_description: Create a QEMU/KVM virtual machine in Proxmox VE
description:
  - Create a new QEMU/KVM virtual machine from scratch (not clone) in Proxmox VE.
  - Supports specifying CPU, memory, disk, network, and boot configuration.
  - If I(vmid) is not provided, Proxmox will auto-assign the next available ID.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node on which to create the VM.
    type: str
    required: true
  vmid:
    description:
      - The VM ID to assign. If not specified, the next available ID is used.
    type: int
  name:
    description:
      - The name of the virtual machine.
    type: str
  memory:
    description:
      - Amount of RAM in MiB.
    type: int
    default: 2048
  cores:
    description:
      - Number of CPU cores per socket.
    type: int
    default: 1
  sockets:
    description:
      - Number of CPU sockets.
    type: int
    default: 1
  cpu_type:
    description:
      - The CPU type to emulate (e.g. C(host), C(kvm64), C(qemu64)).
    type: str
    default: kvm64
  ostype:
    description:
      - The OS type identifier (e.g. C(l26) for Linux 2.6+, C(win10) for Windows 10).
    type: str
    default: l26
  scsi0:
    description:
      - SCSI disk specification (e.g. C(local-lvm:32) for a 32 GiB disk on local-lvm).
    type: str
  ide2:
    description:
      - IDE device specification, typically used for CD-ROM (e.g. C(local:iso/ubuntu.iso,media=cdrom)).
    type: str
  net0:
    description:
      - Network device specification (e.g. C(virtio,bridge=vmbr0)).
    type: str
  boot:
    description:
      - Boot order specification (e.g. C(order=scsi0;ide2;net0)).
    type: str
  start_after_create:
    description:
      - Whether to start the VM immediately after creation.
    type: bool
    default: false
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create a basic Linux VM
  stevefulme1.proxmox.proxmox_vm_create:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    name: my-linux-vm
    memory: 4096
    cores: 2
    scsi0: "local-lvm:32"
    net0: "virtio,bridge=vmbr0"
    start_after_create: true

- name: Create a VM with auto-assigned VMID and CD-ROM
  stevefulme1.proxmox.proxmox_vm_create:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    name: installer-vm
    memory: 2048
    cores: 1
    scsi0: "local-lvm:20"
    ide2: "local:iso/ubuntu-22.04.iso,media=cdrom"
    boot: "order=ide2;scsi0"
'''

RETURN = r'''
vmid:
  description: The VM ID of the created virtual machine.
  type: int
  returned: always
  sample: 100
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "VM 100 created successfully on node pve1."
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


def main():
    module_args = dict(
        node=dict(type='str', required=True),
        vmid=dict(type='int'),
        name=dict(type='str'),
        memory=dict(type='int', default=2048),
        cores=dict(type='int', default=1),
        sockets=dict(type='int', default=1),
        cpu_type=dict(type='str', default='kvm64'),
        ostype=dict(type='str', default='l26'),
        scsi0=dict(type='str'),
        ide2=dict(type='str'),
        net0=dict(type='str'),
        boot=dict(type='str'),
        start_after_create=dict(type='bool', default=False),
    )

    proxmox = ProxmoxModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    node = params['node']

    # Build the creation parameters
    create_params = {}

    if params['vmid']:
        create_params['vmid'] = params['vmid']
    else:
        # Get next available VMID
        try:
            create_params['vmid'] = api.cluster.nextid.get()
        except Exception as e:
            module.fail_json(msg="Failed to get next available VMID: %s" % str(e))

    vmid = int(create_params['vmid'])

    # Check if VM already exists
    try:
        existing_vms = api.nodes(node).qemu.get()
        for vm in existing_vms:
            if int(vm.get('vmid', 0)) == vmid:
                module.exit_json(changed=False, vmid=vmid, msg="VM %d already exists on node %s." % (vmid, node))
    except Exception as e:
        module.fail_json(msg="Failed to check existing VMs: %s" % str(e))

    # Map module params to API params
    param_map = {
        'name': 'name',
        'memory': 'memory',
        'cores': 'cores',
        'sockets': 'sockets',
        'ostype': 'ostype',
        'scsi0': 'scsi0',
        'ide2': 'ide2',
        'net0': 'net0',
        'boot': 'boot',
    }

    for module_param, api_param in param_map.items():
        if params.get(module_param) is not None:
            create_params[api_param] = params[module_param]

    if params['cpu_type']:
        create_params['cpu'] = params['cpu_type']

    if module.check_mode:
        module.exit_json(changed=True, vmid=vmid, msg="VM %d would be created on node %s." % (vmid, node))

    try:
        api.nodes(node).qemu.create(**create_params)
    except Exception as e:
        module.fail_json(msg="Failed to create VM %d on node %s: %s" % (vmid, node, str(e)))

    # Optionally start the VM after creation
    if params['start_after_create']:
        try:
            api.nodes(node).qemu(vmid).status.start.post()
        except Exception as e:
            module.fail_json(msg="VM %d created but failed to start: %s" % (vmid, str(e)))

    module.exit_json(changed=True, vmid=vmid, msg="VM %d created successfully on node %s." % (vmid, node))


if __name__ == '__main__':
    main()
