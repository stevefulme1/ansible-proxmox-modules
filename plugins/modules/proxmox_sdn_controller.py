#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_sdn_controller
short_description: Manage SDN controllers on Proxmox VE
description:
  - Create, update, or remove SDN controllers (EVPN, BGP) on Proxmox VE.
  - Uses the Proxmox VE API at C(/cluster/sdn/controllers).
version_added: "1.0.0"
author:
  - sfulmer
options:
  controller:
    description:
      - Name of the SDN controller.
    type: str
    required: true
  type:
    description:
      - Type of the SDN controller.
    type: str
    choices: [ evpn, bgp ]
  asn:
    description:
      - Autonomous System Number for the controller.
    type: int
  peers:
    description:
      - Comma-separated list of peer IP addresses.
    type: str
  gateway_nodes:
    description:
      - Comma-separated list of gateway node names.
    type: str
  gateway_external_peers:
    description:
      - Comma-separated list of external gateway peer addresses.
    type: str
  loopback:
    description:
      - Loopback IP address for the controller.
    type: str
  ebgp:
    description:
      - Whether to enable eBGP.
    type: bool
  ebgp_multihop:
    description:
      - eBGP multihop TTL value.
    type: int
  node:
    description:
      - Node name to associate with this controller.
    type: str
  state:
    description:
      - Whether the SDN controller should be present or absent.
    type: str
    choices: [ present, absent ]
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create an EVPN SDN controller
  stevefulme1.proxmox.proxmox_sdn_controller:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    controller: myevpn
    type: evpn
    asn: 65000
    peers: "10.0.0.1,10.0.0.2"
    state: present

- name: Create a BGP SDN controller
  stevefulme1.proxmox.proxmox_sdn_controller:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    controller: mybgp
    type: bgp
    asn: 65001
    ebgp: true
    ebgp_multihop: 10
    node: pve1
    state: present

- name: Remove an SDN controller
  stevefulme1.proxmox.proxmox_sdn_controller:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    controller: myevpn
    state: absent
'''

RETURN = r'''
controller_info:
  description: The SDN controller information returned by the API.
  type: dict
  returned: on success when state is present
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)

CONTROLLER_PARAMS = [
    'asn', 'peers', 'ebgp', 'ebgp_multihop', 'node',
    'loopback',
]

CONTROLLER_PARAMS_HYPHEN = {
    'gateway_nodes': 'gateway-nodes',
    'gateway_external_peers': 'gateway-external-peers',
}


def _build_params(module):
    """Build API parameter dict from module params, omitting None values."""
    params = {}
    for key in CONTROLLER_PARAMS:
        val = module.params.get(key)
        if val is not None:
            if key == 'ebgp':
                params[key] = int(val)
            else:
                params[key] = val
    for mod_key, api_key in CONTROLLER_PARAMS_HYPHEN.items():
        val = module.params.get(mod_key)
        if val is not None:
            params[api_key] = val
    return params


def _needs_update(current, desired):
    """Return True if any desired param differs from the current config."""
    for key, value in desired.items():
        if str(current.get(key, '')) != str(value):
            return True
    return False


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            controller=dict(type='str', required=True),
            type=dict(type='str', choices=['evpn', 'bgp']),
            asn=dict(type='int'),
            peers=dict(type='str'),
            gateway_nodes=dict(type='str'),
            gateway_external_peers=dict(type='str'),
            loopback=dict(type='str'),
            ebgp=dict(type='bool'),
            ebgp_multihop=dict(type='int'),
            node=dict(type='str'),
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

    controller = module.params['controller']
    ctrl_type = module.params['type']
    state = module.params['state']

    # Fetch existing controllers
    existing = module.proxmox_api_call(
        'GET', '/cluster/sdn/controllers'
    )

    current = None
    if existing is not None:
        for ctrl in existing:
            if ctrl.get('controller') == controller:
                current = ctrl
                break

    if state == 'present':
        desired = _build_params(module)

        if current is not None:
            if not _needs_update(current, desired):
                module.exit_json(
                    changed=False, controller_info=current
                )

            if module.check_mode:
                module.exit_json(changed=True)

            result = module.proxmox_api_call(
                'PUT',
                '/cluster/sdn/controllers/{controller}',
                controller=controller,
                **desired,
            )
            module.exit_json(changed=True, controller_info=result)

        if module.check_mode:
            module.exit_json(changed=True)

        desired['controller'] = controller
        desired['type'] = ctrl_type

        result = module.proxmox_api_call(
            'POST', '/cluster/sdn/controllers',
            **desired,
        )
        module.exit_json(changed=True, controller_info=result)

    else:  # absent
        if current is None:
            module.exit_json(changed=False)

        if module.check_mode:
            module.exit_json(changed=True)

        module.proxmox_api_call(
            'DELETE',
            '/cluster/sdn/controllers/{controller}',
            controller=controller,
        )
        module.exit_json(changed=True)


if __name__ == '__main__':
    main()
