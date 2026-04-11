# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_role
short_description: Manage access roles in Proxmox VE
version_added: "0.1.0"
description:
  - Create, update, or remove access roles in Proxmox VE via the C(/access/roles) API endpoint.
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
  roleid:
    description: The role name/ID.
    type: str
    required: true
  privs:
    description:
      - Comma-separated string of privileges for the role.
      - "Example: C(VM.Audit,VM.Console,VM.PowerMgmt)."
    type: str
  append:
    description:
      - If C(true), append the specified privileges to the existing set instead of replacing them.
    type: bool
    default: false
  state:
    description: Whether the role should be present or absent.
    type: str
    choices: ['present', 'absent']
    default: present
author:
  - "Proxmox Community (@proxmox-community)"
'''

EXAMPLES = r'''
- name: Create a custom VM operator role
  proxmox_role:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    roleid: VMOperator
    privs: "VM.Audit,VM.Console,VM.PowerMgmt,VM.Monitor"
    state: present

- name: Append privileges to an existing role
  proxmox_role:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    roleid: VMOperator
    privs: "VM.Snapshot,VM.Snapshot.Rollback"
    append: true
    state: present

- name: Remove a role
  proxmox_role:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    roleid: VMOperator
    state: absent
'''

RETURN = r'''
roleid:
  description: The role ID that was managed.
  returned: success
  type: str
  sample: "VMOperator"
privs:
  description: The final set of privileges assigned to the role.
  returned: when state is present
  type: str
  sample: "VM.Audit,VM.Console,VM.PowerMgmt"
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


def get_role(proxmox, roleid):
    """Return role privilege dict or None if role does not exist."""
    try:
        return proxmox.access.roles(roleid).get()
    except Exception:
        return None


def normalize_privs(privs_input):
    """Return a sorted set of privilege strings from a comma-separated string or dict."""
    if isinstance(privs_input, dict):
        return set(privs_input.keys())
    if isinstance(privs_input, str):
        return set(p.strip() for p in privs_input.split(',') if p.strip())
    return set()


def main():
    argument_spec = dict(
        api_host=dict(type='str', required=True),
        api_user=dict(type='str', required=True),
        api_password=dict(type='str', no_log=True),
        api_token_id=dict(type='str'),
        api_token_secret=dict(type='str', no_log=True),
        validate_certs=dict(type='bool', default=True),
        roleid=dict(type='str', required=True),
        privs=dict(type='str'),
        append=dict(type='bool', default=False),
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
    roleid = params['roleid']

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

    existing = get_role(proxmox, roleid)
    changed = False
    result = dict(roleid=roleid)

    if state == 'absent':
        if existing is not None:
            changed = True
            if not module.check_mode:
                try:
                    proxmox.access.roles(roleid).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete role '%s': %s" % (roleid, str(e)))
        module.exit_json(changed=changed, **result)

    # state == present
    desired_privs = normalize_privs(params.get('privs', ''))

    if existing is None:
        changed = True
        if not module.check_mode:
            create_params = dict(roleid=roleid)
            if desired_privs:
                create_params['privs'] = ','.join(sorted(desired_privs))
            try:
                proxmox.access.roles.post(**create_params)
            except Exception as e:
                module.fail_json(msg="Failed to create role '%s': %s" % (roleid, str(e)))
        result['privs'] = ','.join(sorted(desired_privs))
    else:
        current_privs = normalize_privs(existing)

        if params['append']:
            final_privs = current_privs | desired_privs
        else:
            final_privs = desired_privs

        if current_privs != final_privs:
            changed = True
            if not module.check_mode:
                update_params = dict(privs=','.join(sorted(final_privs)))
                if params['append']:
                    update_params['append'] = 1
                try:
                    proxmox.access.roles(roleid).put(**update_params)
                except Exception as e:
                    module.fail_json(msg="Failed to update role '%s': %s" % (roleid, str(e)))

        result['privs'] = ','.join(sorted(final_privs))

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
