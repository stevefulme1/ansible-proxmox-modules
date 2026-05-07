#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_firewall_options
short_description: Manage Proxmox VE cluster firewall options
description:
  - Configure cluster-level firewall options in Proxmox VE.
  - This module always applies configuration (no state parameter).
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  enable:
    description: Enable or disable the cluster firewall.
    type: bool
  policy_in:
    description: Default policy for incoming traffic.
    type: str
    choices: ['ACCEPT', 'DROP', 'REJECT']
  policy_out:
    description: Default policy for outgoing traffic.
    type: str
    choices: ['ACCEPT', 'DROP', 'REJECT']
  log_ratelimit:
    description: Log rate limit string (e.g. 'enable=1,rate=1/second,burst=5').
    type: str
'''

EXAMPLES = r'''
- name: Enable cluster firewall with DROP default policy
  stevefulme1.proxmox.proxmox_firewall_options:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    enable: true
    policy_in: DROP
    policy_out: ACCEPT

- name: Disable cluster firewall
  stevefulme1.proxmox.proxmox_firewall_options:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    enable: false
'''

RETURN = r'''
options:
  description: The firewall options that were applied.
  returned: always
  type: dict
  sample:
    enable: 1
    policy_in: DROP
    policy_out: ACCEPT
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        enable=dict(type='bool'),
        policy_in=dict(type='str', choices=['ACCEPT', 'DROP', 'REJECT']),
        policy_out=dict(type='str', choices=['ACCEPT', 'DROP', 'REJECT']),
        log_ratelimit=dict(type='str'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    # Get current options
    try:
        current = api.cluster.firewall.options.get()
    except Exception as e:
        module.fail_json(msg="Failed to get firewall options: %s" % str(e))

    # Build desired options from provided params
    desired = dict()
    if params.get('enable') is not None:
        desired['enable'] = int(params['enable'])
    if params.get('policy_in') is not None:
        desired['policy_in'] = params['policy_in']
    if params.get('policy_out') is not None:
        desired['policy_out'] = params['policy_out']
    if params.get('log_ratelimit') is not None:
        desired['log_ratelimit'] = params['log_ratelimit']

    if not desired:
        module.exit_json(changed=False, options=current, msg="No options specified to configure.")

    # Check if changes are needed
    needs_update = False
    for key, value in desired.items():
        current_val = current.get(key)
        if current_val is None or str(current_val) != str(value):
            needs_update = True
            break

    changed = False
    if needs_update:
        if not module.check_mode:
            try:
                api.cluster.firewall.options.put(**desired)
            except Exception as e:
                module.fail_json(msg="Failed to set firewall options: %s" % str(e))
        changed = True

    result = dict(changed=changed, options=desired)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
