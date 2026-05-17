#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_lxc_list_info
short_description: List LXC containers across Proxmox VE nodes
version_added: "1.1.0"
description:
  - Retrieve a list of LXC containers across all nodes or a specific node.
  - Returns vmid, hostname, status, memory, CPUs, node, and tags for each container.
  - This is an info module and does not make any changes.
author:
  - sfulmer
options:
  node:
    description:
      - Limit results to containers on this specific node.
      - When omitted, containers from all nodes are returned.
    type: str
  status_filter:
    description:
      - Filter containers by their current status.
    type: str
    choices: ['running', 'stopped']
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
- name: List all containers across the cluster
  stevefulme1.proxmox.proxmox_lxc_list_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
  register: all_cts

- name: List running containers on a specific node
  stevefulme1.proxmox.proxmox_lxc_list_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    status_filter: running
  register: running_cts

- name: Display container list
  ansible.builtin.debug:
    var: all_cts.resources
'''

RETURN = r'''
resources:
  description: List of LXC containers.
  returned: always
  type: list
  elements: dict
  sample:
    - vmid: 200
      name: "dns-server"
      status: "running"
      mem: 536870912
      cpus: 2
      node: "pve1"
      tags: "infra"
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            limit=dict(type='int', default=100),
            offset=dict(type='int', default=0),
            max_results=dict(type='int', default=1000),
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

        containers = []
        for n in nodes_to_query:
            for ct in proxmox.nodes(n).lxc.get():
                ct['node'] = n
                if status_filter and ct.get('status') != status_filter:
                    continue
                containers.append(ct)
    except Exception as e:
        module.fail_json(
            msg="Failed to list containers: {0}".format(str(e))
        )

    module.exit_json(changed=False, resources=containers)


if __name__ == '__main__':
    main()
