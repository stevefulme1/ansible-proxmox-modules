#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_ceph_pool_info
short_description: List Ceph pools on a Proxmox VE node
version_added: "1.1.0"
description:
  - Retrieve the list of Ceph pools from a Proxmox VE node.
  - Returns name, size, min_size, pg_num, bytes_used, and percent_used for each pool.
  - This is an info module and does not make any changes.
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node to query Ceph pools from.
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
- name: List Ceph pools
  stevefulme1.proxmox.proxmox_ceph_pool_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
  register: ceph_pools

- name: Display Ceph pools
  ansible.builtin.debug:
    var: ceph_pools.resources
'''

RETURN = r'''
resources:
  description: List of Ceph pools.
  returned: always
  type: list
  elements: dict
  sample:
    - pool_name: "rbd"
      size: 3
      min_size: 2
      pg_num: 128
      bytes_used: 1073741824
      percent_used: 12.5
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
        pools = proxmox.nodes(node).ceph.pool.get()
    except Exception as e:
        module.fail_json(
            msg="Failed to list Ceph pools on node '{0}': {1}".format(
                node, str(e)
            )
        )

    module.exit_json(changed=False, resources=pools)


if __name__ == '__main__':
    main()
