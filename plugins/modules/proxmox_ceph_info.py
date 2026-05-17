#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_ceph_info
short_description: Query Ceph cluster status on Proxmox VE
description:
  - Retrieve Ceph cluster status information from a Proxmox VE node.
  - Uses the Proxmox VE API at C(/nodes/{node}/ceph/status).
  - This is an info module and does not modify any state.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node from which to query Ceph cluster status.
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
- name: Get Ceph cluster status
  stevefulme1.proxmox.proxmox_ceph_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    node: pve1
  register: ceph_status

- name: Display Ceph health
  ansible.builtin.debug:
    var: ceph_status.ceph_info.health
'''

RETURN = r'''
ceph_info:
  description: The full Ceph cluster status information.
  type: dict
  returned: always
  contains:
    health:
      description: Ceph cluster health status.
      type: dict
    monmap:
      description: Monitor map information.
      type: dict
    osdmap:
      description: OSD map information.
      type: dict
    pgmap:
      description: Placement group statistics.
      type: dict
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


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

    result = module.proxmox_api_call(
        'GET', '/nodes/{node}/ceph/status', node=node
    )

    module.exit_json(changed=False, ceph_info=result)


if __name__ == '__main__':
    main()
