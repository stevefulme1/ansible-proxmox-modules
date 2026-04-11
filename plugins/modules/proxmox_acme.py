# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_acme
short_description: Order or renew ACME certificates on a Proxmox VE node
version_added: "0.1.0"
description:
  - Order or renew an ACME (Let's Encrypt) certificate on a Proxmox VE node.
  - This is an action module that triggers certificate ordering via the
    C(/nodes/{node}/certificates/acme/certificate) API endpoint.
  - The node must already have ACME account and domain configuration set up.
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
  node:
    description: Target Proxmox VE node name.
    type: str
    required: true
  force:
    description: Force certificate renewal even if the current certificate is not expiring soon.
    type: bool
    default: false
author:
  - "Proxmox Community (@proxmox-community)"
'''

EXAMPLES = r'''
- name: Order ACME certificate on node pve1
  proxmox_acme:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1

- name: Force renewal of ACME certificate
  proxmox_acme:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    force: true
'''

RETURN = r'''
task_id:
  description: The UPID of the ACME certificate order task.
  returned: success
  type: str
  sample: "UPID:pve1:00001234:00005678:6789ABCD:acmerenew::root@pam:"
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


def main():
    argument_spec = dict(
        api_host=dict(type='str', required=True),
        api_user=dict(type='str', required=True),
        api_password=dict(type='str', no_log=True),
        api_token_id=dict(type='str'),
        api_token_secret=dict(type='str', no_log=True),
        validate_certs=dict(type='bool', default=True),
        node=dict(type='str', required=True),
        force=dict(type='bool', default=False),
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
    node = params['node']

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

    result = dict(node=node)

    if module.check_mode:
        module.exit_json(changed=True, **result)

    order_params = {}
    if params['force']:
        order_params['force'] = 1

    try:
        task_id = proxmox.nodes(node).certificates.acme.certificate.put(**order_params)
        result['task_id'] = task_id
        result['changed'] = True
    except Exception as e:
        error_msg = str(e)
        # If the certificate is not due for renewal and force is not set,
        # the API may return an error indicating no renewal is needed.
        if 'not due' in error_msg.lower() and not params['force']:
            module.exit_json(changed=False, msg="Certificate is not due for renewal.", **result)
        else:
            module.fail_json(msg="Failed to order ACME certificate on node '%s': %s" % (node, error_msg))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
