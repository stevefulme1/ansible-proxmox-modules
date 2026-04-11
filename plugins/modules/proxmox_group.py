# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_group
short_description: Manage access groups in Proxmox VE
version_added: "0.1.0"
description:
  - Create, update, or remove access groups in Proxmox VE via the C(/access/groups) API endpoint.
  - Group membership is managed through the M(proxmox_user) module's C(groups) parameter.
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
  groupid:
    description: The group name/ID.
    type: str
    required: true
  comment:
    description: Description/comment for the group.
    type: str
  state:
    description: Whether the group should be present or absent.
    type: str
    choices: ['present', 'absent']
    default: present
notes:
  - Group members are managed through the M(proxmox_user) module's C(groups) parameter.
author:
  - "Proxmox Community (@proxmox-community)"
'''

EXAMPLES = r'''
- name: Create an admin group
  proxmox_group:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    groupid: admins
    comment: "Cluster administrators"
    state: present

- name: Remove a group
  proxmox_group:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    groupid: oldgroup
    state: absent
'''

RETURN = r'''
groupid:
  description: The group ID that was managed.
  returned: success
  type: str
  sample: "admins"
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


def get_group(proxmox, groupid):
    """Return group config dict or None if group does not exist."""
    try:
        return proxmox.access.groups(groupid).get()
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
        groupid=dict(type='str', required=True),
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
    groupid = params['groupid']

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

    existing = get_group(proxmox, groupid)
    changed = False
    result = dict(groupid=groupid)

    if state == 'absent':
        if existing is not None:
            changed = True
            if not module.check_mode:
                try:
                    proxmox.access.groups(groupid).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete group '%s': %s" % (groupid, str(e)))
        module.exit_json(changed=changed, **result)

    # state == present
    if existing is None:
        changed = True
        if not module.check_mode:
            create_params = dict(groupid=groupid)
            if params.get('comment') is not None:
                create_params['comment'] = params['comment']
            try:
                proxmox.access.groups.post(**create_params)
            except Exception as e:
                module.fail_json(msg="Failed to create group '%s': %s" % (groupid, str(e)))
    else:
        update_params = {}
        if params.get('comment') is not None:
            if existing.get('comment', '') != params['comment']:
                update_params['comment'] = params['comment']
        if update_params:
            changed = True
            if not module.check_mode:
                try:
                    proxmox.access.groups(groupid).put(**update_params)
                except Exception as e:
                    module.fail_json(msg="Failed to update group '%s': %s" % (groupid, str(e)))

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
