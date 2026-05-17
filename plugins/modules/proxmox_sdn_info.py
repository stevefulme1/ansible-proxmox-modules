#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_sdn_info
short_description: Query SDN running and pending state on Proxmox VE
description:
  - Retrieve SDN running configuration and pending changes from Proxmox VE.
  - Optionally filter by resource type (zones, vnets, subnets, controllers).
  - Uses the Proxmox VE API at C(/cluster/sdn).
  - This is an info module and does not modify any state.
version_added: "1.0.0"
author:
  - sfulmer
options:
  type:
    description:
      - Filter the SDN information by resource type.
      - If not specified, all SDN information is returned.
    type: str
    choices: [ zones, vnets, subnets, controllers ]
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
- name: Get all SDN information
  stevefulme1.proxmox.proxmox_sdn_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
  register: sdn_info

- name: Get only SDN zones
  stevefulme1.proxmox.proxmox_sdn_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    type: zones
  register: sdn_zones

- name: Get SDN controllers with pending changes
  stevefulme1.proxmox.proxmox_sdn_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    type: controllers
  register: sdn_controllers

- name: Display SDN information
  ansible.builtin.debug:
    var: sdn_info.sdn
'''

RETURN = r'''
sdn:
  description: >-
    The SDN configuration data. When type is specified, contains the
    filtered resource list. Otherwise contains the full SDN index.
  type: list
  elements: dict
  returned: always
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)

TYPE_PATHS = {
    'zones': '/cluster/sdn/zones',
    'vnets': '/cluster/sdn/vnets',
    'subnets': '/cluster/sdn/vnets',
    'controllers': '/cluster/sdn/controllers',
}


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            limit=dict(type='int', default=100),
            offset=dict(type='int', default=0),
            max_results=dict(type='int', default=1000),
            type=dict(
                type='str',
                choices=['zones', 'vnets', 'subnets', 'controllers'],
            ),
        ),
        supports_check_mode=True,
    )

    sdn_type = module.params['type']

    if sdn_type:
        api_path = TYPE_PATHS[sdn_type]
        result = module.proxmox_api_call('GET', api_path)
    else:
        result = module.proxmox_api_call('GET', '/cluster/sdn')

    module.exit_json(changed=False, sdn=result or [])


if __name__ == '__main__':
    main()
