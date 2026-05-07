#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_firewall_rule
short_description: Manage Proxmox VE firewall rules
description:
  - Create, update, or delete firewall rules at cluster, host, or VM scope in Proxmox VE.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  scope:
    description: The scope at which to manage the firewall rule.
    type: str
    choices: ['cluster', 'host', 'vm']
    default: cluster
  node:
    description: Node name. Required for host and vm scope.
    type: str
  vmid:
    description: VM ID. Required for vm scope.
    type: int
  action:
    description: The action to take (ACCEPT, DROP, REJECT).
    type: str
    choices: ['ACCEPT', 'DROP', 'REJECT']
  type:
    description: Rule direction or group reference.
    type: str
    choices: ['in', 'out', 'group']
  enable:
    description: Whether the rule is enabled.
    type: bool
  source:
    description: Source address or alias.
    type: str
  dest:
    description: Destination address or alias.
    type: str
  sport:
    description: Source port or port range.
    type: str
  dport:
    description: Destination port or port range.
    type: str
  proto:
    description: IP protocol (tcp, udp, icmp, etc.).
    type: str
  comment:
    description: Rule comment.
    type: str
  pos:
    description: Rule position (used to identify existing rules).
    type: int
  macro:
    description: Predefined macro to use.
    type: str
  iface:
    description: Network interface.
    type: str
  log:
    description: Log level.
    type: str
    choices: ['nolog', 'emerg', 'alert', 'crit', 'err', 'warning', 'notice', 'info', 'debug']
  state:
    description: Whether the rule should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Add a cluster-level firewall rule to accept SSH
  stevefulme1.proxmox.proxmox_firewall_rule:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    scope: cluster
    action: ACCEPT
    type: in
    proto: tcp
    dport: "22"
    comment: Allow SSH
    state: present

- name: Add a host-level firewall rule
  stevefulme1.proxmox.proxmox_firewall_rule:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    scope: host
    node: pve1
    action: ACCEPT
    type: in
    proto: tcp
    dport: "8006"
    comment: Allow PVE web UI
    state: present

- name: Add a VM firewall rule
  stevefulme1.proxmox.proxmox_firewall_rule:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    scope: vm
    node: pve1
    vmid: 100
    action: ACCEPT
    type: in
    proto: tcp
    dport: "80,443"
    comment: Allow HTTP/HTTPS
    state: present

- name: Remove a firewall rule by position
  stevefulme1.proxmox.proxmox_firewall_rule:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    scope: cluster
    pos: 0
    state: absent
'''

RETURN = r'''
pos:
  description: The position of the rule that was managed.
  returned: when available
  type: int
  sample: 0
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def _get_firewall_api(api, params):
    """Return the correct firewall API endpoint based on scope."""
    scope = params['scope']
    if scope == 'cluster':
        return api.cluster.firewall.rules
    elif scope == 'host':
        return api.nodes(params['node']).firewall.rules
    elif scope == 'vm':
        return api.nodes(params['node']).qemu(params['vmid']).firewall.rules
    return None


def _rule_matches(rule, params):
    """Check if an existing rule matches the desired rule by key fields."""
    match_fields = ['action', 'type', 'source', 'dest', 'proto', 'dport']
    for field in match_fields:
        desired = params.get(field)
        if desired is not None and str(rule.get(field, '')) != str(desired):
            return False
        if desired is None and rule.get(field):
            return False
    return True


def main():
    module_args = dict(
        scope=dict(type='str', choices=['cluster', 'host', 'vm'], default='cluster'),
        node=dict(type='str'),
        vmid=dict(type='int'),
        action=dict(type='str', choices=['ACCEPT', 'DROP', 'REJECT']),
        type=dict(type='str', choices=['in', 'out', 'group']),
        enable=dict(type='bool'),
        source=dict(type='str'),
        dest=dict(type='str'),
        sport=dict(type='str'),
        dport=dict(type='str'),
        proto=dict(type='str'),
        comment=dict(type='str'),
        pos=dict(type='int'),
        macro=dict(type='str'),
        iface=dict(type='str'),
        log=dict(type='str', choices=['nolog', 'emerg', 'alert', 'crit', 'err', 'warning', 'notice', 'info', 'debug']),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(
        argument_spec=module_args,
        required_if=[
            ('scope', 'host', ['node']),
            ('scope', 'vm', ['node', 'vmid']),
            ('state', 'present', ['action', 'type']),
        ],
    )
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    state = params['state']
    fw_api = _get_firewall_api(api, params)

    # Get existing rules
    try:
        rules = fw_api.get()
    except Exception as e:
        module.fail_json(msg="Failed to get firewall rules: %s" % str(e))

    # Find matching rule
    existing = None
    existing_pos = None

    if params.get('pos') is not None:
        # Identify by position
        for rule in rules:
            if rule.get('pos') == params['pos']:
                existing = rule
                existing_pos = params['pos']
                break
    else:
        # Identify by matching fields
        for rule in rules:
            if _rule_matches(rule, params):
                existing = rule
                existing_pos = rule.get('pos')
                break

    changed = False
    result = dict(changed=False)

    if state == 'absent':
        if existing is not None:
            if not module.check_mode:
                try:
                    fw_api(existing_pos).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete firewall rule at pos %s: %s" % (existing_pos, str(e)))
            changed = True
            result['pos'] = existing_pos
    else:
        rule_data = dict()
        rule_fields = [
            'action', 'type', 'enable', 'source', 'dest', 'sport', 'dport',
            'proto', 'comment', 'macro', 'iface', 'log',
        ]
        for field in rule_fields:
            if params.get(field) is not None:
                value = params[field]
                if field == 'enable':
                    value = int(value)
                rule_data[field] = value

        if existing is not None:
            # Check if update is needed
            needs_update = False
            for key, value in rule_data.items():
                if str(existing.get(key, '')) != str(value):
                    needs_update = True
                    break

            if needs_update:
                if not module.check_mode:
                    try:
                        fw_api(existing_pos).put(**rule_data)
                    except Exception as e:
                        module.fail_json(msg="Failed to update firewall rule at pos %s: %s" % (existing_pos, str(e)))
                changed = True
            result['pos'] = existing_pos
        else:
            if params.get('pos') is not None:
                rule_data['pos'] = params['pos']
            if not module.check_mode:
                try:
                    fw_api.post(**rule_data)
                except Exception as e:
                    module.fail_json(msg="Failed to create firewall rule: %s" % str(e))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
