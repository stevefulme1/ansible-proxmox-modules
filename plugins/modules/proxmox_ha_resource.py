# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_ha_resource
short_description: Manage HA resources in Proxmox VE
version_added: "0.1.0"
description:
  - Create, update, or remove High Availability resources in a Proxmox VE cluster.
  - A resource is identified by its service ID (sid), e.g. C(vm:100) or C(ct:200).
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
  sid:
    description:
      - The service ID of the HA resource.
      - Format is C(type:id), for example C(vm:100) or C(ct:200).
    type: str
    required: true
  state:
    description: Whether the HA resource should be present or absent.
    type: str
    choices: ['present', 'absent']
    default: present
  ha_state:
    description: Requested HA state of the resource.
    type: str
    choices: ['started', 'stopped', 'ignored', 'disabled']
    default: started
  group:
    description: The HA group for this resource.
    type: str
  max_restart:
    description: Maximum number of restart attempts.
    type: int
    default: 1
  max_relocate:
    description: Maximum number of relocate attempts.
    type: int
    default: 1
  comment:
    description: Description/comment for the HA resource.
    type: str
author:
  - "Proxmox Community (@proxmox-community)"
'''

EXAMPLES = r'''
- name: Add VM 100 as HA resource
  proxmox_ha_resource:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    sid: "vm:100"
    ha_state: started
    max_restart: 3
    max_relocate: 2
    state: present

- name: Remove HA resource for CT 200
  proxmox_ha_resource:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    sid: "ct:200"
    state: absent
'''

RETURN = r'''
sid:
  description: The service ID of the HA resource.
  returned: success
  type: str
  sample: "vm:100"
ha_state:
  description: The requested HA state of the resource.
  returned: success
  type: str
  sample: "started"
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


def get_ha_resource(proxmox, sid):
    """Return the HA resource dict for the given sid, or None if not found."""
    try:
        return proxmox.cluster.ha.resources(sid).get()
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
        sid=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        ha_state=dict(type='str', default='started', choices=['started', 'stopped', 'ignored', 'disabled']),
        group=dict(type='str'),
        max_restart=dict(type='int', default=1),
        max_relocate=dict(type='int', default=1),
        comment=dict(type='str'),
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
    sid = params['sid']

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

    existing = get_ha_resource(proxmox, sid)
    changed = False
    result = dict(sid=sid)

    if state == 'absent':
        if existing is not None:
            changed = True
            if not module.check_mode:
                try:
                    proxmox.cluster.ha.resources(sid).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete HA resource '%s': %s" % (sid, str(e)))
        module.exit_json(changed=changed, **result)

    # state == present
    desired = dict(
        state=params['ha_state'],
        max_restart=params['max_restart'],
        max_relocate=params['max_relocate'],
    )
    if params.get('group') is not None:
        desired['group'] = params['group']
    if params.get('comment') is not None:
        desired['comment'] = params['comment']

    if existing is None:
        changed = True
        if not module.check_mode:
            create_params = dict(sid=sid)
            create_params.update(desired)
            try:
                proxmox.cluster.ha.resources.post(**create_params)
            except Exception as e:
                module.fail_json(msg="Failed to create HA resource '%s': %s" % (sid, str(e)))
    else:
        update_params = {}
        for key, value in desired.items():
            if str(existing.get(key, '')) != str(value):
                update_params[key] = value
        if update_params:
            changed = True
            if not module.check_mode:
                try:
                    proxmox.cluster.ha.resources(sid).put(**update_params)
                except Exception as e:
                    module.fail_json(msg="Failed to update HA resource '%s': %s" % (sid, str(e)))

    result['ha_state'] = params['ha_state']
    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
