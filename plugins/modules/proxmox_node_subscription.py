#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_subscription
short_description: Manage node subscription in Proxmox VE
version_added: "1.0.0"
description:
  - Set, check, or remove subscription keys on Proxmox VE nodes via the
    C(/nodes/{node}/subscription) API endpoint.
  - Use C(state=present) with C(key) to set a subscription key.
  - Use C(state=present) without C(key) (or with C(force)) to re-check the
    subscription status against the server.
  - Use C(state=absent) to remove the subscription key.
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
    description: Target Proxmox VE node name.
    type: str
    required: true
  key:
    description:
      - The subscription key to set (e.g. C(pve2s-1234567890)).
    type: str
  force:
    description:
      - Force re-check of subscription status against the licensing server.
    type: bool
    default: false
  state:
    description:
      - C(present) to set or check subscription.
      - C(absent) to remove the subscription key.
    type: str
    choices: ['present', 'absent']
    default: present
author:
  - sfulmer
'''

EXAMPLES = r'''
- name: Set a subscription key
  sfulmer.proxmox.proxmox_node_subscription:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    key: "pve2s-1234567890"
    state: present

- name: Force re-check subscription status
  sfulmer.proxmox.proxmox_node_subscription:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    force: true
    state: present

- name: Remove subscription key
  sfulmer.proxmox.proxmox_node_subscription:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    state: absent
'''

RETURN = r'''
subscription:
  description: The current subscription status after the operation.
  returned: success
  type: dict
  sample:
    status: "Active"
    level: "s"
    key: "pve2s-1234567890"
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    argument_spec = dict(
        node=dict(type='str', required=True),
        key=dict(type='str', no_log=True),
        force=dict(type='bool', default=False),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    proxmox = ProxmoxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module = proxmox.module
    params = module.params
    node = params['node']
    state = params['state']

    api = proxmox.get_api()

    # Get current subscription status
    try:
        current = api.nodes(node).subscription.get()
    except Exception as e:
        module.fail_json(
            msg="Failed to query subscription on node '%s': %s" % (node, str(e)))

    changed = False

    if state == 'absent':
        # Remove subscription key
        if current.get('key') or current.get('status', '').lower() == 'active':
            changed = True
            if not module.check_mode:
                try:
                    api.nodes(node).subscription.delete()
                except Exception as e:
                    module.fail_json(
                        msg="Failed to remove subscription from node '%s': %s"
                        % (node, str(e)))
        # Re-read status
        if not module.check_mode:
            try:
                current = api.nodes(node).subscription.get()
            except Exception:
                pass
        module.exit_json(changed=changed, subscription=current)

    # state == present
    if params.get('key'):
        # Set subscription key
        current_key = current.get('key', '')
        if current_key != params['key']:
            changed = True
            if not module.check_mode:
                try:
                    api.nodes(node).subscription.put(key=params['key'])
                except Exception as e:
                    module.fail_json(
                        msg="Failed to set subscription key on node '%s': %s"
                        % (node, str(e)))

    if params.get('force') or (not params.get('key') and not changed):
        # Re-check subscription status
        changed = True
        if not module.check_mode:
            try:
                api.nodes(node).subscription.post()
            except Exception as e:
                module.fail_json(
                    msg="Failed to check subscription on node '%s': %s"
                    % (node, str(e)))

    # Re-read current status
    if not module.check_mode:
        try:
            current = api.nodes(node).subscription.get()
        except Exception:
            pass

    module.exit_json(changed=changed, subscription=current)


if __name__ == '__main__':
    main()
