# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_notification_endpoint
short_description: Manage notification endpoints in Proxmox VE
version_added: "0.1.0"
description:
  - Create, update, or remove notification endpoints in Proxmox VE.
  - Supports sendmail, SMTP, Gotify, and webhook endpoint types.
  - Uses the C(/cluster/notifications/endpoints/{type}) API endpoints.
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
    description: Unique name for the notification endpoint.
    type: str
    required: true
  endpoint_type:
    description:
      - The type of notification endpoint.
      - Required when I(state=present).
    type: str
    choices: ['sendmail', 'smtp', 'gotify', 'webhook']
  mailto:
    description:
      - List of email addresses to send notifications to.
      - Used with C(sendmail) and C(smtp) endpoint types.
    type: list
    elements: str
  mailto_user:
    description:
      - List of Proxmox VE users to send notifications to.
      - Used with C(sendmail) endpoint type.
    type: list
    elements: str
  server:
    description:
      - SMTP server hostname or IP address.
      - Used with C(smtp) endpoint type.
    type: str
  port:
    description:
      - SMTP server port.
      - Used with C(smtp) endpoint type.
    type: int
  username:
    description:
      - SMTP authentication username.
      - Used with C(smtp) endpoint type.
    type: str
  password:
    description:
      - SMTP authentication password.
      - Used with C(smtp) endpoint type.
    type: str
  from_address:
    description:
      - Sender email address.
      - Used with C(sendmail) and C(smtp) endpoint types.
    type: str
  url:
    description:
      - URL for the endpoint.
      - Used with C(gotify) and C(webhook) endpoint types.
    type: str
  token:
    description:
      - Authentication token for the Gotify server.
      - Used with C(gotify) endpoint type.
    type: str
  secret:
    description:
      - Secret for webhook authentication.
      - Used with C(webhook) endpoint type.
    type: str
  body:
    description:
      - Template for the webhook request body.
      - Used with C(webhook) endpoint type.
    type: str
  comment:
    description: Description/comment for the endpoint.
    type: str
  state:
    description: Whether the notification endpoint should be present or absent.
    type: str
    choices: ['present', 'absent']
    default: present
author:
  - "Proxmox Community (@proxmox-community)"
'''

EXAMPLES = r'''
- name: Create a sendmail notification endpoint
  proxmox_notification_endpoint:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    name: admin-mail
    endpoint_type: sendmail
    mailto:
      - admin@example.com
    from_address: pve@example.com
    state: present

- name: Create an SMTP notification endpoint
  proxmox_notification_endpoint:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    name: smtp-relay
    endpoint_type: smtp
    server: smtp.example.com
    port: 587
    username: notifications@example.com
    password: smtppassword
    mailto:
      - ops@example.com
    from_address: pve-alerts@example.com
    state: present

- name: Create a Gotify notification endpoint
  proxmox_notification_endpoint:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    name: gotify-alerts
    endpoint_type: gotify
    url: https://gotify.example.com
    token: "app-token-here"
    state: present

- name: Create a webhook notification endpoint
  proxmox_notification_endpoint:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    name: slack-webhook
    endpoint_type: webhook
    url: https://hooks.slack.com/services/xxx
    body: '{"text": "{{message}}"}'
    state: present

- name: Remove a notification endpoint
  proxmox_notification_endpoint:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    name: old-endpoint
    state: absent
'''

RETURN = r'''
name:
  description: The name of the notification endpoint.
  returned: success
  type: str
  sample: "admin-mail"
endpoint_type:
  description: The type of the notification endpoint.
  returned: when state is present
  type: str
  sample: "sendmail"
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False

# Endpoint types and their API paths
ENDPOINT_TYPES = ['sendmail', 'smtp', 'gotify', 'webhook']

# Parameters relevant to each endpoint type
TYPE_PARAMS = {
    'sendmail': ['mailto', 'mailto_user', 'from_address', 'comment'],
    'smtp': ['mailto', 'server', 'port', 'username', 'password', 'from_address', 'comment'],
    'gotify': ['url', 'token', 'comment'],
    'webhook': ['url', 'secret', 'body', 'comment'],
}

# Parameters that map to different API keys
PARAM_TO_API = {
    'from_address': 'from-address',
    'mailto_user': 'mailto-user',
}


def get_endpoint_api(proxmox, endpoint_type):
    """Return the API resource for the given endpoint type."""
    return getattr(proxmox.cluster.notifications.endpoints, endpoint_type)


def find_existing_endpoint(proxmox, name):
    """Search all endpoint types for an endpoint with the given name.

    Returns (endpoint_type, config_dict) or (None, None).
    """
    for etype in ENDPOINT_TYPES:
        try:
            api = get_endpoint_api(proxmox, etype)
            endpoints = api.get()
            for ep in endpoints:
                if ep.get('name') == name:
                    return etype, ep
        except Exception:
            continue
    return None, None


def build_endpoint_params(params, endpoint_type):
    """Build API parameter dict from module params for the given endpoint type."""
    api_params = {}
    for param in TYPE_PARAMS.get(endpoint_type, []):
        value = params.get(param)
        if value is None:
            continue
        api_key = PARAM_TO_API.get(param, param)
        if isinstance(value, list):
            value = ','.join(value)
        api_params[api_key] = value
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
        endpoint_type=dict(type='str', choices=ENDPOINT_TYPES),
        mailto=dict(type='list', elements='str'),
        mailto_user=dict(type='list', elements='str'),
        server=dict(type='str'),
        port=dict(type='int'),
        username=dict(type='str'),
        password=dict(type='str', no_log=True),
        from_address=dict(type='str'),
        url=dict(type='str'),
        token=dict(type='str', no_log=True),
        secret=dict(type='str', no_log=True),
        body=dict(type='str'),
        comment=dict(type='str'),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['api_password', 'api_token_id']],
        required_together=[['api_token_id', 'api_token_secret']],
        required_if=[
            ['state', 'present', ['endpoint_type']],
        ],
    )

    if not HAS_PROXMOXER:
        module.fail_json(msg="proxmoxer library is required. Install it with: pip install proxmoxer")

    params = module.params
    state = params['state']
    name = params['name']
    endpoint_type = params.get('endpoint_type')

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

    existing_type, existing = find_existing_endpoint(proxmox, name)
    changed = False
    result = dict(name=name)

    if state == 'absent':
        if existing is not None:
            changed = True
            if not module.check_mode:
                try:
                    api = get_endpoint_api(proxmox, existing_type)
                    api(name).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete endpoint '%s': %s" % (name, str(e)))
        module.exit_json(changed=changed, **result)

    # state == present
    result['endpoint_type'] = endpoint_type
    desired = build_endpoint_params(params, endpoint_type)

    if existing is None:
        changed = True
        if not module.check_mode:
            create_params = dict(name=name)
            create_params.update(desired)
            try:
                api = get_endpoint_api(proxmox, endpoint_type)
                api.post(**create_params)
            except Exception as e:
                module.fail_json(msg="Failed to create endpoint '%s': %s" % (name, str(e)))
    else:
        # If type changed, we need to delete and recreate
        if existing_type != endpoint_type:
            changed = True
            if not module.check_mode:
                try:
                    old_api = get_endpoint_api(proxmox, existing_type)
                    old_api(name).delete()
                except Exception as e:
                    module.fail_json(
                        msg="Failed to delete old endpoint '%s' for type change: %s" % (name, str(e))
                    )
                create_params = dict(name=name)
                create_params.update(desired)
                try:
                    new_api = get_endpoint_api(proxmox, endpoint_type)
                    new_api.post(**create_params)
                except Exception as e:
                    module.fail_json(msg="Failed to recreate endpoint '%s': %s" % (name, str(e)))
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
                        api = get_endpoint_api(proxmox, endpoint_type)
                        api(name).put(**update_params)
                    except Exception as e:
                        module.fail_json(
                            msg="Failed to update endpoint '%s': %s" % (name, str(e))
                        )

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
