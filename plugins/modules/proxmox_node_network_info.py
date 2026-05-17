#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_network_info
short_description: Query network interface information on Proxmox VE nodes
version_added: "1.0.0"
description:
  - Retrieve network interface configuration from a Proxmox VE node via the
    C(/nodes/{node}/network) API endpoint.
  - This is an info module and does not make any changes.
  - Companion to the C(proxmox_node_network) module for read-only queries.
options:
  api_host:
    description: Proxmox VE API host (hostname or IP).
    type: str
    required: true
  api_user:
    description: Proxmox VE API user (e.g. C(root@pam)).
    type: str
    required: true
  api_password:
    description: Password for API user.
    type: str
  api_token_id:
    description: API token ID.
    type: str
  api_token_secret:
    description: API token secret.
    type: str
  validate_certs:
    description: Whether to validate SSL certificates.
    type: bool
    default: true
  node:
    description: Target Proxmox VE node name.
    type: str
    required: true
  type:
    description:
      - Filter interfaces by type.
      - "Examples: C(bridge), C(bond), C(eth), C(vlan), C(OVSBridge)."
    type: str
author:
  - sfulmer
  limit:
    description:
      - Maximum number of results to return.
    type: int
    default: 100
  offset:
    description:
      - Number of results to skip for pagination.
    type: int
    default: 0
  max_results:
    description:
      - Maximum total results to return.
    type: int
    default: 1000
'''

EXAMPLES = r'''
- name: List all network interfaces on a node
  stevefulme1.proxmox.proxmox_node_network_info:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
  register: net_info

- name: List only bridge interfaces
  stevefulme1.proxmox.proxmox_node_network_info:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    type: bridge
  register: bridge_info

- name: Display interface names
  ansible.builtin.debug:
    msg: "{{ net_info.interfaces | map(attribute='iface') | list }}"
'''

RETURN = r'''
interfaces:
  description: List of network interface configuration dictionaries.
  returned: success
  type: list
  elements: dict
  sample:
    - iface: "vmbr0"
      type: "bridge"
      address: "192.168.1.1"
      netmask: "255.255.255.0"
      gateway: "192.168.1.254"
      bridge_ports: "eno1"
      active: 1
      autostart: 1
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    argument_spec = dict(
        limit=dict(type='int', default=100),
        offset=dict(type='int', default=0),
        max_results=dict(type='int', default=1000),
        node=dict(type='str', required=True),
        type=dict(type='str'),
    )

    proxmox = ProxmoxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module = proxmox.module
    params = module.params
    node = params['node']

    api = proxmox.get_api()

    try:
        get_params = {}
        if params.get('type'):
            get_params['type'] = params['type']
        interfaces = api.nodes(node).network.get(**get_params)
    except Exception as e:
        module.fail_json(
            msg="Failed to query network interfaces on node '%s': %s"
            % (node, str(e)))

    module.exit_json(changed=False, interfaces=interfaces)


if __name__ == '__main__':
    main()
