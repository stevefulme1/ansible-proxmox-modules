#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_storage_status_info
short_description: Query storage usage and health in Proxmox VE
description:
  - Retrieve storage usage and health status from a specific node in Proxmox VE.
  - This is an info module that does not modify state.
  - Uses the C(/nodes/{node}/storage/{storage}/status) API endpoint.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node name.
    type: str
    required: true
  storage:
    description:
      - The storage identifier to query.
    type: str
    required: true
  limit:
    description:
      - Maximum number of results to return.
    type: int
    default: 100
  offset:
    description:
      - Number of results to skip for pagination.
    type: int
    default: 0
  max_results:
    description:
      - Maximum total results to return.
    type: int
    default: 1000
'''

EXAMPLES = r'''
- name: Get storage status
  stevefulme1.proxmox.proxmox_storage_status_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    storage: local
  register: storage_status

- name: Display storage usage
  ansible.builtin.debug:
    msg: "Used: {{ storage_status.used }} / Total: {{ storage_status.total }}"
'''

RETURN = r'''
storage:
  description: The storage identifier.
  returned: always
  type: str
  sample: "local"
type:
  description: The storage type.
  returned: always
  type: str
  sample: "dir"
total:
  description: Total storage capacity in bytes.
  returned: always
  type: int
  sample: 107374182400
used:
  description: Used storage in bytes.
  returned: always
  type: int
  sample: 53687091200
avail:
  description: Available storage in bytes.
  returned: always
  type: int
  sample: 53687091200
active:
  description: Whether the storage is active.
  returned: always
  type: bool
  sample: true
enabled:
  description: Whether the storage is enabled.
  returned: always
  type: bool
  sample: true
shared:
  description: Whether the storage is shared.
  returned: always
  type: bool
  sample: false
content:
  description: Content types supported by this storage.
  returned: always
  type: str
  sample: "images,iso,vztmpl"
status:
  description: Full status data from the API.
  returned: always
  type: dict
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        limit=dict(type='int', default=100),
        offset=dict(type='int', default=0),
        max_results=dict(type='int', default=1000),
        node=dict(type='str', required=True),
        storage=dict(type='str', required=True),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    node = params['node']
    storage = params['storage']

    try:
        status = api.nodes(node).storage(storage).status.get()
    except Exception as e:
        module.fail_json(msg="Failed to get storage status for '%s' on node '%s': %s" % (storage, node, str(e)))

    result = dict(
        changed=False,
        storage=storage,
        type=status.get('type', ''),
        total=status.get('total', 0),
        used=status.get('used', 0),
        avail=status.get('avail', 0),
        active=bool(status.get('active', False)),
        enabled=bool(status.get('enabled', True)),
        shared=bool(status.get('shared', False)),
        content=status.get('content', ''),
        status=status,
    )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
