#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_info
short_description: Query VM status and configuration in Proxmox VE
description:
  - Retrieve status and configuration of a QEMU/KVM virtual machine in Proxmox VE.
  - This is an info module that does not modify state.
  - Uses C(/nodes/{node}/qemu/{vmid}/status/current) and C(/nodes/{node}/qemu/{vmid}/config) API endpoints.
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
'''

EXAMPLES = r'''
- name: Get VM information
  stevefulme1.proxmox.proxmox_vm_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
  register: vm_info

- name: Display VM status
  ansible.builtin.debug:
    msg: "VM {{ vm_info.name }} is {{ vm_info.status }}"

- name: Display VM memory
  ansible.builtin.debug:
    msg: "Memory: {{ vm_info.config.memory }} MB"
'''

RETURN = r'''
vmid:
  description: The VM ID.
  returned: always
  type: int
  sample: 100
name:
  description: The VM name.
  returned: always
  type: str
  sample: "webserver-01"
status:
  description: The current VM status (e.g. running, stopped).
  returned: always
  type: str
  sample: "running"
qmpstatus:
  description: The QEMU Machine Protocol status.
  returned: when available
  type: str
  sample: "running"
uptime:
  description: VM uptime in seconds.
  returned: when running
  type: int
  sample: 86400
cpus:
  description: Number of CPUs allocated.
  returned: always
  type: int
  sample: 4
maxmem:
  description: Maximum memory in bytes.
  returned: always
  type: int
  sample: 8589934592
maxdisk:
  description: Maximum disk size in bytes.
  returned: always
  type: int
  sample: 34359738368
pid:
  description: Process ID of the running VM.
  returned: when running
  type: int
  sample: 12345
template:
  description: Whether the VM is a template.
  returned: always
  type: bool
  sample: false
config:
  description: Full VM configuration dictionary.
  returned: always
  type: dict
vm_status:
  description: Full status data from the API.
  returned: always
  type: dict
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        node=dict(type='str', required=True),
        vmid=dict(type='int', required=True),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    node = params['node']
    vmid = params['vmid']

    # Get VM status
    try:
        vm_status = api.nodes(node).qemu(vmid).status.current.get()
    except Exception as e:
        module.fail_json(msg="Failed to get status for VM %d on node '%s': %s" % (vmid, node, str(e)))

    # Get VM config
    try:
        config = api.nodes(node).qemu(vmid).config.get()
    except Exception as e:
        module.fail_json(msg="Failed to get config for VM %d on node '%s': %s" % (vmid, node, str(e)))

    result = dict(
        changed=False,
        vmid=vmid,
        name=vm_status.get('name', ''),
        status=vm_status.get('status', ''),
        qmpstatus=vm_status.get('qmpstatus', ''),
        uptime=vm_status.get('uptime', 0),
        cpus=vm_status.get('cpus', 0),
        maxmem=vm_status.get('maxmem', 0),
        maxdisk=vm_status.get('maxdisk', 0),
        pid=vm_status.get('pid', 0),
        template=bool(config.get('template', 0)),
        config=config,
        vm_status=vm_status,
    )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
