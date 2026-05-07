#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_traffic_control
short_description: Manage Proxmox Backup Server bandwidth/traffic control rules
description:
  - Create, update, or remove traffic control (bandwidth limit) rules on a Proxmox Backup Server.
  - Uses the C(/config/traffic-control) API endpoint.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  name:
    description: Unique name for the traffic control rule.
    type: str
    required: true
  rate_in:
    description: Inbound bandwidth rate limit (e.g. C(10mbit)).
    type: str
  rate_out:
    description: Outbound bandwidth rate limit (e.g. C(10mbit)).
    type: str
  burst_in:
    description: Inbound burst allowance.
    type: str
  burst_out:
    description: Outbound burst allowance.
    type: str
  network:
    description:
      - List of CIDR network specifications that this rule applies to.
    type: list
    elements: str
  timeframe:
    description:
      - List of time specifications that define when this rule is active.
    type: list
    elements: str
  comment:
    description: Description for the traffic control rule.
    type: str
  state:
    description: Whether the traffic control rule should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create a bandwidth limit rule
  stevefulme1.proxmox.proxmox_pbs_traffic_control:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: office-limit
    rate_in: "100mbit"
    rate_out: "50mbit"
    network:
      - "10.0.0.0/8"
      - "192.168.1.0/24"
    comment: Bandwidth limit for office network
    state: present

- name: Create a time-based traffic control rule
  stevefulme1.proxmox.proxmox_pbs_traffic_control:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: business-hours-limit
    rate_in: "50mbit"
    rate_out: "25mbit"
    network:
      - "10.0.0.0/8"
    timeframe:
      - "mon..fri 8:00-18:00"
    comment: Limit during business hours
    state: present

- name: Remove a traffic control rule
  stevefulme1.proxmox.proxmox_pbs_traffic_control:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: office-limit
    state: absent
'''

RETURN = r'''
name:
  description: The traffic control rule name that was managed.
  returned: always
  type: str
  sample: office-limit
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        rate_in=dict(type='str'),
        rate_out=dict(type='str'),
        burst_in=dict(type='str'),
        burst_out=dict(type='str'),
        network=dict(type='list', elements='str'),
        timeframe=dict(type='list', elements='str'),
        comment=dict(type='str'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    name = params['name']
    state = params['state']

    api_key_map = {
        'rate_in': 'rate-in',
        'rate_out': 'rate-out',
        'burst_in': 'burst-in',
        'burst_out': 'burst-out',
    }

    try:
        rules = api('config/traffic-control').get()
    except Exception as e:
        module.fail_json(msg="Failed to list traffic control rules: %s" % str(e))

    existing = None
    for rule in rules:
        if rule.get('name') == name:
            existing = rule
            break

    changed = False
    result = dict(name=name, changed=False)

    config_keys = ['rate_in', 'rate_out', 'burst_in', 'burst_out', 'comment']

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api('config/traffic-control/{0}'.format(name)).delete()
                except Exception as e:
                    module.fail_json(
                        msg="Failed to delete traffic control rule '%s': %s" % (name, str(e))
                    )
            changed = True
    else:
        config = {}
        for key in config_keys:
            if params.get(key) is not None:
                api_key = api_key_map.get(key, key)
                config[api_key] = params[key]

        # Handle list parameters - convert to comma-separated strings for the API
        if params.get('network') is not None:
            config['network'] = ','.join(params['network'])
        if params.get('timeframe') is not None:
            config['timeframe'] = ','.join(params['timeframe'])

        if existing:
            update_params = {}
            for api_key, value in config.items():
                if str(existing.get(api_key, '')) != str(value):
                    update_params[api_key] = value
            if update_params:
                if not module.check_mode:
                    try:
                        api('config/traffic-control/{0}'.format(name)).put(**update_params)
                    except Exception as e:
                        module.fail_json(
                            msg="Failed to update traffic control rule '%s': %s" % (name, str(e))
                        )
                changed = True
        else:
            config['name'] = name
            if not module.check_mode:
                try:
                    api('config/traffic-control').post(**config)
                except Exception as e:
                    module.fail_json(
                        msg="Failed to create traffic control rule '%s': %s" % (name, str(e))
                    )
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
