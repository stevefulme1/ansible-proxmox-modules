#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_sdn_zone
short_description: Manage Proxmox VE SDN zones
description:
  - Create, update, or delete SDN zones in a Proxmox VE cluster.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  zone:
    description: The name of the SDN zone.
    type: str
    required: true
  type:
    description: The type of SDN zone.
    type: str
    choices: ['simple', 'vlan', 'vxlan', 'evpn', 'qinq']
    default: simple
  bridge:
    description: Bridge interface to use.
    type: str
  mtu:
    description: Maximum transmission unit size.
    type: int
  dns:
    description: DNS server for the zone.
    type: str
  reversedns:
    description: Reverse DNS zone.
    type: str
  ipam:
    description: IPAM plugin to use.
    type: str
  tag:
    description: VLAN tag number.
    type: int
  vlan_protocol:
    description: VLAN protocol.
    type: str
    choices: ['802.1q', '802.1ad']
  state:
    description: Whether the zone should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create a simple SDN zone
  stevefulme1.proxmox.proxmox_sdn_zone:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    zone: myzone
    type: simple
    state: present

- name: Create a VLAN zone with tag
  stevefulme1.proxmox.proxmox_sdn_zone:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    zone: vlanzone
    type: vlan
    bridge: vmbr0
    tag: 100
    state: present

- name: Remove an SDN zone
  stevefulme1.proxmox.proxmox_sdn_zone:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    zone: myzone
    state: absent
'''

RETURN = r'''
zone:
  description: The zone name that was managed.
  returned: always
  type: str
  sample: myzone
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        zone=dict(type='str', required=True),
        type=dict(type='str', choices=['simple', 'vlan', 'vxlan', 'evpn', 'qinq'], default='simple'),
        bridge=dict(type='str'),
        mtu=dict(type='int'),
        dns=dict(type='str'),
        reversedns=dict(type='str'),
        ipam=dict(type='str'),
        tag=dict(type='int'),
        vlan_protocol=dict(type='str', choices=['802.1q', '802.1ad']),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    zone_name = params['zone']
    state = params['state']

    # Get current zones
    try:
        zones = api.cluster.sdn.zones.get()
    except Exception as e:
        module.fail_json(msg="Failed to get SDN zones: %s" % str(e))

    existing = None
    for z in zones:
        if z.get('zone') == zone_name:
            existing = z
            break

    changed = False
    result = dict(zone=zone_name, changed=False)

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.cluster.sdn.zones(zone_name).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete zone '%s': %s" % (zone_name, str(e)))
            changed = True
    else:
        # Build desired config
        config = dict(type=params['type'])
        optional_params = ['bridge', 'mtu', 'dns', 'reversedns', 'ipam', 'tag', 'vlan_protocol']
        for p in optional_params:
            if params.get(p) is not None:
                key = p.replace('_', '-') if p == 'vlan_protocol' else p
                config[key] = params[p]

        if existing:
            # Check if update is needed
            needs_update = False
            for key, value in config.items():
                if key == 'type':
                    continue  # type cannot be changed
                if existing.get(key) != value:
                    needs_update = True
                    break

            if needs_update:
                if not module.check_mode:
                    update_data = {k: v for k, v in config.items() if k != 'type'}
                    try:
                        api.cluster.sdn.zones(zone_name).put(**update_data)
                    except Exception as e:
                        module.fail_json(msg="Failed to update zone '%s': %s" % (zone_name, str(e)))
                changed = True
        else:
            config['zone'] = zone_name
            if not module.check_mode:
                try:
                    api.cluster.sdn.zones.post(**config)
                except Exception as e:
                    module.fail_json(msg="Failed to create zone '%s': %s" % (zone_name, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
