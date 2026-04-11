#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_time
short_description: Manage Proxmox VE node timezone
description:
  - Manage the timezone configuration on a Proxmox VE node.
  - Uses the C(/nodes/{node}/time) API endpoint to read and update timezone settings.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The name of the Proxmox VE node to manage.
    type: str
    required: true
  timezone:
    description:
      - The desired timezone for the node.
      - Must be a valid timezone string such as C(America/New_York) or C(UTC).
    type: str
    required: true
  state:
    description:
      - The desired state of the timezone configuration.
    type: str
    choices: ['present']
    default: present
extends_documentation_fragment:
  - sfulmer.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Set timezone to America/New_York
  sfulmer.proxmox.proxmox_node_time:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    timezone: America/New_York

- name: Set timezone to UTC
  sfulmer.proxmox.proxmox_node_time:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    timezone: UTC
'''

RETURN = r'''
timezone:
  description: The current timezone after changes.
  type: str
  returned: always
  sample: America/New_York
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            timezone=dict(type='str', required=True),
            state=dict(type='str', choices=['present'], default='present'),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    desired_tz = module.params['timezone']

    try:
        current = module.proxmox_api.nodes(node).time.get()
    except Exception as e:
        module.fail_json(msg="Failed to get time settings for node '{0}': {1}".format(node, e))

    current_tz = current.get('timezone', '')

    if current_tz == desired_tz:
        module.exit_json(changed=False, timezone=current_tz)

    if module.check_mode:
        module.exit_json(changed=True, timezone=desired_tz)

    try:
        module.proxmox_api.nodes(node).time.put(timezone=desired_tz)
        updated = module.proxmox_api.nodes(node).time.get()
    except Exception as e:
        module.fail_json(msg="Failed to update timezone for node '{0}': {1}".format(node, e))

    module.exit_json(changed=True, timezone=updated.get('timezone', desired_tz))


if __name__ == '__main__':
    main()
