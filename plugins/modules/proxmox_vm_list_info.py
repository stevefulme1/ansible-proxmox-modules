#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_vm_list_info
short_description: List QEMU VMs across Proxmox VE nodes
version_added: "1.1.0"
description:
  - Retrieve a list of QEMU virtual machines across all nodes or a specific node.
  - Returns vmid, name, status, memory, CPUs, node, and tags for each VM.
  - This is an info module and does not make any changes.
author:
  - sfulmer
options:
  node:
    description:
      - Limit results to VMs on this specific node.
      - When omitted, VMs from all nodes are returned.
    type: str
  status_filter:
    description:
      - Filter VMs by their current status.
    type: str
    choices: ['running', 'stopped']
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: List all VMs across the cluster
  stevefulme1.proxmox.proxmox_vm_list_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
  register: all_vms

- name: List running VMs on a specific node
  stevefulme1.proxmox.proxmox_vm_list_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    status_filter: running
  register: running_vms

- name: Display VM list
  ansible.builtin.debug:
    var: all_vms.resources
'''

RETURN = r'''
resources:
  description: List of QEMU virtual machines.
  returned: always
  type: list
  elements: dict
  sample:
    - vmid: 100
      name: "web-server"
      status: "running"
      mem: 4294967296
      cpus: 4
      node: "pve1"
      tags: "production;web"
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str'),
            status_filter=dict(type='str', choices=['running', 'stopped']),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    status_filter = module.params['status_filter']

    proxmox = module.proxmox_api()

    try:
        if node:
            nodes_to_query = [node]
        else:
            nodes_to_query = [
                n['node'] for n in proxmox.nodes.get()
            ]

        vms = []
        for n in nodes_to_query:
            for vm in proxmox.nodes(n).qemu.get():
                vm['node'] = n
                if status_filter and vm.get('status') != status_filter:
                    continue
                vms.append(vm)
    except Exception as e:
        module.fail_json(
            msg="Failed to list VMs: {0}".format(str(e))
        )

    module.exit_json(changed=False, resources=vms)


if __name__ == '__main__':
    main()
