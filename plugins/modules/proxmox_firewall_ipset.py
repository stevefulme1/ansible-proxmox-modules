#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_firewall_ipset
short_description: Manage Proxmox VE firewall IP sets
description:
  - Create, update, or delete firewall IP sets in a Proxmox VE cluster.
  - Manages both the IP set itself and its member entries.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  name:
    description: The name of the IP set.
    type: str
    required: true
  comment:
    description: Comment for the IP set.
    type: str
  members:
    description: List of IP set members.
    type: list
    elements: dict
    suboptions:
      cidr:
        description: IP address or network in CIDR notation.
        type: str
        required: true
      comment:
        description: Comment for this member entry.
        type: str
      nomatch:
        description: If true, this entry is an exclusion (nomatch).
        type: bool
        default: false
  state:
    description: Whether the IP set should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create an IP set with members
  stevefulme1.proxmox.proxmox_firewall_ipset:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    name: trusted_nets
    comment: Trusted networks
    members:
      - cidr: 10.0.0.0/8
        comment: Private range
      - cidr: 192.168.1.0/24
        comment: Office network
      - cidr: 192.168.1.50
        nomatch: true
        comment: Exclude this host
    state: present

- name: Remove an IP set
  stevefulme1.proxmox.proxmox_firewall_ipset:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    name: trusted_nets
    state: absent
'''

RETURN = r'''
name:
  description: The IP set name that was managed.
  returned: always
  type: str
  sample: trusted_nets
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    member_spec = dict(
        cidr=dict(type='str', required=True),
        comment=dict(type='str'),
        nomatch=dict(type='bool', default=False),
    )

    module_args = dict(
        name=dict(type='str', required=True),
        comment=dict(type='str'),
        members=dict(type='list', elements='dict', options=member_spec),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    ipset_name = params['name']
    state = params['state']

    # Get existing IP sets
    try:
        ipsets = api.cluster.firewall.ipset.get()
    except Exception as e:
        module.fail_json(msg="Failed to get IP sets: %s" % str(e))

    existing = None
    for s in ipsets:
        if s.get('name') == ipset_name:
            existing = s
            break

    changed = False
    result = dict(name=ipset_name, changed=False)

    if state == 'absent':
        if existing:
            if not module.check_mode:
                # First remove all members, then the ipset
                try:
                    members = api.cluster.firewall.ipset(ipset_name).get()
                    for m in members:
                        api.cluster.firewall.ipset(ipset_name)(m['cidr']).delete()
                    api.cluster.firewall.ipset(ipset_name).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete IP set '%s': %s" % (ipset_name, str(e)))
            changed = True
    else:
        if not existing:
            # Create the IP set
            create_data = dict(name=ipset_name)
            if params.get('comment') is not None:
                create_data['comment'] = params['comment']
            if not module.check_mode:
                try:
                    api.cluster.firewall.ipset.post(**create_data)
                except Exception as e:
                    module.fail_json(msg="Failed to create IP set '%s': %s" % (ipset_name, str(e)))
            changed = True

        # Manage members if specified
        if params.get('members') is not None:
            if not module.check_mode:
                try:
                    current_members = api.cluster.firewall.ipset(ipset_name).get() if not changed or not module.check_mode else []
                except Exception:
                    current_members = []

                current_cidrs = {m['cidr']: m for m in current_members}
                desired_cidrs = {m['cidr']: m for m in params['members']}

                # Remove members not in desired list
                for cidr in list(current_cidrs.keys()):
                    if cidr not in desired_cidrs:
                        try:
                            api.cluster.firewall.ipset(ipset_name)(cidr).delete()
                        except Exception as e:
                            module.fail_json(msg="Failed to remove member '%s' from IP set: %s" % (cidr, str(e)))
                        changed = True

                # Add or update members
                for cidr, member in desired_cidrs.items():
                    member_data = dict(cidr=cidr)
                    if member.get('comment'):
                        member_data['comment'] = member['comment']
                    if member.get('nomatch'):
                        member_data['nomatch'] = 1

                    if cidr not in current_cidrs:
                        try:
                            api.cluster.firewall.ipset(ipset_name).post(**member_data)
                        except Exception as e:
                            module.fail_json(msg="Failed to add member '%s' to IP set: %s" % (cidr, str(e)))
                        changed = True
                    else:
                        # Check if update needed
                        cur = current_cidrs[cidr]
                        needs_update = False
                        if member.get('comment', '') != cur.get('comment', ''):
                            needs_update = True
                        if bool(member.get('nomatch')) != bool(cur.get('nomatch')):
                            needs_update = True
                        if needs_update:
                            try:
                                api.cluster.firewall.ipset(ipset_name)(cidr).put(**member_data)
                            except Exception as e:
                                module.fail_json(msg="Failed to update member '%s' in IP set: %s" % (cidr, str(e)))
                            changed = True
            else:
                # In check mode, just mark changed if members are specified and set is new
                if not existing:
                    changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
