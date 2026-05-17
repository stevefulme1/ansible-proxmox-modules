#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_cluster_join_info
short_description: Get Proxmox VE cluster join information
description:
  - Retrieve cluster join information from Proxmox VE.
  - Uses the C(/cluster/config/join) API endpoint.
  - Returns totem configuration and node information needed to join the cluster.
  - This is an info module and does not make any changes.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - Optionally specify a node to get its specific join information.
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
- name: Get cluster join information
  stevefulme1.proxmox.proxmox_cluster_join_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  register: join_info

- name: Get join info for a specific node
  stevefulme1.proxmox.proxmox_cluster_join_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
  register: join_info
'''

RETURN = r'''
join_info:
  description: Cluster join information including totem and node configuration.
  type: dict
  returned: always
  sample:
    totem:
      cluster_name: mycluster
      config_version: 3
      interface: {}
    nodelist:
      - name: pve1
        nodeid: 1
        pve_addr: 192.168.1.10
        quorum_votes: 1
    preferred_node: pve1
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            limit=dict(type='int', default=100),
            offset=dict(type='int', default=0),
            max_results=dict(type='int', default=1000),
            node=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    params = {}
    node = module.params.get('node')
    if node:
        params['node'] = node

    try:
        result = module.proxmox_api.cluster.config.join.get(**params)
    except Exception as e:
        module.fail_json(msg="Failed to get cluster join information: {0}".format(e))

    module.exit_json(changed=False, join_info=result)


if __name__ == '__main__':
    main()
