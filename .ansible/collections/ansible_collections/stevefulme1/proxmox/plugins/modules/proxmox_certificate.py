# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_certificate
short_description: Manage custom SSL certificates on Proxmox VE nodes
version_added: "0.1.0"
description:
  - Upload or remove custom SSL certificates on a Proxmox VE node.
  - Uses the C(/nodes/{node}/certificates/custom) API endpoint.
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
  certificates:
    description:
      - PEM-encoded certificate chain.
      - Required when I(state=present).
    type: str
  key:
    description:
      - PEM-encoded private key.
      - Required when I(state=present).
    type: str
  force:
    description: Force upload even if the certificate has not changed.
    type: bool
    default: false
  restart:
    description: Restart pveproxy after uploading the certificate.
    type: bool
    default: false
  state:
    description: Whether the custom certificate should be present or absent.
    type: str
    choices: ['present', 'absent']
    default: present
author:
  - "Proxmox Community (@proxmox-community)"
'''

EXAMPLES = r'''
- name: Upload a custom SSL certificate
  proxmox_certificate:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    certificates: "{{ lookup('file', '/path/to/cert.pem') }}"
    key: "{{ lookup('file', '/path/to/key.pem') }}"
    restart: true
    state: present

- name: Remove custom SSL certificate
  proxmox_certificate:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    state: absent
'''

RETURN = r'''
fingerprint:
  description: The fingerprint of the uploaded certificate.
  returned: when state is present and changed
  type: str
  sample: "AB:CD:EF:01:23:45:67:89:AB:CD:EF:01:23:45:67:89:AB:CD:EF:01"
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from proxmoxer import ProxmoxAPI
    HAS_PROXMOXER = True
except ImportError:
    HAS_PROXMOXER = False


def get_current_cert_info(proxmox, node):
    """Return list of certificate info dicts for the node."""
    try:
        return proxmox.nodes(node).certificates.info.get()
    except Exception:
        return []


def main():
    argument_spec = dict(
        api_host=dict(type='str', required=True),
        api_user=dict(type='str', required=True),
        api_password=dict(type='str', no_log=True),
        api_token_id=dict(type='str'),
        api_token_secret=dict(type='str', no_log=True),
        validate_certs=dict(type='bool', default=True),
        node=dict(type='str', required=True),
        certificates=dict(type='str'),
        key=dict(type='str', no_log=True),
        force=dict(type='bool', default=False),
        restart=dict(type='bool', default=False),
        state=dict(type='str', default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_one_of=[['api_password', 'api_token_id']],
        required_together=[['api_token_id', 'api_token_secret']],
        required_if=[
            ['state', 'present', ['certificates', 'key']],
        ],
    )

    if not HAS_PROXMOXER:
        module.fail_json(msg="proxmoxer library is required. Install it with: pip install proxmoxer")

    params = module.params
    state = params['state']
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

    changed = False
    result = dict(node=node)

    # Check for existing custom certificate
    cert_info = get_current_cert_info(proxmox, node)
    has_custom = False
    current_fingerprint = None
    for cert in cert_info:
        if cert.get('filename', '') == 'pveproxy-ssl.pem':
            has_custom = True
            current_fingerprint = cert.get('fingerprint', '')
            break

    if state == 'absent':
        if has_custom:
            changed = True
            if not module.check_mode:
                try:
                    proxmox.nodes(node).certificates.custom.delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete custom certificate on node '%s': %s" % (node, str(e)))
        module.exit_json(changed=changed, **result)

    # state == present
    if not has_custom or params['force']:
        changed = True
    else:
        # Certificate exists, we would need to compare fingerprints to detect change.
        # Since we don't have a way to compute the fingerprint of the provided cert
        # without additional libraries, we upload if force is set or if no custom cert exists.
        # With an existing cert and no force, we still upload (the API is idempotent).
        changed = True

    if changed and not module.check_mode:
        upload_params = dict(
            certificates=params['certificates'],
            key=params['key'],
        )
        if params['force']:
            upload_params['force'] = 1
        if params['restart']:
            upload_params['restart'] = 1
        try:
            resp = proxmox.nodes(node).certificates.custom.post(**upload_params)
            if isinstance(resp, dict):
                result['fingerprint'] = resp.get('fingerprint', '')
        except Exception as e:
            module.fail_json(msg="Failed to upload certificate on node '%s': %s" % (node, str(e)))

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
