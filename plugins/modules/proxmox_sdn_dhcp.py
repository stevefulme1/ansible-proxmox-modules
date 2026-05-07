#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_sdn_dhcp
short_description: Manage SDN DHCP settings on Proxmox VE
description:
  - Configure DHCP ranges and DNS server settings on SDN subnet configurations.
  - Updates subnet config with DHCP range via the Proxmox VE API at
    C(/cluster/sdn/vnets/{vnet}/subnets/{subnet}).
version_added: "1.0.0"
author:
  - sfulmer
options:
  vnet:
    description:
      - Name of the SDN VNet containing the subnet.
    type: str
    required: true
  subnet:
    description:
      - The subnet identifier (e.g. C(10.0.0.0-24) or C(10.0.0.0/24)).
    type: str
    required: true
  dhcp_range:
    description:
      - List of DHCP address ranges.
      - Each range is a dictionary with C(start_address) and C(end_address).
    type: list
    elements: dict
    suboptions:
      start_address:
        description:
          - Start IP address of the DHCP range.
        type: str
        required: true
      end_address:
        description:
          - End IP address of the DHCP range.
        type: str
        required: true
  dhcp_dns_server:
    description:
      - DNS server IP address to distribute via DHCP.
    type: str
  state:
    description:
      - Whether the DHCP configuration should be present or absent.
      - When C(absent), DHCP range and DNS server settings are removed from
        the subnet.
    type: str
    choices: [ present, absent ]
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Configure DHCP range on a subnet
  stevefulme1.proxmox.proxmox_sdn_dhcp:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    vnet: myvnet
    subnet: "10.0.0.0-24"
    dhcp_range:
      - start_address: "10.0.0.100"
        end_address: "10.0.0.200"
    dhcp_dns_server: "10.0.0.1"
    state: present

- name: Configure multiple DHCP ranges
  stevefulme1.proxmox.proxmox_sdn_dhcp:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    vnet: myvnet
    subnet: "10.0.0.0-24"
    dhcp_range:
      - start_address: "10.0.0.100"
        end_address: "10.0.0.150"
      - start_address: "10.0.0.200"
        end_address: "10.0.0.250"
    state: present

- name: Remove DHCP settings from a subnet
  stevefulme1.proxmox.proxmox_sdn_dhcp:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    vnet: myvnet
    subnet: "10.0.0.0-24"
    state: absent
'''

RETURN = r'''
subnet_info:
  description: The subnet configuration after DHCP settings are applied.
  type: dict
  returned: on success
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


def _format_dhcp_ranges(dhcp_range):
    """Format DHCP ranges into the Proxmox API format."""
    if not dhcp_range:
        return None
    ranges = []
    for r in dhcp_range:
        ranges.append(
            'start-address={0},end-address={1}'.format(
                r['start_address'], r['end_address']
            )
        )
    return '\n'.join(ranges)


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            vnet=dict(type='str', required=True),
            subnet=dict(type='str', required=True),
            dhcp_range=dict(
                type='list',
                elements='dict',
                options=dict(
                    start_address=dict(type='str', required=True),
                    end_address=dict(type='str', required=True),
                ),
            ),
            dhcp_dns_server=dict(type='str'),
            state=dict(
                type='str',
                choices=['present', 'absent'],
                default='present',
            ),
        ),
        supports_check_mode=True,
    )

    vnet = module.params['vnet']
    subnet = module.params['subnet']
    dhcp_range = module.params['dhcp_range']
    dhcp_dns_server = module.params['dhcp_dns_server']
    state = module.params['state']

    api_path = '/cluster/sdn/vnets/{vnet}/subnets/{subnet}'

    # Fetch existing subnet config
    current = module.proxmox_api_call(
        'GET', api_path, vnet=vnet, subnet=subnet,
    )

    if state == 'present':
        params = {}
        changed = False

        formatted_range = _format_dhcp_ranges(dhcp_range)
        if formatted_range is not None:
            current_range = current.get('dhcp-range', '') if current else ''
            if current_range != formatted_range:
                params['dhcp-range'] = formatted_range
                changed = True

        if dhcp_dns_server is not None:
            current_dns = current.get('dhcp-dns-server', '') if current else ''
            if current_dns != dhcp_dns_server:
                params['dhcp-dns-server'] = dhcp_dns_server
                changed = True

        if not changed:
            module.exit_json(changed=False, subnet_info=current)

        if module.check_mode:
            module.exit_json(changed=True)

        result = module.proxmox_api_call(
            'PUT', api_path, vnet=vnet, subnet=subnet, **params,
        )
        module.exit_json(changed=True, subnet_info=result)

    else:  # absent
        current_range = current.get('dhcp-range', '') if current else ''
        current_dns = current.get('dhcp-dns-server', '') if current else ''

        if not current_range and not current_dns:
            module.exit_json(changed=False, subnet_info=current)

        if module.check_mode:
            module.exit_json(changed=True)

        params = {}
        if current_range:
            params['delete'] = 'dhcp-range'
        if current_dns:
            existing_delete = params.get('delete', '')
            if existing_delete:
                params['delete'] = existing_delete + ',dhcp-dns-server'
            else:
                params['delete'] = 'dhcp-dns-server'

        result = module.proxmox_api_call(
            'PUT', api_path, vnet=vnet, subnet=subnet, **params,
        )
        module.exit_json(changed=True, subnet_info=result)


if __name__ == '__main__':
    main()
