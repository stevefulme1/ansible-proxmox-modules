#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_dns
short_description: Manage Proxmox VE node DNS settings
description:
  - Manage DNS configuration on a Proxmox VE node.
  - Uses the C(/nodes/{node}/dns) API endpoint to read and update DNS settings.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The name of the Proxmox VE node to manage.
    type: str
    required: true
  search:
    description:
      - The DNS search domain.
    type: str
  dns1:
    description:
      - First nameserver IP address.
    type: str
  dns2:
    description:
      - Second nameserver IP address.
    type: str
  dns3:
    description:
      - Third nameserver IP address.
    type: str
  state:
    description:
      - The desired state of the DNS configuration.
    type: str
    choices: ['present']
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Set DNS search domain and nameservers
  stevefulme1.proxmox.proxmox_node_dns:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    search: example.com
    dns1: 8.8.8.8
    dns2: 8.8.4.4

- name: Set only the search domain
  stevefulme1.proxmox.proxmox_node_dns:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    search: lab.example.com
'''

RETURN = r'''
dns:
  description: The current DNS configuration after changes.
  type: dict
  returned: always
  sample:
    search: example.com
    dns1: 8.8.8.8
    dns2: 8.8.4.4
diff:
  description: Dictionary of changed settings showing before and after values.
  type: dict
  returned: changed
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            search=dict(type='str'),
            dns1=dict(type='str'),
            dns2=dict(type='str'),
            dns3=dict(type='str'),
            state=dict(type='str', choices=['present'], default='present'),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']

    try:
        current = module.proxmox_api.nodes(node).dns.get()
    except Exception as e:
        module.fail_json(msg="Failed to get DNS settings for node '{0}': {1}".format(node, e))

    desired_keys = ['search', 'dns1', 'dns2', 'dns3']
    changes = {}
    for key in desired_keys:
        desired_value = module.params.get(key)
        if desired_value is not None:
            current_value = current.get(key, '')
            if str(desired_value) != str(current_value):
                changes[key] = desired_value

    if not changes:
        module.exit_json(changed=False, dns=current)

    diff = {key: {'before': current.get(key, ''), 'after': changes[key]} for key in changes}

    if module.check_mode:
        module.exit_json(changed=True, dns=current, diff=diff)

    try:
        module.proxmox_api.nodes(node).dns.put(**changes)
        updated = module.proxmox_api.nodes(node).dns.get()
    except Exception as e:
        module.fail_json(msg="Failed to update DNS settings for node '{0}': {1}".format(node, e))

    module.exit_json(changed=True, dns=updated, diff=diff)


if __name__ == '__main__':
    main()
