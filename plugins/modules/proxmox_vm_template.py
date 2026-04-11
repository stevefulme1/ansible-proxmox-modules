#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_template
short_description: Convert a VM to a template in Proxmox VE
description:
  - Convert a QEMU/KVM virtual machine to a template in Proxmox VE.
  - This is a one-way operation and cannot be reversed.
  - Uses the C(/nodes/{node}/qemu/{vmid}/template) API endpoint.
  - If the VM is already a template, no action is taken.
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
  disk:
    description:
      - The disk to use as the base image for the template (e.g. C(scsi0), C(virtio0)).
      - If not specified, Proxmox uses the default disk.
    type: str
'''

EXAMPLES = r'''
- name: Convert VM to template
  sfulmer.proxmox.proxmox_vm_template:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 9000

- name: Convert VM to template using specific disk
  sfulmer.proxmox.proxmox_vm_template:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 9000
    disk: scsi0
'''

RETURN = r'''
vmid:
  description: The VM ID that was converted to a template.
  returned: success
  type: int
  sample: 9000
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        node=dict(type='str', required=True),
        vmid=dict(type='int', required=True),
        disk=dict(type='str'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    node = params['node']
    vmid = params['vmid']
    result = dict(vmid=vmid)

    # Check if VM is already a template
    try:
        config = api.nodes(node).qemu(vmid).config.get()
    except Exception as e:
        module.fail_json(msg="Failed to get VM %d config: %s" % (vmid, str(e)))

    if config.get('template'):
        module.exit_json(changed=False, msg="VM %d is already a template." % vmid, **result)

    if module.check_mode:
        module.exit_json(changed=True, **result)

    template_params = {}
    if params.get('disk'):
        template_params['disk'] = params['disk']

    try:
        api.nodes(node).qemu(vmid).template.post(**template_params)
    except Exception as e:
        module.fail_json(msg="Failed to convert VM %d to template: %s" % (vmid, str(e)))

    module.exit_json(changed=True, **result)


if __name__ == '__main__':
    main()
