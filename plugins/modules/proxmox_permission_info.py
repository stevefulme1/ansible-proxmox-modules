#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_permission_info
short_description: Query effective permissions in Proxmox VE
description:
  - Retrieve effective permissions for a user or on a specific path.
  - This is an info module and does not modify any state.
version_added: "1.0.0"
author:
  - sfulmer
options:
  userid:
    description:
      - The user ID to query permissions for (e.g. C(user@pam)).
      - If not specified, returns permissions for the authenticated user.
    type: str
  path:
    description:
      - The ACL path to query permissions for (e.g. C(/vms/100)).
      - If not specified, returns permissions for all paths.
    type: str
extends_documentation_fragment:
  - sfulmer.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Get permissions for the current user
  sfulmer.proxmox.proxmox_permission_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  register: permissions

- name: Get permissions for a specific user
  sfulmer.proxmox.proxmox_permission_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    userid: admin@pve
  register: permissions

- name: Get permissions on a specific path
  sfulmer.proxmox.proxmox_permission_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    userid: admin@pve
    path: /vms/100
  register: permissions
'''

RETURN = r'''
permissions:
  description: A map of paths to permission sets.
  type: dict
  returned: always
  sample:
    /vms/100:
      VM.Audit: 1
      VM.Console: 1
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            userid=dict(type='str'),
            path=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    userid = module.params.get('userid')
    path = module.params.get('path')

    params = {}
    if userid:
        params['userid'] = userid
    if path:
        params['path'] = path

    permissions = module.proxmox_request(
        'GET', 'access/permissions', params=params,
    )

    module.exit_json(changed=False, permissions=permissions)


if __name__ == '__main__':
    main()
