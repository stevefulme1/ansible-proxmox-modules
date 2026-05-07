#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_sdn_vnet
short_description: Manage Proxmox VE SDN VNets
description:
  - Create, update, or delete SDN VNets in a Proxmox VE cluster.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  vnet:
    description: The name of the VNet.
    type: str
    required: true
  zone:
    description: The SDN zone this VNet belongs to. Required when state is present.
    type: str
  tag:
    description: VLAN/VXLAN tag number.
    type: int
  alias:
    description: Alias/description for the VNet.
    type: str
  vlanaware:
    description: Whether the VNet bridge is VLAN-aware.
    type: bool
  state:
    description: Whether the VNet should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create a VNet
  stevefulme1.proxmox.proxmox_sdn_vnet:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    vnet: myvnet
    zone: myzone
    tag: 100
    state: present

- name: Remove a VNet
  stevefulme1.proxmox.proxmox_sdn_vnet:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    vnet: myvnet
    state: absent
'''

RETURN = r'''
vnet:
  description: The VNet name that was managed.
  returned: always
  type: str
  sample: myvnet
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        vnet=dict(type='str', required=True),
        zone=dict(type='str'),
        tag=dict(type='int'),
        alias=dict(type='str'),
        vlanaware=dict(type='bool'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(
        argument_spec=module_args,
        required_if=[
            ('state', 'present', ['zone']),
        ],
    )
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    vnet_name = params['vnet']
    state = params['state']

    # Get current vnets
    try:
        vnets = api.cluster.sdn.vnets.get()
    except Exception as e:
        module.fail_json(msg="Failed to get SDN VNets: %s" % str(e))

    existing = None
    for v in vnets:
        if v.get('vnet') == vnet_name:
            existing = v
            break

    changed = False
    result = dict(vnet=vnet_name, changed=False)

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.cluster.sdn.vnets(vnet_name).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete VNet '%s': %s" % (vnet_name, str(e)))
            changed = True
    else:
        config = dict(zone=params['zone'])
        if params.get('tag') is not None:
            config['tag'] = params['tag']
        if params.get('alias') is not None:
            config['alias'] = params['alias']
        if params.get('vlanaware') is not None:
            config['vlanaware'] = int(params['vlanaware'])

        if existing:
            needs_update = False
            for key, value in config.items():
                if existing.get(key) != value:
                    needs_update = True
                    break

            if needs_update:
                if not module.check_mode:
                    try:
                        api.cluster.sdn.vnets(vnet_name).put(**config)
                    except Exception as e:
                        module.fail_json(msg="Failed to update VNet '%s': %s" % (vnet_name, str(e)))
                changed = True
        else:
            config['vnet'] = vnet_name
            if not module.check_mode:
                try:
                    api.cluster.sdn.vnets.post(**config)
                except Exception as e:
                    module.fail_json(msg="Failed to create VNet '%s': %s" % (vnet_name, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
