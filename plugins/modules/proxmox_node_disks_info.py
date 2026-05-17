#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_disks_info
short_description: Query physical disk information on Proxmox VE nodes
version_added: "1.0.0"
description:
  - Retrieve information about physical disks on a Proxmox VE node
    via the C(/nodes/{node}/disks/list) API endpoint.
  - This is an info module and does not make any changes.
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
  type:
    description:
      - Filter disks by type (e.g. C(ssd), C(hdd), C(nvme)).
    type: str
author:
  - sfulmer
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
- name: List all physical disks on a node
  stevefulme1.proxmox.proxmox_node_disks_info:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
  register: disk_info

- name: List only SSD disks
  stevefulme1.proxmox.proxmox_node_disks_info:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    type: ssd
  register: ssd_info
'''

RETURN = r'''
disks:
  description: List of physical disk information dictionaries.
  returned: success
  type: list
  elements: dict
  sample:
    - devpath: "/dev/sda"
      model: "Samsung SSD 860"
      serial: "S3YBNX0K123456"
      size: 500107862016
      type: "ssd"
      health: "PASSED"
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    argument_spec = dict(
        limit=dict(type='int', default=100),
        offset=dict(type='int', default=0),
        max_results=dict(type='int', default=1000),
        node=dict(type='str', required=True),
        type=dict(type='str'),
    )

    proxmox = ProxmoxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module = proxmox.module
    params = module.params
    node = params['node']

    api = proxmox.get_api()

    try:
        get_params = {}
        if params.get('type'):
            get_params['type'] = params['type']
        disks = api.nodes(node).disks.list.get(**get_params)
    except Exception as e:
        module.fail_json(
            msg="Failed to query disks on node '%s': %s" % (node, str(e)))

    module.exit_json(changed=False, disks=disks)


if __name__ == '__main__':
    main()
