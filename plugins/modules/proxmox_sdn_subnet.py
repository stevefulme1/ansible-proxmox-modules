#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_sdn_subnet
short_description: Manage Proxmox VE SDN subnets
description:
  - Create, update, or delete SDN subnets on a VNet in a Proxmox VE cluster.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  subnet:
    description: The subnet in CIDR notation (e.g. 10.0.0.0/24).
    type: str
    required: true
  vnet:
    description: The VNet this subnet belongs to.
    type: str
    required: true
  gateway:
    description: Gateway IP address for the subnet.
    type: str
  snat:
    description: Whether to enable source NAT.
    type: bool
  dhcp_range:
    description: List of DHCP ranges.
    type: list
    elements: dict
    suboptions:
      start_address:
        description: Start IP of the DHCP range.
        type: str
        required: true
      end_address:
        description: End IP of the DHCP range.
        type: str
        required: true
  dnszoneprefix:
    description: DNS zone prefix.
    type: str
  state:
    description: Whether the subnet should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create a subnet on a VNet
  sfulmer.proxmox.proxmox_sdn_subnet:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    subnet: 10.0.0.0/24
    vnet: myvnet
    gateway: 10.0.0.1
    state: present

- name: Create a subnet with DHCP range
  sfulmer.proxmox.proxmox_sdn_subnet:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    subnet: 10.0.1.0/24
    vnet: myvnet
    gateway: 10.0.1.1
    dhcp_range:
      - start_address: 10.0.1.100
        end_address: 10.0.1.200
    state: present

- name: Remove a subnet
  sfulmer.proxmox.proxmox_sdn_subnet:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    subnet: 10.0.0.0/24
    vnet: myvnet
    state: absent
'''

RETURN = r'''
subnet:
  description: The subnet CIDR that was managed.
  returned: always
  type: str
  sample: "10.0.0.0/24"
vnet:
  description: The VNet the subnet belongs to.
  returned: always
  type: str
  sample: myvnet
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def _format_dhcp_ranges(ranges):
    """Convert list of dicts to Proxmox dhcp-range format."""
    if not ranges:
        return None
    parts = []
    for r in ranges:
        parts.append("%s-%s" % (r['start_address'], r['end_address']))
    return ','.join(parts)


def main():
    dhcp_range_spec = dict(
        start_address=dict(type='str', required=True),
        end_address=dict(type='str', required=True),
    )

    module_args = dict(
        subnet=dict(type='str', required=True),
        vnet=dict(type='str', required=True),
        gateway=dict(type='str'),
        snat=dict(type='bool'),
        dhcp_range=dict(type='list', elements='dict', options=dhcp_range_spec),
        dnszoneprefix=dict(type='str'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    subnet_cidr = params['subnet']
    vnet_name = params['vnet']
    state = params['state']

    # Proxmox uses the subnet CIDR as the identifier, replacing '/' with '-'
    subnet_id = subnet_cidr.replace('/', '-')

    # Get current subnets for this vnet
    try:
        subnets = api.cluster.sdn.vnets(vnet_name).subnets.get()
    except Exception as e:
        module.fail_json(msg="Failed to get subnets for VNet '%s': %s" % (vnet_name, str(e)))

    existing = None
    for s in subnets:
        if s.get('subnet') == subnet_cidr or s.get('cidr') == subnet_cidr:
            existing = s
            break

    changed = False
    result = dict(subnet=subnet_cidr, vnet=vnet_name, changed=False)

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.cluster.sdn.vnets(vnet_name).subnets(subnet_id).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete subnet '%s': %s" % (subnet_cidr, str(e)))
            changed = True
    else:
        config = dict()
        if params.get('gateway') is not None:
            config['gateway'] = params['gateway']
        if params.get('snat') is not None:
            config['snat'] = int(params['snat'])
        if params.get('dnszoneprefix') is not None:
            config['dnszoneprefix'] = params['dnszoneprefix']

        dhcp_str = _format_dhcp_ranges(params.get('dhcp_range'))
        if dhcp_str is not None:
            config['dhcp-range'] = dhcp_str

        if existing:
            needs_update = False
            for key, value in config.items():
                if existing.get(key) != value:
                    needs_update = True
                    break

            if needs_update:
                if not module.check_mode:
                    try:
                        api.cluster.sdn.vnets(vnet_name).subnets(subnet_id).put(**config)
                    except Exception as e:
                        module.fail_json(msg="Failed to update subnet '%s': %s" % (subnet_cidr, str(e)))
                changed = True
        else:
            config['subnet'] = subnet_cidr
            config['type'] = 'subnet'
            if not module.check_mode:
                try:
                    api.cluster.sdn.vnets(vnet_name).subnets.post(**config)
                except Exception as e:
                    module.fail_json(msg="Failed to create subnet '%s': %s" % (subnet_cidr, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
