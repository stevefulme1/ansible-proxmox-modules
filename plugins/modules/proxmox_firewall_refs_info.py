#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_firewall_refs_info
short_description: Query available firewall references on Proxmox VE
description:
  - Retrieve a list of available firewall references (aliases and IP sets)
    from Proxmox VE.
  - Uses the Proxmox VE API at C(/cluster/firewall/refs).
  - This is an info module and does not modify any state.
version_added: "1.0.0"
author:
  - sfulmer
options:
  type:
    description:
      - Filter results by reference type.
      - If not specified, all reference types are returned.
    type: str
    choices: [ alias, ipset ]
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
- name: Get all firewall references
  stevefulme1.proxmox.proxmox_firewall_refs_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
  register: fw_refs

- name: Get only alias references
  stevefulme1.proxmox.proxmox_firewall_refs_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    type: alias
  register: fw_aliases

- name: Display firewall references
  ansible.builtin.debug:
    var: fw_refs.firewall_refs
'''

RETURN = r'''
firewall_refs:
  description: List of available firewall references.
  type: list
  elements: dict
  returned: always
  contains:
    name:
      description: Name of the firewall reference.
      type: str
    type:
      description: Type of the reference (alias or ipset).
      type: str
    comment:
      description: Optional comment associated with the reference.
      type: str
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
            type=dict(type='str', choices=['alias', 'ipset']),
        ),
        supports_check_mode=True,
    )

    ref_type = module.params['type']

    params = {}
    if ref_type is not None:
        params['type'] = ref_type

    result = module.proxmox_api_call(
        'GET', '/cluster/firewall/refs', **params
    )

    module.exit_json(changed=False, firewall_refs=result or [])


if __name__ == '__main__':
    main()
