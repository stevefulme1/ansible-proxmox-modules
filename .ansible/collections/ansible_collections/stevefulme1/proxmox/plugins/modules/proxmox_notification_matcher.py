# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_notification_matcher
short_description: Manage notification matchers in Proxmox VE
version_added: "0.1.0"
description:
  - Create, update, or remove notification matchers in Proxmox VE.
  - Matchers route notifications to endpoints based on severity, field matching,
    and other criteria.
  - Uses the C(/cluster/notifications/matchers) API endpoint.
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
  name:
    description: Unique name for the notification matcher.
    type: str
    required: true
  match_severity:
    description:
      - List of severity levels to match.
      - Notifications matching any of these severities will be routed to the targets.
    type: list
    elements: str
    choices: ['info', 'notice', 'warning', 'error']
  match_field:
    description:
      - List of field match expressions.
      - "Each entry must be in the format C(exact:fieldname=value) or C(regex:fieldname=pattern)."
    type: list
    elements: str
  target:
    description:
      - List of notification endpoint names to route matched notifications to.
    type: list
    elements: str
  comment:
    description: Description/comment for the matcher.
    type: str
  mode:
    description:
      - How to combine multiple match conditions.
      - C(all) requires all conditions to match, C(any) requires at least one.
    type: str
    choices: ['all', 'any']
  invert_match:
    description:
      - If C(true), invert the result of the match conditions.
      - Notifications that do NOT match will be routed to the targets.
    type: bool
  state:
    description: Whether the notification matcher should be present or absent.
    type: str
    choices: ['present', 'absent']
    default: present
author:
  - "Proxmox Community (@proxmox-community)"
'''

EXAMPLES = r'''
- name: Create a matcher for error notifications
  proxmox_notification_matcher:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    name: errors-to-admin
    match_severity:
      - error
      - warning
    target:
      - admin-mail
    mode: any
    state: present

- name: Create a matcher with field matching
  proxmox_notification_matcher:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    name: backup-failures
    match_field:
      - "exact:type=vzdump"
    match_severity:
      - error
    target:
      - admin-mail
      - slack-webhook
    mode: all
    state: present

- name: Remove a notification matcher
  proxmox_notification_matcher:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    name: old-matcher
    state: absent
'''

RETURN = r'''
name:
  description: The name of the notification matcher.
  returned: success
  type: str
  sample: "errors-to-admin"
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False

# API parameter name mapping
PARAM_TO_API = {
    'match_severity': 'match-severity',
    'match_field': 'match-field',
    'invert_match': 'invert-match',
}


def get_matcher(proxmox, name):
    """Return matcher config dict or None if not found."""
    try:
        matchers = proxmox.cluster.notifications.matchers.get()
        for matcher in matchers:
            if matcher.get('name') == name:
                return matcher
    except Exception:
        pass
    return None


def build_api_params(params):
    """Build API parameter dict from module params."""
    api_params = {}

    if params.get('match_severity') is not None:
        api_params['match-severity'] = ','.join(params['match_severity'])

    if params.get('match_field') is not None:
        api_params['match-field'] = ','.join(params['match_field'])

    if params.get('target') is not None:
        api_params['target'] = ','.join(params['target'])

    if params.get('comment') is not None:
        api_params['comment'] = params['comment']

    if params.get('mode') is not None:
        api_params['mode'] = params['mode']

    if params.get('invert_match') is not None:
        api_params['invert-match'] = 1 if params['invert_match'] else 0

    return api_params


def main():
    argument_spec = dict(
        api_host=dict(type='str', required=True),
        api_user=dict(type='str', required=True),
        api_password=dict(type='str', no_log=True),
        api_token_id=dict(type='str'),
        api_token_secret=dict(type='str', no_log=True),
        validate_certs=dict(type='bool', default=True),
        name=dict(type='str', required=True),
        match_severity=dict(type='list', elements='str', choices=['info', 'notice', 'warning', 'error']),
        match_field=dict(type='list', elements='str'),
        target=dict(type='list', elements='str'),
        comment=dict(type='str'),
        mode=dict(type='str', choices=['all', 'any']),
        invert_match=dict(type='bool'),
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
    name = params['name']

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

    existing = get_matcher(proxmox, name)
    changed = False
    result = dict(name=name)

    if state == 'absent':
        if existing is not None:
            changed = True
            if not module.check_mode:
                try:
                    proxmox.cluster.notifications.matchers(name).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete matcher '%s': %s" % (name, str(e)))
        module.exit_json(changed=changed, **result)

    # state == present
    desired = build_api_params(params)

    if existing is None:
        changed = True
        if not module.check_mode:
            create_params = dict(name=name)
            create_params.update(desired)
            try:
                proxmox.cluster.notifications.matchers.post(**create_params)
            except Exception as e:
                module.fail_json(msg="Failed to create matcher '%s': %s" % (name, str(e)))
    else:
        update_params = {}
        for key, value in desired.items():
            current_val = existing.get(key, '')
            if str(current_val) != str(value):
                update_params[key] = value
        if update_params:
            changed = True
            if not module.check_mode:
                try:
                    proxmox.cluster.notifications.matchers(name).put(**update_params)
                except Exception as e:
                    module.fail_json(msg="Failed to update matcher '%s': %s" % (name, str(e)))

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
