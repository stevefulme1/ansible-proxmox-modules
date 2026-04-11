#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_apt
short_description: Manage APT repositories on Proxmox VE nodes
version_added: "1.0.0"
description:
  - List, add, enable, or disable APT repositories on Proxmox VE nodes
    via the C(/nodes/{node}/apt/repositories) API endpoint.
  - Use C(state=present) with C(handle) to add a standard repository.
  - Use C(index) and C(enabled) to enable or disable an existing repository.
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
  index:
    description:
      - The repository index number (from GET) to enable or disable.
      - Required when modifying an existing repository entry.
    type: int
  enabled:
    description:
      - Whether the repository at the given C(index) should be enabled.
    type: bool
  handle:
    description:
      - Standard repository handle to add (e.g. C(no-subscription), C(enterprise), C(test)).
      - Used with C(state=present) to add a standard repository.
    type: str
  digest:
    description:
      - SHA digest from a previous GET for concurrency safety.
    type: str
  state:
    description:
      - C(present) to add a standard repository via C(handle) or modify via C(index).
      - C(absent) is not supported by the Proxmox API for APT repositories.
    type: str
    choices: ['present', 'absent']
    default: present
author:
  - sfulmer
'''

EXAMPLES = r'''
- name: Add the no-subscription repository
  sfulmer.proxmox.proxmox_node_apt:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    handle: no-subscription
    state: present

- name: Disable enterprise repository at index 0
  sfulmer.proxmox.proxmox_node_apt:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    index: 0
    enabled: false
    state: present

- name: Enable repository at index 1
  sfulmer.proxmox.proxmox_node_apt:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    index: 1
    enabled: true
    state: present
'''

RETURN = r'''
repositories:
  description: The list of APT repositories after the operation.
  returned: success
  type: list
  elements: dict
digest:
  description: Configuration digest for concurrency control.
  returned: success
  type: str
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    argument_spec = dict(
        node=dict(type='str', required=True),
        index=dict(type='int'),
        enabled=dict(type='bool'),
        handle=dict(type='str'),
        digest=dict(type='str'),
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

    if state == 'absent':
        module.fail_json(msg="The Proxmox API does not support removing APT repositories. "
                         "Use index/enabled to disable a repository instead.")

    api = proxmox.get_api()

    try:
        current = api.nodes(node).apt.repositories.get()
    except Exception as e:
        module.fail_json(msg="Failed to query APT repositories on node '%s': %s" % (node, str(e)))

    changed = False
    result = dict()

    # Add a standard repository by handle
    if params.get('handle'):
        handle = params['handle']
        # Check if the handle is already present by looking at existing standard repos
        existing_handles = []
        for file_info in current.get('files', []):
            for repo in file_info.get('repositories', []):
                for info in current.get('infos', []):
                    if info.get('property') == 'handle' and info.get('value') == handle:
                        existing_handles.append(info)

        if not existing_handles:
            changed = True
            if not module.check_mode:
                post_params = dict(handle=handle)
                if params.get('digest'):
                    post_params['digest'] = params['digest']
                try:
                    api.nodes(node).apt.repositories.post(**post_params)
                except Exception as e:
                    module.fail_json(
                        msg="Failed to add standard repository '%s' on node '%s': %s"
                        % (handle, node, str(e)))

    # Enable/disable a repository by index
    if params.get('index') is not None and params.get('enabled') is not None:
        idx = params['index']
        desired_enabled = params['enabled']

        # Find current state of the repo at the given index
        repo_count = 0
        current_enabled = None
        for file_info in current.get('files', []):
            for repo in file_info.get('repositories', []):
                if repo_count == idx:
                    current_enabled = repo.get('Enabled', True)
                    break
                repo_count += 1
            if current_enabled is not None:
                break

        if current_enabled is None:
            module.fail_json(msg="Repository index %d not found on node '%s'." % (idx, node))

        # Proxmox API uses 1/0 for enabled
        if bool(current_enabled) != desired_enabled:
            changed = True
            if not module.check_mode:
                put_params = dict(
                    index=idx,
                    enabled=1 if desired_enabled else 0,
                )
                if params.get('digest'):
                    put_params['digest'] = params['digest']
                try:
                    api.nodes(node).apt.repositories.put(**put_params)
                except Exception as e:
                    module.fail_json(
                        msg="Failed to update repository index %d on node '%s': %s"
                        % (idx, node, str(e)))

    # Re-read current state
    if not module.check_mode:
        try:
            current = api.nodes(node).apt.repositories.get()
        except Exception:
            pass

    repos = []
    for file_info in current.get('files', []):
        for repo in file_info.get('repositories', []):
            repos.append(repo)

    result['repositories'] = repos
    result['digest'] = current.get('digest', '')

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
