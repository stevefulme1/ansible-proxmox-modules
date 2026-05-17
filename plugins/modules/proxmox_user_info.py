#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_user_info
short_description: List users on Proxmox VE
version_added: "1.1.0"
description:
  - Retrieve the list of users configured on Proxmox VE, or details for a specific user.
  - Returns userid, email, firstname, lastname, enable, groups, and tokens.
  - This is an info module and does not make any changes.
author:
  - sfulmer
options:
  userid:
    description:
      - A specific user ID to query (e.g. C(admin@pve)).
      - When omitted, all users are returned.
    type: str
  limit:
    description:
      - Maximum number of results to return.
      - Applied client-side to truncate results.
    type: int
    default: 100
  offset:
    description:
      - Number of results to skip before returning.
      - Applied client-side for pagination.
    type: int
    default: 0
  max_results:
    description:
      - Maximum total number of results to return.
      - Set to 0 for no limit.
    type: int
    default: 1000
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: List all users
  stevefulme1.proxmox.proxmox_user_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
  register: users

- name: Get a specific user
  stevefulme1.proxmox.proxmox_user_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    userid: admin@pve
  register: user

- name: Display users
  ansible.builtin.debug:
    var: users.resources
'''

RETURN = r'''
resources:
  description: List of users (or a single-element list when userid is specified).
  returned: always
  type: list
  elements: dict
  sample:
    - userid: "root@pam"
      email: "admin@example.com"
      firstname: "Root"
      lastname: "Admin"
      enable: 1
      groups: ""
      tokens: []
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            limit=dict(type='int', default=100),
            offset=dict(type='int', default=0),
            max_results=dict(type='int', default=1000),
            userid=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    userid = module.params['userid']

    proxmox = module.proxmox_api()

    try:
        if userid:
            user = proxmox.access.users(userid).get()
            resources = [user]
        else:
            resources = proxmox.access.users.get()
    except Exception as e:
        module.fail_json(
            msg="Failed to list users: {0}".format(str(e))
        )

    # Apply client-side pagination
    _offset = module.params.get("offset") or 0
    _limit = module.params.get("limit") or 100
    if isinstance(resources, list):
        resources = resources[_offset:_offset + _limit]
    module.exit_json(changed=False, resources=resources)


if __name__ == '__main__':
    main()
