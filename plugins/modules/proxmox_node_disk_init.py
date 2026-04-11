#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_disk_init
short_description: Initialize or wipe disks with GPT on Proxmox VE nodes
version_added: "1.0.0"
description:
  - Initialize a disk with a GPT partition table on a Proxmox VE node
    via the C(/nodes/{node}/disks/initgpt) API endpoint.
  - This is a destructive action module. It always reports C(changed=True).
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
  disk:
    description:
      - The device path of the disk to initialize (e.g. C(/dev/sdb)).
    type: str
    required: true
  uuid:
    description:
      - UUID to use for the GPT disk label. Auto-generated if omitted.
    type: str
author:
  - sfulmer
'''

EXAMPLES = r'''
- name: Initialize /dev/sdb with GPT
  sfulmer.proxmox.proxmox_node_disk_init:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    disk: /dev/sdb

- name: Initialize disk with specific UUID
  sfulmer.proxmox.proxmox_node_disk_init:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    disk: /dev/sdc
    uuid: "12345678-1234-1234-1234-123456789abc"
'''

RETURN = r'''
disk:
  description: The device path that was initialized.
  returned: success
  type: str
  sample: "/dev/sdb"
upid:
  description: The task UPID returned by the API.
  returned: success, not check_mode
  type: str
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    argument_spec = dict(
        node=dict(type='str', required=True),
        disk=dict(type='str', required=True),
        uuid=dict(type='str'),
    )

    proxmox = ProxmoxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module = proxmox.module
    params = module.params
    node = params['node']
    disk = params['disk']

    api = proxmox.get_api()
    result = dict(disk=disk)

    # Action module: always changed
    changed = True
    if not module.check_mode:
        post_params = dict(disk=disk)
        if params.get('uuid'):
            post_params['uuid'] = params['uuid']
        try:
            upid = api.nodes(node).disks.initgpt.post(**post_params)
            result['upid'] = upid
        except Exception as e:
            module.fail_json(
                msg="Failed to initialize disk '%s' on node '%s': %s"
                % (disk, node, str(e)))

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
