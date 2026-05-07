#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_wake_on_lan
short_description: Trigger Wake-on-LAN for a Proxmox VE node
version_added: "1.0.0"
description:
  - Send a Wake-on-LAN magic packet to a Proxmox VE node via the
    C(/nodes/{node}/wakeonlan) API endpoint.
  - This is an action module that always reports C(changed=True).
  - The target node must have WoL configured in its BIOS/UEFI and the
    MAC address must be known to the cluster.
options:
  api_host:
    description: Proxmox VE API host (hostname or IP).
    type: str
    required: true
  api_user:
    description: Proxmox VE API user (e.g. C(root@pam)).
    type: str
    required: true
  api_password:
    description: Password for API user.
    type: str
  api_token_id:
    description: API token ID.
    type: str
  api_token_secret:
    description: API token secret.
    type: str
  validate_certs:
    description: Whether to validate SSL certificates.
    type: bool
    default: true
  node:
    description: Target Proxmox VE node name to wake.
    type: str
    required: true
author:
  - sfulmer
'''

EXAMPLES = r'''
- name: Wake up a node via WoL
  stevefulme1.proxmox.proxmox_node_wake_on_lan:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve2
'''

RETURN = r'''
node:
  description: The node name that was sent a WoL packet.
  returned: success
  type: str
  sample: "pve2"
mac:
  description: The MAC address the WoL packet was sent to (if returned by the API).
  returned: success, not check_mode
  type: str
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    argument_spec = dict(
        node=dict(type='str', required=True),
    )

    proxmox = ProxmoxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module = proxmox.module
    node = module.params['node']

    api = proxmox.get_api()
    result = dict(node=node)

    # Action module: always changed
    changed = True
    if not module.check_mode:
        try:
            response = api.nodes(node).wakeonlan.post()
            # The API returns the MAC address as a string
            if response:
                result['mac'] = response
        except Exception as e:
            module.fail_json(
                msg="Failed to send Wake-on-LAN to node '%s': %s" % (node, str(e)))

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
