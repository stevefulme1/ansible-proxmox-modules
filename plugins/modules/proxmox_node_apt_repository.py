#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_apt_repository
short_description: Manage APT repository configuration on Proxmox VE nodes
description:
  - Add, remove, or configure APT repositories on Proxmox VE nodes.
  - Supports managing enterprise and no-subscription repositories for both PVE and Ceph.
  - Idempotent — checks current repository state before making changes.
version_added: "1.1.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node to manage APT repositories on.
    type: str
    required: true
  handle:
    description:
      - The repository handle identifier.
      - Common handles include C(pve-enterprise), C(pve-no-subscription),
        C(ceph-quincy-enterprise), C(ceph-quincy-no-subscription).
    type: str
    required: true
  enabled:
    description:
      - Whether the repository should be enabled or disabled.
    type: bool
    default: true
  state:
    description:
      - Whether the repository should be present or absent.
    type: str
    default: present
    choices:
      - present
      - absent
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Enable the no-subscription repository
  stevefulme1.proxmox.proxmox_node_apt_repository:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    handle: pve-no-subscription
    enabled: true
    state: present

- name: Disable the enterprise repository
  stevefulme1.proxmox.proxmox_node_apt_repository:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    handle: pve-enterprise
    enabled: false

- name: Add Ceph no-subscription repository
  stevefulme1.proxmox.proxmox_node_apt_repository:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    handle: ceph-quincy-no-subscription
    state: present

- name: Remove the enterprise repository
  stevefulme1.proxmox.proxmox_node_apt_repository:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    handle: pve-enterprise
    state: absent
'''

RETURN = r'''
handle:
  description: The repository handle that was managed.
  type: str
  returned: always
  sample: pve-no-subscription
enabled:
  description: Whether the repository is enabled.
  type: bool
  returned: always
  sample: true
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "Repository pve-no-subscription added and enabled on node pve1."
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def _find_repo(repos_data, handle):
    """Search existing repositories for one matching the given handle.

    Returns a tuple of (file_path, index, repo_dict) if found, or (None, None, None).
    The Proxmox API returns repos grouped by file; each file contains a list of
    repository entries that may carry a ``Handle`` field matching standard handles.
    """
    files = repos_data.get('files', [])
    for file_entry in files:
        file_path = file_entry.get('path', '')
        for idx, repo in enumerate(file_entry.get('repositories', [])):
            if repo.get('Handle') == handle:
                return file_path, idx, repo
    return None, None, None


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            handle=dict(type='str', required=True),
            enabled=dict(type='bool', default=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    handle = module.params['handle']
    enabled = module.params['enabled']
    state = module.params['state']

    api = module.get_api()

    # Fetch current repository configuration
    try:
        repos_data = api.nodes(node).apt.repositories.get()
    except Exception as e:
        module.fail_json(msg="Failed to list APT repositories on node '{0}': {1}".format(node, e))

    file_path, repo_idx, existing_repo = _find_repo(repos_data, handle)

    changed = False

    if state == 'present':
        if existing_repo is not None:
            # Repository exists — check if enabled state matches
            current_enabled = bool(existing_repo.get('Enabled', True))
            if current_enabled != enabled:
                changed = True
                if not module.check_mode:
                    try:
                        api.nodes(node).apt.repositories.put(
                            path=file_path,
                            index=repo_idx,
                            enabled=int(enabled),
                        )
                    except Exception as e:
                        module.fail_json(msg="Failed to update repository '{0}' on node '{1}': {2}".format(handle, node, e))
                action = "enabled" if enabled else "disabled"
                msg = "Repository {0} {1} on node {2}.".format(handle, action, node)
            else:
                msg = "Repository {0} already {1} on node {2}.".format(handle, "enabled" if enabled else "disabled", node)
        else:
            # Repository does not exist — add it
            changed = True
            if not module.check_mode:
                try:
                    api.nodes(node).apt.repositories.post(handle=handle)
                except Exception as e:
                    module.fail_json(msg="Failed to add repository '{0}' on node '{1}': {2}".format(handle, node, e))
                # If the user wants the repo disabled after adding, update it
                if not enabled:
                    try:
                        updated_data = api.nodes(node).apt.repositories.get()
                        new_path, new_idx, _ = _find_repo(updated_data, handle)
                        if new_path is not None:
                            api.nodes(node).apt.repositories.put(
                                path=new_path,
                                index=new_idx,
                                enabled=0,
                            )
                    except Exception as e:
                        module.fail_json(msg="Repository '{0}' added but failed to disable it: {1}".format(handle, e))
            msg = "Repository {0} added on node {1}.".format(handle, node)

    elif state == 'absent':
        if existing_repo is not None:
            # Proxmox API does not provide a delete endpoint for individual repos.
            # The standard approach is to disable the repository.
            current_enabled = bool(existing_repo.get('Enabled', True))
            if current_enabled:
                changed = True
                if not module.check_mode:
                    try:
                        api.nodes(node).apt.repositories.put(
                            path=file_path,
                            index=repo_idx,
                            enabled=0,
                        )
                    except Exception as e:
                        module.fail_json(msg="Failed to disable repository '{0}' on node '{1}': {2}".format(handle, node, e))
                msg = "Repository {0} disabled on node {1}.".format(handle, node)
            else:
                msg = "Repository {0} already disabled on node {1}.".format(handle, node)
        else:
            msg = "Repository {0} does not exist on node {1}.".format(handle, node)

    module.exit_json(changed=changed, handle=handle, enabled=enabled, msg=msg)


if __name__ == '__main__':
    main()
