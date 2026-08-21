# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_user
short_description: Manage users in Proxmox VE
version_added: "0.1.0"
description:
  - Create, update, or remove users in Proxmox VE via the C(/access/users) API endpoint.
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
  userid:
    description:
      - The user ID in the format C(user@realm), e.g. C(admin@pve).
    type: str
    required: true
  password:
    description:
      - Password for the user.
      - Only used when creating or updating PAM/PVE realm users.
    type: str
  groups:
    description: List of groups the user should belong to.
    type: list
    elements: str
  email:
    description: Email address of the user.
    type: str
  firstname:
    description: First name of the user.
    type: str
  lastname:
    description: Last name of the user.
    type: str
  comment:
    description: Description/comment for the user.
    type: str
  enable:
    description: Whether the user account is enabled.
    type: bool
    default: true
  expire:
    description:
      - Account expiration date as epoch timestamp.
      - Set to C(0) for no expiration.
    type: int
  state:
    description: Whether the user should be present or absent.
    type: str
    choices: ['present', 'absent']
    default: present
author:
  - "Proxmox Community (@proxmox-community)"
'''

EXAMPLES = r'''
- name: Create a PVE user
  proxmox_user:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    userid: admin@pve
    password: userpassword
    groups:
      - admins
    email: admin@example.com
    firstname: Admin
    lastname: User
    state: present

- name: Remove a user
  proxmox_user:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    userid: olduser@pve
    state: absent
'''

RETURN = r'''
userid:
  description: The user ID that was managed.
  returned: success
  type: str
  sample: "admin@pve"
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


def get_user(proxmox, userid):
    """Return user config dict or None if user does not exist."""
    try:
        return proxmox.access.users(userid).get()
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
        password=dict(type='str', no_log=True),
        groups=dict(type='list', elements='str'),
        email=dict(type='str'),
        firstname=dict(type='str'),
        lastname=dict(type='str'),
        comment=dict(type='str'),
        enable=dict(type='bool', default=True),
        expire=dict(type='int'),
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

    existing = get_user(proxmox, userid)
    changed = False
    result = dict(userid=userid)

    if state == 'absent':
        if existing is not None:
            changed = True
            if not module.check_mode:
                try:
                    proxmox.access.users(userid).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete user '%s': %s" % (userid, str(e)))
        module.exit_json(changed=changed, **result)

    # state == present
    desired = dict(enable=1 if params['enable'] else 0)

    if params.get('groups') is not None:
        desired['groups'] = ','.join(params['groups'])
    if params.get('email') is not None:
        desired['email'] = params['email']
    if params.get('firstname') is not None:
        desired['firstname'] = params['firstname']
    if params.get('lastname') is not None:
        desired['lastname'] = params['lastname']
    if params.get('comment') is not None:
        desired['comment'] = params['comment']
    if params.get('expire') is not None:
        desired['expire'] = params['expire']

    if existing is None:
        changed = True
        if not module.check_mode:
            create_params = dict(userid=userid)
            create_params.update(desired)
            if params.get('password'):
                create_params['password'] = params['password']
            try:
                proxmox.access.users.post(**create_params)
            except Exception as e:
                module.fail_json(msg="Failed to create user '%s': %s" % (userid, str(e)))
    else:
        update_params = {}
        for key, value in desired.items():
            current_val = existing.get(key, '')
            # Normalize comparison for groups (API may return as list or comma-separated)
            if key == 'groups':
                existing_groups = existing.get('groups', '')
                if isinstance(existing_groups, list):
                    existing_groups = ','.join(sorted(existing_groups))
                desired_groups = ','.join(sorted(value.split(','))) if value else ''
                if existing_groups != desired_groups:
                    update_params[key] = value
            elif str(current_val) != str(value):
                update_params[key] = value

        # Password changes always trigger an update (we cannot compare)
        if params.get('password'):
            update_params['password'] = params['password']
            changed = True

        if update_params:
            changed = True
            if not module.check_mode:
                try:
                    proxmox.access.users(userid).put(**update_params)
                except Exception as e:
                    module.fail_json(msg="Failed to update user '%s': %s" % (userid, str(e)))

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
