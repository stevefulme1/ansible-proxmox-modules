#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_acl
short_description: Manage ACL entries in Proxmox VE
description:
  - Create and remove Access Control List entries in Proxmox VE.
  - Assigns roles to users, groups, or API tokens on specific paths.
version_added: "1.0.0"
author:
  - sfulmer
options:
  path:
    description:
      - The ACL path (e.g. C(/vms/100), C(/storage/local), C(/)).
    type: str
    required: true
  roles:
    description:
      - List of roles to assign.
    type: list
    elements: str
    required: true
  users:
    description:
      - List of users to assign the roles to (e.g. C(user@pam)).
    type: list
    elements: str
  groups:
    description:
      - List of groups to assign the roles to.
    type: list
    elements: str
  tokens:
    description:
      - List of API tokens to assign the roles to (e.g. C(user@pam!token)).
    type: list
    elements: str
  propagate:
    description:
      - Whether to propagate permissions to child objects.
    type: bool
    default: true
  state:
    description:
      - Whether the ACL entry should be present or absent.
    type: str
    default: present
    choices:
      - present
      - absent
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Grant PVEAdmin role to a user on a VM
  stevefulme1.proxmox.proxmox_acl:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    path: /vms/100
    roles:
      - PVEAdmin
    users:
      - admin@pve
    state: present

- name: Grant multiple roles to a group
  stevefulme1.proxmox.proxmox_acl:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    path: /
    roles:
      - PVEAuditor
      - PVEPoolUser
    groups:
      - developers
    propagate: true
    state: present

- name: Remove ACL entry
  stevefulme1.proxmox.proxmox_acl:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    path: /vms/100
    roles:
      - PVEAdmin
    users:
      - admin@pve
    state: absent
'''

RETURN = r'''
path:
  description: The ACL path that was managed.
  type: str
  returned: always
  sample: /vms/100
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "ACL entry updated successfully."
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


def _get_current_acls(module):
    """Retrieve all current ACL entries."""
    return module.proxmox_request('GET', 'access/acl')


def _acl_exists(acls, path, role, subject_type, subject):
    """Check if a specific ACL entry already exists."""
    for acl in acls:
        if acl.get('path') == path and acl.get('roleid') == role and acl.get(subject_type) == subject:
            return True
    return False


def _apply_acl(module, path, roles, subjects, propagate, delete=False):
    """Apply or remove ACL entries for a set of subjects."""
    for role in roles:
        for subject_type, subject_list in subjects.items():
            if not subject_list:
                continue
            for subject in subject_list:
                data = {
                    'path': path,
                    'roles': role,
                    subject_type: subject,
                    'propagate': int(propagate),
                }
                if delete:
                    data['delete'] = 1
                module.proxmox_request('PUT', 'access/acl', data=data)


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            path=dict(type='str', required=True),
            roles=dict(type='list', elements='str', required=True),
            users=dict(type='list', elements='str'),
            groups=dict(type='list', elements='str'),
            tokens=dict(type='list', elements='str'),
            propagate=dict(type='bool', default=True),
            state=dict(
                type='str', default='present',
                choices=['present', 'absent'],
            ),
        ),
        required_one_of=[['users', 'groups', 'tokens']],
        supports_check_mode=True,
    )

    path = module.params['path']
    roles = module.params['roles']
    users = module.params.get('users') or []
    groups = module.params.get('groups') or []
    tokens = module.params.get('tokens') or []
    propagate = module.params['propagate']
    state = module.params['state']

    subjects = {
        'users': users,
        'groups': groups,
        'tokens': tokens,
    }

    # Map subject types to ACL response field names for lookup
    subject_acl_field = {
        'users': 'ugid',
        'groups': 'ugid',
        'tokens': 'ugid',
    }

    current_acls = _get_current_acls(module)
    changed = False

    if state == 'present':
        for role in roles:
            for subject_type, subject_list in subjects.items():
                for subject in subject_list:
                    field = subject_acl_field[subject_type]
                    if not _acl_exists(current_acls, path, role, field, subject):
                        changed = True

        if changed and not module.check_mode:
            _apply_acl(module, path, roles, subjects, propagate, delete=False)

        msg = "ACL entry updated successfully." if changed else "ACL entry already up to date."

    elif state == 'absent':
        for role in roles:
            for subject_type, subject_list in subjects.items():
                for subject in subject_list:
                    field = subject_acl_field[subject_type]
                    if _acl_exists(current_acls, path, role, field, subject):
                        changed = True

        if changed and not module.check_mode:
            _apply_acl(module, path, roles, subjects, propagate, delete=True)

        msg = "ACL entry removed successfully." if changed else "ACL entry does not exist."

    module.exit_json(changed=changed, path=path, msg=msg)


if __name__ == '__main__':
    main()
