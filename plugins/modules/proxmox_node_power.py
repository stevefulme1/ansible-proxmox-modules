#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_power
short_description: Reboot or shutdown a Proxmox VE node
description:
  - Reboot or shutdown a Proxmox VE node.
  - This is a destructive operation and does not support check mode.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node to reboot or shutdown.
    type: str
    required: true
  command:
    description:
      - The power command to execute.
      - C(reboot) reboots the node.
      - C(shutdown) shuts down the node.
    type: str
    required: true
    choices:
      - reboot
      - shutdown
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Reboot a Proxmox node
  stevefulme1.proxmox.proxmox_node_power:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    command: reboot

- name: Shutdown a Proxmox node
  stevefulme1.proxmox.proxmox_node_power:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    command: shutdown
'''

RETURN = r'''
node:
  description: The node that was targeted.
  type: str
  returned: always
  sample: pve1
command:
  description: The power command that was executed.
  type: str
  returned: always
  sample: reboot
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "Node pve1 reboot command sent successfully."
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


def main():
    module_args = dict(
        node=dict(type='str', required=True),
        command=dict(type='str', required=True, choices=['reboot', 'shutdown']),
    )

    proxmox = ProxmoxModule(
        argument_spec=module_args,
        supports_check_mode=False,
    )
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    node = params['node']
    command = params['command']

    try:
        api.nodes(node).status.post(command=command)
    except Exception as e:
        module.fail_json(msg="Failed to %s node %s: %s" % (command, node, str(e)))

    module.exit_json(
        changed=True,
        node=node,
        command=command,
        msg="Node %s %s command sent successfully." % (node, command),
    )


if __name__ == '__main__':
    main()
