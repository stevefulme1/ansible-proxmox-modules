#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pool_info
short_description: Query resource pool information on Proxmox VE
version_added: "1.0.0"
description:
  - Retrieve information about resource pools on Proxmox VE.
  - Can list all pools or get details for a specific pool.
  - This is an info module and does not make any changes.
author:
  - sfulmer
options:
  poolid:
    description:
      - The pool identifier to query. If omitted, all pools are returned.
    type: str
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
- name: List all resource pools
  stevefulme1.proxmox.proxmox_pool_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
  register: all_pools

- name: Get details of a specific pool
  stevefulme1.proxmox.proxmox_pool_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    poolid: production
  register: pool_detail

- name: Display pool info
  ansible.builtin.debug:
    var: pool_detail.pools
'''

RETURN = r'''
pools:
  description:
    - List of pool information dictionaries.
    - When C(poolid) is specified, returns a single-element list with full pool details including members.
    - When C(poolid) is omitted, returns all pools with summary information.
  returned: always
  type: list
  elements: dict
  sample:
    - poolid: "production"
      comment: "Production workloads"
      members:
        - id: "qemu/100"
          node: "pve1"
          type: "qemu"
          vmid: 100
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            limit=dict(type='int', default=100),
            offset=dict(type='int', default=0),
            max_results=dict(type='int', default=1000),
            poolid=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    poolid = module.params['poolid']

    proxmox = module.proxmox_api()

    if poolid:
        try:
            pool = proxmox.pools(poolid).get()
            module.exit_json(changed=False, pools=[pool])
        except Exception as e:
            module.fail_json(msg="Failed to get pool '{0}': {1}".format(poolid, str(e)))
    else:
        try:
            pools = proxmox.pools.get()
            module.exit_json(changed=False, pools=pools)
        except Exception as e:
            module.fail_json(msg="Failed to list pools: {0}".format(str(e)))


if __name__ == '__main__':
    main()
