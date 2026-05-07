#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_sdn_ipam
short_description: Manage SDN IPAM backends on Proxmox VE
description:
  - Create, update, or remove SDN IPAM (IP Address Management) backends on Proxmox VE.
  - Uses the Proxmox VE API at C(/cluster/sdn/ipams).
version_added: "1.0.0"
author:
  - sfulmer
options:
  ipam:
    description:
      - Name of the IPAM backend.
    type: str
    required: true
  type:
    description:
      - Type of the IPAM backend.
    type: str
    choices: [ pve, netbox, phpipam ]
  url:
    description:
      - URL of the IPAM backend API endpoint.
      - Required for netbox and phpipam types.
    type: str
  token:
    description:
      - API token for authenticating with the IPAM backend.
      - Required for netbox and phpipam types.
    type: str
    no_log: true
  section:
    description:
      - Section ID for phpIPAM.
      - Only applicable when type is C(phpipam).
    type: int
  state:
    description:
      - Whether the IPAM backend should be present or absent.
    type: str
    choices: [ present, absent ]
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create a Proxmox VE native IPAM backend
  stevefulme1.proxmox.proxmox_sdn_ipam:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    ipam: pveipam
    type: pve
    state: present

- name: Create a NetBox IPAM backend
  stevefulme1.proxmox.proxmox_sdn_ipam:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    ipam: netbox
    type: netbox
    url: "https://netbox.example.com/api"
    token: "{{ netbox_token }}"
    state: present

- name: Create a phpIPAM backend
  stevefulme1.proxmox.proxmox_sdn_ipam:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    ipam: phpipam
    type: phpipam
    url: "https://phpipam.example.com/api"
    token: "{{ phpipam_token }}"
    section: 1
    state: present

- name: Remove an IPAM backend
  stevefulme1.proxmox.proxmox_sdn_ipam:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    ipam: netbox
    state: absent
'''

RETURN = r'''
ipam_info:
  description: The IPAM backend information returned by the API.
  type: dict
  returned: on success when state is present
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)

IPAM_PARAMS = ['url', 'token', 'section']


def _build_params(module):
    """Build API parameter dict from module params, omitting None values."""
    params = {}
    for key in IPAM_PARAMS:
        val = module.params.get(key)
        if val is not None:
            params[key] = val
    return params


def _needs_update(current, desired):
    """Return True if any desired param differs from current config."""
    for key, value in desired.items():
        if key == 'token':
            return True
        if str(current.get(key, '')) != str(value):
            return True
    return False


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            ipam=dict(type='str', required=True),
            type=dict(type='str', choices=['pve', 'netbox', 'phpipam']),
            url=dict(type='str'),
            token=dict(type='str', no_log=True),
            section=dict(type='int'),
            state=dict(
                type='str',
                choices=['present', 'absent'],
                default='present',
            ),
        ),
        required_if=[
            ('state', 'present', ['type']),
        ],
        supports_check_mode=True,
    )

    ipam = module.params['ipam']
    ipam_type = module.params['type']
    state = module.params['state']

    # Fetch existing IPAM backends
    existing = module.proxmox_api_call('GET', '/cluster/sdn/ipams')

    current = None
    if existing is not None:
        for entry in existing:
            if entry.get('ipam') == ipam:
                current = entry
                break

    if state == 'present':
        desired = _build_params(module)

        if current is not None:
            if not _needs_update(current, desired):
                module.exit_json(changed=False, ipam_info=current)

            if module.check_mode:
                module.exit_json(changed=True)

            result = module.proxmox_api_call(
                'PUT', '/cluster/sdn/ipams/{ipam}',
                ipam=ipam, **desired,
            )
            module.exit_json(changed=True, ipam_info=result)

        if module.check_mode:
            module.exit_json(changed=True)

        desired['ipam'] = ipam
        desired['type'] = ipam_type

        result = module.proxmox_api_call(
            'POST', '/cluster/sdn/ipams', **desired,
        )
        module.exit_json(changed=True, ipam_info=result)

    else:  # absent
        if current is None:
            module.exit_json(changed=False)

        if module.check_mode:
            module.exit_json(changed=True)

        module.proxmox_api_call(
            'DELETE', '/cluster/sdn/ipams/{ipam}', ipam=ipam,
        )
        module.exit_json(changed=True)


if __name__ == '__main__':
    main()
