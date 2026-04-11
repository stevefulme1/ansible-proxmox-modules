#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_user
short_description: Manage Proxmox Backup Server users
description:
  - Create, update, or remove users on a Proxmox Backup Server.
  - Uses the C(/access/users) API endpoint.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  userid:
    description:
      - The user ID in C(user@realm) format.
    type: str
    required: true
  password:
    description:
      - Password for the user.
      - Only used when creating or updating a user.
    type: str
    no_log: true
  email:
    description: Email address for the user.
    type: str
  firstname:
    description: First name of the user.
    type: str
  lastname:
    description: Last name of the user.
    type: str
  comment:
    description: Description or comment for the user.
    type: str
  enable:
    description: Whether the user account is enabled.
    type: bool
  expire:
    description:
      - Account expiration date as epoch timestamp.
      - Set to C(0) for no expiration.
    type: int
  state:
    description: Whether the user should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create a PBS user
  sfulmer.proxmox.proxmox_pbs_user:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    userid: backup-admin@pbs
    password: securepassword
    email: admin@example.com
    firstname: Backup
    lastname: Admin
    comment: Backup administration account
    enable: true
    state: present

- name: Disable a PBS user
  sfulmer.proxmox.proxmox_pbs_user:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    userid: backup-admin@pbs
    enable: false
    state: present

- name: Remove a PBS user
  sfulmer.proxmox.proxmox_pbs_user:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    userid: backup-admin@pbs
    state: absent
'''

RETURN = r'''
userid:
  description: The user ID that was managed.
  returned: always
  type: str
  sample: backup-admin@pbs
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        userid=dict(type='str', required=True),
        password=dict(type='str', no_log=True),
        email=dict(type='str'),
        firstname=dict(type='str'),
        lastname=dict(type='str'),
        comment=dict(type='str'),
        enable=dict(type='bool'),
        expire=dict(type='int'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    userid = params['userid']
    state = params['state']

    try:
        users = api.access.users.get()
    except Exception as e:
        module.fail_json(msg="Failed to list users: %s" % str(e))

    existing = None
    for user in users:
        if user.get('userid') == userid:
            existing = user
            break

    changed = False
    result = dict(userid=userid, changed=False)

    config_keys = ['email', 'firstname', 'lastname', 'comment', 'enable', 'expire']

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.access.users(userid).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete user '%s': %s" % (userid, str(e)))
            changed = True
    else:
        config = {}
        for key in config_keys:
            if params.get(key) is not None:
                value = params[key]
                if isinstance(value, bool):
                    value = int(value)
                config[key] = value

        if existing:
            update_params = {}
            for key, value in config.items():
                if str(existing.get(key, '')) != str(value):
                    update_params[key] = value
            # Password is always included in update if provided (cannot compare)
            if params.get('password'):
                update_params['password'] = params['password']
                changed = True
            if update_params:
                if not module.check_mode:
                    try:
                        api.access.users(userid).put(**update_params)
                    except Exception as e:
                        module.fail_json(msg="Failed to update user '%s': %s" % (userid, str(e)))
                changed = True
        else:
            config['userid'] = userid
            if params.get('password'):
                config['password'] = params['password']
            if not module.check_mode:
                try:
                    api.access.users.post(**config)
                except Exception as e:
                    module.fail_json(msg="Failed to create user '%s': %s" % (userid, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
