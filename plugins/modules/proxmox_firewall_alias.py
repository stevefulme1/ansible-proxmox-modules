#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_firewall_alias
short_description: Manage Proxmox VE firewall aliases
description:
  - Create, update, or delete firewall aliases in a Proxmox VE cluster.
  - Aliases map a name to an IP address or CIDR for use in firewall rules.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  name:
    description: The alias name.
    type: str
    required: true
  cidr:
    description: IP address or network in CIDR notation. Required when state is present.
    type: str
  comment:
    description: Comment for the alias.
    type: str
  state:
    description: Whether the alias should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create a firewall alias
  stevefulme1.proxmox.proxmox_firewall_alias:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    name: webserver
    cidr: 10.0.1.10
    comment: Main web server
    state: present

- name: Remove a firewall alias
  stevefulme1.proxmox.proxmox_firewall_alias:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    name: webserver
    state: absent
'''

RETURN = r'''
name:
  description: The alias name that was managed.
  returned: always
  type: str
  sample: webserver
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        cidr=dict(type='str'),
        comment=dict(type='str'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(
        argument_spec=module_args,
        required_if=[
            ('state', 'present', ['cidr']),
        ],
    )
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    alias_name = params['name']
    state = params['state']

    # Get existing aliases
    try:
        aliases = api.cluster.firewall.aliases.get()
    except Exception as e:
        module.fail_json(msg="Failed to get firewall aliases: %s" % str(e))

    existing = None
    for a in aliases:
        if a.get('name') == alias_name:
            existing = a
            break

    changed = False
    result = dict(name=alias_name, changed=False)

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.cluster.firewall.aliases(alias_name).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete alias '%s': %s" % (alias_name, str(e)))
            changed = True
    else:
        config = dict(cidr=params['cidr'])
        if params.get('comment') is not None:
            config['comment'] = params['comment']

        if existing:
            needs_update = False
            if existing.get('cidr') != params['cidr']:
                needs_update = True
            if params.get('comment') is not None and existing.get('comment', '') != params['comment']:
                needs_update = True

            if needs_update:
                if not module.check_mode:
                    update_data = dict(cidr=params['cidr'])
                    if params.get('comment') is not None:
                        update_data['comment'] = params['comment']
                    # Proxmox API uses PUT with the alias name and rename field
                    update_data['rename'] = alias_name
                    try:
                        api.cluster.firewall.aliases(alias_name).put(**update_data)
                    except Exception as e:
                        module.fail_json(msg="Failed to update alias '%s': %s" % (alias_name, str(e)))
                changed = True
        else:
            create_data = dict(name=alias_name, cidr=params['cidr'])
            if params.get('comment') is not None:
                create_data['comment'] = params['comment']
            if not module.check_mode:
                try:
                    api.cluster.firewall.aliases.post(**create_data)
                except Exception as e:
                    module.fail_json(msg="Failed to create alias '%s': %s" % (alias_name, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
