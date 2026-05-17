#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_info
short_description: Query node status information on Proxmox VE
version_added: "1.0.0"
description:
  - Retrieve status information for a specific Proxmox VE node.
  - Returns CPU usage, memory usage, uptime, kernel version, PVE version, and more.
  - This is an info module and does not make any changes.
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node to query.
    type: str
    required: true
  limit:
    description:
      - Maximum number of results to return.
      - Applied client-side to truncate results.
    type: int
    default: 100
  offset:
    description:
      - Number of results to skip before returning.
      - Applied client-side for pagination.
    type: int
    default: 0
  max_results:
    description:
      - Maximum total number of results to return.
      - Set to 0 for no limit.
    type: int
    default: 1000
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Get node status
  stevefulme1.proxmox.proxmox_node_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
  register: node_status

- name: Display node info
  ansible.builtin.debug:
    var: node_status.node_info

- name: Show uptime
  ansible.builtin.debug:
    msg: "Node uptime: {{ node_status.node_info.uptime }} seconds"
'''

RETURN = r'''
node_info:
  description: Dictionary containing the node status information.
  returned: always
  type: dict
  sample:
    cpu: 0.05
    cpuinfo:
      cores: 8
      model: "Intel(R) Xeon(R) CPU E5-2680 v4"
      sockets: 1
    memory:
      total: 34359738368
      used: 8589934592
      free: 25769803776
    uptime: 1234567
    kversion: "Linux 6.8.12-1-pve #1 SMP"
    pveversion: "pve-manager/8.2.2"
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            limit=dict(type='int', default=100),
            offset=dict(type='int', default=0),
            max_results=dict(type='int', default=1000),
            node=dict(type='str', required=True),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']

    proxmox = module.proxmox_api()

    try:
        status = proxmox.nodes(node).status.get()
    except Exception as e:
        module.fail_json(msg="Failed to get status for node '{0}': {1}".format(node, str(e)))

    module.exit_json(changed=False, node_info=status)


if __name__ == '__main__':
    main()
