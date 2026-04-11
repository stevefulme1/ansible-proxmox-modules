#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_token
short_description: Manage Proxmox Backup Server API tokens
description:
  - Create, update, or remove API tokens for users on a Proxmox Backup Server.
  - Uses the C(/access/users/{userid}/token) API endpoint.
  - When a token is first created, the token secret is returned. This secret
    is only available at creation time and cannot be retrieved later.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  userid:
    description:
      - The user ID that owns the token, in C(user@realm) format.
    type: str
    required: true
  tokenid:
    description: The token name/ID to manage.
    type: str
    required: true
  comment:
    description: Description or comment for the token.
    type: str
  enable:
    description: Whether the token is enabled.
    type: bool
  expire:
    description:
      - Token expiration date as epoch timestamp.
      - Set to C(0) for no expiration.
    type: int
  state:
    description: Whether the token should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create an API token
  sfulmer.proxmox.proxmox_pbs_token:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    userid: backup-admin@pbs
    tokenid: automation
    comment: Automation token for CI/CD
    enable: true
    expire: 0
    state: present
  register: token_result

- name: Show the token secret (only available at creation)
  ansible.builtin.debug:
    var: token_result.token_secret

- name: Remove an API token
  sfulmer.proxmox.proxmox_pbs_token:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    userid: backup-admin@pbs
    tokenid: automation
    state: absent
'''

RETURN = r'''
userid:
  description: The user ID that owns the token.
  returned: always
  type: str
  sample: backup-admin@pbs
tokenid:
  description: The token ID that was managed.
  returned: always
  type: str
  sample: automation
full_tokenid:
  description: The full token identifier in C(user@realm!tokenid) format.
  returned: always
  type: str
  sample: "backup-admin@pbs!automation"
token_secret:
  description:
    - The token secret value. Only returned when the token is first created.
    - This value cannot be retrieved again after creation.
  returned: when token is created
  type: str
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        userid=dict(type='str', required=True),
        tokenid=dict(type='str', required=True),
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
    tokenid = params['tokenid']
    state = params['state']
    full_tokenid = "%s!%s" % (userid, tokenid)

    # Check if token exists
    existing = None
    try:
        existing = api.access.users(userid).token(tokenid).get()
    except Exception:
        existing = None

    changed = False
    result = dict(userid=userid, tokenid=tokenid, full_tokenid=full_tokenid, changed=False)

    config_keys = ['comment', 'enable', 'expire']

    if state == 'absent':
        if existing is not None:
            if not module.check_mode:
                try:
                    api.access.users(userid).token(tokenid).delete()
                except Exception as e:
                    module.fail_json(
                        msg="Failed to delete token '%s' for user '%s': %s" % (tokenid, userid, str(e))
                    )
            changed = True
    else:
        config = {}
        for key in config_keys:
            if params.get(key) is not None:
                value = params[key]
                if isinstance(value, bool):
                    value = int(value)
                config[key] = value

        if existing is None:
            changed = True
            if not module.check_mode:
                try:
                    resp = api.access.users(userid).token(tokenid).post(**config)
                    if isinstance(resp, dict):
                        result['token_secret'] = resp.get('value', '')
                    elif isinstance(resp, str):
                        result['token_secret'] = resp
                except Exception as e:
                    module.fail_json(
                        msg="Failed to create token '%s' for user '%s': %s" % (tokenid, userid, str(e))
                    )
        else:
            update_params = {}
            for key, value in config.items():
                if str(existing.get(key, '')) != str(value):
                    update_params[key] = value
            if update_params:
                if not module.check_mode:
                    try:
                        api.access.users(userid).token(tokenid).put(**update_params)
                    except Exception as e:
                        module.fail_json(
                            msg="Failed to update token '%s' for user '%s': %s" % (tokenid, userid, str(e))
                        )
                changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
