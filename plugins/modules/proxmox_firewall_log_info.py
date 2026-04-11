#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_firewall_log_info
short_description: Query firewall logs on Proxmox VE
description:
  - Retrieve firewall log entries from Proxmox VE.
  - When C(node) is specified, uses the node-level API at
    C(/nodes/{node}/firewall/log).
  - When C(node) is omitted, uses the cluster-level API at
    C(/cluster/firewall/log).
  - This is an info module and does not modify any state.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node from which to query firewall logs.
      - If not specified, cluster-level logs are returned.
    type: str
  start:
    description:
      - Line number to start from (for pagination).
    type: int
  limit:
    description:
      - Maximum number of log entries to return.
    type: int
    default: 50
  since:
    description:
      - Only return log entries since this Unix timestamp.
    type: int
extends_documentation_fragment:
  - sfulmer.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Get cluster-level firewall logs
  sfulmer.proxmox.proxmox_firewall_log_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    limit: 100
  register: cluster_logs

- name: Get node-level firewall logs
  sfulmer.proxmox.proxmox_firewall_log_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    node: pve1
    limit: 25
    since: 1700000000
  register: node_logs

- name: Display firewall logs
  ansible.builtin.debug:
    var: cluster_logs.firewall_logs
'''

RETURN = r'''
firewall_logs:
  description: List of firewall log entries.
  type: list
  elements: dict
  returned: always
  contains:
    n:
      description: Log entry line number.
      type: int
    t:
      description: Log entry text content.
      type: str
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str'),
            start=dict(type='int'),
            limit=dict(type='int', default=50),
            since=dict(type='int'),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    start = module.params['start']
    limit = module.params['limit']
    since = module.params['since']

    params = {}
    if start is not None:
        params['start'] = start
    if limit is not None:
        params['limit'] = limit
    if since is not None:
        params['since'] = since

    if node:
        api_path = '/nodes/{node}/firewall/log'
        result = module.proxmox_api_call(
            'GET', api_path, node=node, **params
        )
    else:
        api_path = '/cluster/firewall/log'
        result = module.proxmox_api_call(
            'GET', api_path, **params
        )

    module.exit_json(changed=False, firewall_logs=result or [])


if __name__ == '__main__':
    main()
