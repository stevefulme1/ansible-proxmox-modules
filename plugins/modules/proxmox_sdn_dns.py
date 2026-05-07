#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_sdn_dns
short_description: Manage SDN DNS integrations on Proxmox VE
description:
  - Create, update, or remove SDN DNS integrations on Proxmox VE.
  - Uses the Proxmox VE API at C(/cluster/sdn/dns).
version_added: "1.0.0"
author:
  - sfulmer
options:
  dns:
    description:
      - Name of the SDN DNS integration.
    type: str
    required: true
  type:
    description:
      - Type of the DNS integration.
    type: str
    choices: [ powerdns, plugin ]
  url:
    description:
      - URL of the DNS server API endpoint.
    type: str
  key:
    description:
      - API key for authenticating with the DNS server.
    type: str
    no_log: true
  reversedns:
    description:
      - Reverse DNS zone for IPv4.
    type: str
  reversev6dns:
    description:
      - Reverse DNS zone for IPv6.
    type: str
  ttl:
    description:
      - Default TTL for DNS records.
    type: int
  state:
    description:
      - Whether the DNS integration should be present or absent.
    type: str
    choices: [ present, absent ]
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create a PowerDNS integration
  stevefulme1.proxmox.proxmox_sdn_dns:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    dns: mydns
    type: powerdns
    url: "http://pdns.example.com:8081/api/v1"
    key: "{{ pdns_api_key }}"
    reversedns: "10.in-addr.arpa"
    ttl: 300
    state: present

- name: Remove a DNS integration
  stevefulme1.proxmox.proxmox_sdn_dns:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: ansible
    api_token_secret: "{{ api_token }}"
    dns: mydns
    state: absent
'''

RETURN = r'''
dns_info:
  description: The SDN DNS integration information returned by the API.
  type: dict
  returned: on success when state is present
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)

DNS_PARAMS = ['url', 'key', 'reversedns', 'reversev6dns', 'ttl']


def _build_params(module):
    """Build API parameter dict from module params, omitting None values."""
    params = {}
    for key in DNS_PARAMS:
        val = module.params.get(key)
        if val is not None:
            params[key] = val
    return params


def _needs_update(current, desired):
    """Return True if any desired param differs from current config."""
    for key, value in desired.items():
        if key == 'key':
            # Cannot compare secrets; always assume changed if provided
            return True
        if str(current.get(key, '')) != str(value):
            return True
    return False


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            dns=dict(type='str', required=True),
            type=dict(type='str', choices=['powerdns', 'plugin']),
            url=dict(type='str'),
            key=dict(type='str', no_log=True),
            reversedns=dict(type='str'),
            reversev6dns=dict(type='str'),
            ttl=dict(type='int'),
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

    dns = module.params['dns']
    dns_type = module.params['type']
    state = module.params['state']

    # Fetch existing DNS integrations
    existing = module.proxmox_api_call('GET', '/cluster/sdn/dns')

    current = None
    if existing is not None:
        for entry in existing:
            if entry.get('dns') == dns:
                current = entry
                break

    if state == 'present':
        desired = _build_params(module)

        if current is not None:
            if not _needs_update(current, desired):
                module.exit_json(changed=False, dns_info=current)

            if module.check_mode:
                module.exit_json(changed=True)

            result = module.proxmox_api_call(
                'PUT', '/cluster/sdn/dns/{dns}',
                dns=dns, **desired,
            )
            module.exit_json(changed=True, dns_info=result)

        if module.check_mode:
            module.exit_json(changed=True)

        desired['dns'] = dns
        desired['type'] = dns_type

        result = module.proxmox_api_call(
            'POST', '/cluster/sdn/dns', **desired,
        )
        module.exit_json(changed=True, dns_info=result)

    else:  # absent
        if current is None:
            module.exit_json(changed=False)

        if module.check_mode:
            module.exit_json(changed=True)

        module.proxmox_api_call(
            'DELETE', '/cluster/sdn/dns/{dns}', dns=dns,
        )
        module.exit_json(changed=True)


if __name__ == '__main__':
    main()
