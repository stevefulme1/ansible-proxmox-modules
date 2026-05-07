#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_config
short_description: Modify VM hardware configuration in Proxmox VE
description:
  - Update QEMU/KVM virtual machine hardware configuration in Proxmox VE.
  - Uses the C(/nodes/{node}/qemu/{vmid}/config) API endpoint.
  - Checks current configuration before applying changes for idempotency.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node name where the VM resides.
    type: str
    required: true
  vmid:
    description:
      - The VM ID number.
    type: int
    required: true
  cores:
    description:
      - Number of CPU cores per socket.
    type: int
  sockets:
    description:
      - Number of CPU sockets.
    type: int
  memory:
    description:
      - Amount of RAM in MB.
    type: int
  balloon:
    description:
      - Amount of target RAM for the balloon driver in MB. Set to 0 to disable ballooning.
    type: int
  cpu_type:
    description:
      - Emulated CPU type (e.g. C(host), C(kvm64), C(qemu64)).
    type: str
  name:
    description:
      - VM name.
    type: str
  description:
    description:
      - VM description.
    type: str
  boot:
    description:
      - Boot order string (e.g. C(order=scsi0;ide2;net0)).
    type: str
  hotplug:
    description:
      - Hotplug features string (e.g. C(network,disk,usb)).
    type: str
  ostype:
    description:
      - Guest OS type (e.g. C(l26), C(win10), C(other)).
    type: str
  machine:
    description:
      - Machine type (e.g. C(q35), C(pc), C(pc-i440fx-8.1)).
    type: str
  args:
    description:
      - Arbitrary QEMU arguments passed to the VM.
    type: str
'''

EXAMPLES = r'''
- name: Set VM CPU and memory
  stevefulme1.proxmox.proxmox_vm_config:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    cores: 4
    sockets: 2
    memory: 8192

- name: Update VM name and description
  stevefulme1.proxmox.proxmox_vm_config:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    name: webserver-01
    description: "Production web server"

- name: Set CPU type to host passthrough
  stevefulme1.proxmox.proxmox_vm_config:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    cpu_type: host
'''

RETURN = r'''
vmid:
  description: The VM ID that was configured.
  returned: success
  type: int
  sample: 100
config:
  description: The configuration parameters that were applied.
  returned: success
  type: dict
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        node=dict(type='str', required=True),
        vmid=dict(type='int', required=True),
        cores=dict(type='int'),
        sockets=dict(type='int'),
        memory=dict(type='int'),
        balloon=dict(type='int'),
        cpu_type=dict(type='str'),
        name=dict(type='str'),
        description=dict(type='str'),
        boot=dict(type='str'),
        hotplug=dict(type='str'),
        ostype=dict(type='str'),
        machine=dict(type='str'),
        args=dict(type='str'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    node = params['node']
    vmid = params['vmid']

    # Get current config
    try:
        current_config = api.nodes(node).qemu(vmid).config.get()
    except Exception as e:
        module.fail_json(msg="Failed to get VM %d config: %s" % (vmid, str(e)))

    # Map module params to API params (cpu_type -> cpu in the API)
    param_map = {
        'cores': 'cores',
        'sockets': 'sockets',
        'memory': 'memory',
        'balloon': 'balloon',
        'cpu_type': 'cpu',
        'name': 'name',
        'description': 'description',
        'boot': 'boot',
        'hotplug': 'hotplug',
        'ostype': 'ostype',
        'machine': 'machine',
        'args': 'args',
    }

    update_params = {}
    for module_key, api_key in param_map.items():
        desired_val = params.get(module_key)
        if desired_val is None:
            continue
        current_val = current_config.get(api_key)
        if current_val is None or str(current_val) != str(desired_val):
            update_params[api_key] = desired_val

    changed = bool(update_params)
    result = dict(vmid=vmid, config=update_params)

    if changed and not module.check_mode:
        try:
            api.nodes(node).qemu(vmid).config.put(**update_params)
        except Exception as e:
            module.fail_json(msg="Failed to update VM %d config: %s" % (vmid, str(e)))

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
