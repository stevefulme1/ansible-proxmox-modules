#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_acl
short_description: Manage Proxmox Backup Server access control lists
description:
  - Add or remove ACL entries on a Proxmox Backup Server.
  - Uses the C(/access/acl) API endpoint with PUT for both add and remove operations.
  - To remove an ACL entry, the module sends a PUT with C(delete=1).
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  path:
    description:
      - The ACL path (e.g. C(/datastore/backups) or C(/)).
    type: str
    required: true
  role:
    description: The role to assign or remove.
    type: str
    required: true
  auth_id:
    description:
      - The authentication entity (user or API token) in C(user@realm) or C(user@realm!token) format.
    type: str
    required: true
  propagate:
    description: Whether the ACL should propagate to child objects.
    type: bool
    default: true
  state:
    description: Whether the ACL entry should be present or absent.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Grant DatastoreAdmin role on a datastore
  sfulmer.proxmox.proxmox_pbs_acl:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    path: /datastore/backups
    role: DatastoreAdmin
    auth_id: backup-admin@pbs
    propagate: true
    state: present

- name: Grant token access to a datastore
  sfulmer.proxmox.proxmox_pbs_acl:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    path: /datastore/backups
    role: DatastoreBackup
    auth_id: backup-admin@pbs!automation
    state: present

- name: Remove an ACL entry
  sfulmer.proxmox.proxmox_pbs_acl:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    path: /datastore/backups
    role: DatastoreAdmin
    auth_id: backup-admin@pbs
    state: absent
'''

RETURN = r'''
path:
  description: The ACL path that was managed.
  returned: always
  type: str
  sample: /datastore/backups
role:
  description: The role that was assigned or removed.
  returned: always
  type: str
  sample: DatastoreAdmin
auth_id:
  description: The authentication entity the ACL applies to.
  returned: always
  type: str
  sample: backup-admin@pbs
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        path=dict(type='str', required=True),
        role=dict(type='str', required=True),
        auth_id=dict(type='str', required=True),
        propagate=dict(type='bool', default=True),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    acl_path = params['path']
    role = params['role']
    auth_id = params['auth_id']
    propagate = params['propagate']
    state = params['state']

    # Check existing ACLs
    try:
        acls = api.access.acl.get()
    except Exception as e:
        module.fail_json(msg="Failed to list ACLs: %s" % str(e))

    existing = None
    for acl in acls:
        acl_ugid = acl.get('ugid', '')
        if (acl.get('path') == acl_path and acl.get('roleid') == role and acl_ugid == auth_id):
            existing = acl
            break

    changed = False
    result = dict(path=acl_path, role=role, auth_id=auth_id, changed=False)

    # Determine the auth_id key: token uses 'auth-id', user-only might too in PBS
    auth_param = 'auth-id'

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.access.acl.put(
                        path=acl_path,
                        role=role,
                        **{auth_param: auth_id, 'delete': 1}
                    )
                except Exception as e:
                    module.fail_json(msg="Failed to remove ACL entry: %s" % str(e))
            changed = True
    else:
        if existing:
            # Check if propagate differs
            current_propagate = bool(existing.get('propagate', 1))
            if current_propagate != propagate:
                if not module.check_mode:
                    try:
                        api.access.acl.put(
                            path=acl_path,
                            role=role,
                            propagate=int(propagate),
                            **{auth_param: auth_id}
                        )
                    except Exception as e:
                        module.fail_json(msg="Failed to update ACL entry: %s" % str(e))
                changed = True
        else:
            if not module.check_mode:
                try:
                    api.access.acl.put(
                        path=acl_path,
                        role=role,
                        propagate=int(propagate),
                        **{auth_param: auth_id}
                    )
                except Exception as e:
                    module.fail_json(msg="Failed to create ACL entry: %s" % str(e))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
