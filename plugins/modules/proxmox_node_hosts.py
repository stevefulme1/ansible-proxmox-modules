#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_hosts
short_description: Manage Proxmox VE node /etc/hosts entries
description:
  - Manage the full contents of C(/etc/hosts) on a Proxmox VE node.
  - Uses the C(/nodes/{node}/hosts) API endpoint which returns data and a digest.
  - The digest is used for idempotency to detect if changes are needed.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The name of the Proxmox VE node to manage.
    type: str
    required: true
  content:
    description:
      - The full content of the /etc/hosts file.
    type: str
    required: true
  state:
    description:
      - The desired state of the hosts file.
    type: str
    choices: ['present']
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Set hosts file content
  stevefulme1.proxmox.proxmox_node_hosts:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    content: |
      127.0.0.1 localhost
      192.168.1.10 pve1.example.com pve1

- name: Update hosts with multiple entries
  stevefulme1.proxmox.proxmox_node_hosts:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    content: |
      127.0.0.1 localhost
      192.168.1.10 pve1.example.com pve1
      192.168.1.11 pve2.example.com pve2
'''

RETURN = r'''
digest:
  description: The digest of the hosts file after changes.
  type: str
  returned: always
content:
  description: The current content of the hosts file.
  type: str
  returned: always
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            content=dict(type='str', required=True),
            state=dict(type='str', choices=['present'], default='present'),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    desired_content = module.params['content']

    try:
        current = module.proxmox_api.nodes(node).hosts.get()
    except Exception as e:
        module.fail_json(msg="Failed to get hosts file for node '{0}': {1}".format(node, e))

    current_data = current.get('data', '')
    current_digest = current.get('digest', '')

    if current_data.strip() == desired_content.strip():
        module.exit_json(changed=False, digest=current_digest, content=current_data)

    if module.check_mode:
        module.exit_json(changed=True, digest=current_digest, content=desired_content)

    try:
        module.proxmox_api.nodes(node).hosts.post(
            data=desired_content,
            digest=current_digest,
        )
        updated = module.proxmox_api.nodes(node).hosts.get()
    except Exception as e:
        module.fail_json(msg="Failed to update hosts file for node '{0}': {1}".format(node, e))

    module.exit_json(
        changed=True,
        digest=updated.get('digest', ''),
        content=updated.get('data', ''),
    )


if __name__ == '__main__':
    main()
