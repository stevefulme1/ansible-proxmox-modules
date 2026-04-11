# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_token
short_description: Manage API tokens for users in Proxmox VE
version_added: "0.1.0"
description:
  - Create, update, or remove API tokens for Proxmox VE users via
    the C(/access/users/{userid}/token/{tokenid}) API endpoint.
  - When a token is first created, the token secret is returned. This secret
    is only available at creation time and cannot be retrieved later.
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
    description: API token ID for authentication.
    type: str
  api_token_secret:
    description: API token secret for authentication.
    type: str
  validate_certs:
    description: Whether to validate SSL certificates.
    type: bool
    default: true
  userid:
    description:
      - The user ID that owns the token, in the format C(user@realm).
    type: str
    required: true
  tokenid:
    description: The token name/ID to manage.
    type: str
    required: true
  privsep:
    description:
      - Whether the token has separate privileges from the user.
      - When C(true), the token requires its own ACL entries.
      - When C(false), the token inherits the user's privileges.
    type: bool
    default: true
  expire:
    description:
      - Token expiration date as epoch timestamp.
      - Set to C(0) for no expiration.
    type: int
  comment:
    description: Description/comment for the token.
    type: str
  state:
    description: Whether the token should be present or absent.
    type: str
    choices: ['present', 'absent']
    default: present
author:
  - "Proxmox Community (@proxmox-community)"
'''

EXAMPLES = r'''
- name: Create an API token for automation
  proxmox_token:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    userid: automation@pve
    tokenid: ci-token
    privsep: false
    expire: 0
    comment: "CI/CD automation token"
    state: present
  register: token_result

- name: Show the token secret (only available at creation time)
  ansible.builtin.debug:
    var: token_result.token_secret

- name: Remove an API token
  proxmox_token:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    userid: automation@pve
    tokenid: ci-token
    state: absent
'''

RETURN = r'''
userid:
  description: The user ID that owns the token.
  returned: success
  type: str
  sample: "automation@pve"
tokenid:
  description: The token ID that was managed.
  returned: success
  type: str
  sample: "ci-token"
full_tokenid:
  description: The full token identifier in the format C(user@realm!tokenid).
  returned: success
  type: str
  sample: "automation@pve!ci-token"
token_secret:
  description:
    - The token secret value. Only returned when the token is first created.
    - This value cannot be retrieved again after creation.
  returned: when token is created
  type: str
  sample: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


def get_token(proxmox, userid, tokenid):
    """Return token config dict or None if token does not exist."""
    try:
        return proxmox.access.users(userid).token(tokenid).get()
    except Exception:
        return None


def main():
    argument_spec = dict(
        api_host=dict(type='str', required=True),
        api_user=dict(type='str', required=True),
        api_password=dict(type='str', no_log=True),
        api_token_id=dict(type='str'),
        api_token_secret=dict(type='str', no_log=True),
        validate_certs=dict(type='bool', default=True),
        userid=dict(type='str', required=True),
        tokenid=dict(type='str', required=True),
        privsep=dict(type='bool', default=True),
        expire=dict(type='int'),
        comment=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['api_password', 'api_token_id']],
        required_together=[['api_token_id', 'api_token_secret']],
    )

    if not HAS_PROXMOXER:
        module.fail_json(msg="proxmoxer library is required. Install it with: pip install proxmoxer")

    params = module.params
    state = params['state']
    userid = params['userid']
    tokenid = params['tokenid']
    full_tokenid = "%s!%s" % (userid, tokenid)

    auth_args = dict(
        host=params['api_host'],
        user=params['api_user'],
        verify_ssl=params['validate_certs'],
    )
    if params.get('api_token_id') and params.get('api_token_secret'):
        auth_args['token_name'] = params['api_token_id']
        auth_args['token_value'] = params['api_token_secret']
    elif params.get('api_password'):
        auth_args['password'] = params['api_password']

    try:
        proxmox = ProxmoxAPI(**auth_args)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Proxmox API: %s" % str(e))

    existing = get_token(proxmox, userid, tokenid)
    changed = False
    result = dict(userid=userid, tokenid=tokenid, full_tokenid=full_tokenid)

    if state == 'absent':
        if existing is not None:
            changed = True
            if not module.check_mode:
                try:
                    proxmox.access.users(userid).token(tokenid).delete()
                except Exception as e:
                    module.fail_json(
                        msg="Failed to delete token '%s' for user '%s': %s" % (tokenid, userid, str(e))
                    )
        module.exit_json(changed=changed, **result)

    # state == present
    desired = dict(privsep=1 if params['privsep'] else 0)
    if params.get('expire') is not None:
        desired['expire'] = params['expire']
    if params.get('comment') is not None:
        desired['comment'] = params['comment']

    if existing is None:
        changed = True
        if not module.check_mode:
            try:
                resp = proxmox.access.users(userid).token(tokenid).post(**desired)
                # The API returns the token secret info on creation
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
        for key, value in desired.items():
            if str(existing.get(key, '')) != str(value):
                update_params[key] = value
        if update_params:
            changed = True
            if not module.check_mode:
                try:
                    proxmox.access.users(userid).token(tokenid).put(**update_params)
                except Exception as e:
                    module.fail_json(
                        msg="Failed to update token '%s' for user '%s': %s" % (tokenid, userid, str(e))
                    )

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
