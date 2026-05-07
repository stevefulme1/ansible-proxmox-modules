#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_firewall_group
short_description: Manage Proxmox VE firewall security groups
description:
  - Create or delete firewall security groups in a Proxmox VE cluster.
  - Rules within groups are managed by the proxmox_firewall_rule module using type=group.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  group:
    description: The security group name.
    type: str
    required: true
  comment:
    description: Comment for the security group.
    type: str
  state:
    description: Whether the security group should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create a firewall security group
  stevefulme1.proxmox.proxmox_firewall_group:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    group: webservers
    comment: Rules for web servers
    state: present

- name: Remove a firewall security group
  stevefulme1.proxmox.proxmox_firewall_group:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    group: webservers
    state: absent
'''

RETURN = r'''
group:
  description: The security group name that was managed.
  returned: always
  type: str
  sample: webservers
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        group=dict(type='str', required=True),
        comment=dict(type='str'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    group_name = params['group']
    state = params['state']

    # Get existing groups
    try:
        groups = api.cluster.firewall.groups.get()
    except Exception as e:
        module.fail_json(msg="Failed to get firewall groups: %s" % str(e))

    existing = None
    for g in groups:
        if g.get('group') == group_name:
            existing = g
            break

    changed = False
    result = dict(group=group_name, changed=False)

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.cluster.firewall.groups(group_name).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete security group '%s': %s" % (group_name, str(e)))
            changed = True
    else:
        if existing:
            # Check if comment needs updating
            if params.get('comment') is not None and existing.get('comment', '') != params['comment']:
                # Proxmox doesn't have a direct update for group metadata;
                # we create a dummy rule POST with comment to update, or simply note no change.
                # In practice, groups are containers -- comment is set at creation only.
                # For a workaround, delete and recreate.
                if not module.check_mode:
                    try:
                        # Delete all rules in the group first
                        rules = api.cluster.firewall.groups(group_name).get()
                        for rule in rules:
                            api.cluster.firewall.groups(group_name)(rule['pos']).delete()
                        api.cluster.firewall.groups(group_name).delete()
                        create_data = dict(group=group_name)
                        if params.get('comment') is not None:
                            create_data['comment'] = params['comment']
                        api.cluster.firewall.groups.post(**create_data)
                    except Exception as e:
                        module.fail_json(msg="Failed to update security group '%s': %s" % (group_name, str(e)))
                changed = True
        else:
            create_data = dict(group=group_name)
            if params.get('comment') is not None:
                create_data['comment'] = params['comment']
            if not module.check_mode:
                try:
                    api.cluster.firewall.groups.post(**create_data)
                except Exception as e:
                    module.fail_json(msg="Failed to create security group '%s': %s" % (group_name, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
