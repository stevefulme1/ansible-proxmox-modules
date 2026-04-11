#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_realm
short_description: Manage authentication realms in Proxmox VE
description:
  - Create, update, and delete authentication realms (domains) in Proxmox VE.
  - Supports PAM, PVE, LDAP, Active Directory, and OpenID Connect realm types.
version_added: "1.0.0"
author:
  - sfulmer
options:
  realm:
    description:
      - The realm identifier (e.g. C(myldap), C(myad)).
    type: str
    required: true
  type:
    description:
      - The authentication realm type.
    type: str
    required: true
    choices:
      - pam
      - pve
      - ldap
      - ad
      - openid
  default:
    description:
      - Whether this realm is the default authentication realm.
    type: bool
  comment:
    description:
      - A description or comment for the realm.
    type: str
  base_dn:
    description:
      - Base Distinguished Name for LDAP/AD realms.
    type: str
  bind_dn:
    description:
      - Bind Distinguished Name for LDAP/AD realms.
    type: str
  server1:
    description:
      - Primary server address for LDAP/AD/OpenID realms.
    type: str
  server2:
    description:
      - Fallback server address for LDAP/AD realms.
    type: str
  port:
    description:
      - Server port for LDAP/AD realms.
    type: int
  secure:
    description:
      - Whether to use TLS/SSL for the connection.
    type: bool
  domain:
    description:
      - AD domain name. Used for Active Directory realms.
    type: str
  tfa:
    description:
      - Two-factor authentication configuration string.
    type: str
  issuer_url:
    description:
      - OpenID Connect issuer URL.
    type: str
  client_id:
    description:
      - OpenID Connect client ID.
    type: str
  client_key:
    description:
      - OpenID Connect client secret key.
    type: str
    no_log: true
  autocreate:
    description:
      - Automatically create users on login if they do not exist.
    type: bool
  state:
    description:
      - Whether the realm should be present or absent.
    type: str
    default: present
    choices:
      - present
      - absent
extends_documentation_fragment:
  - sfulmer.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create an LDAP realm
  sfulmer.proxmox.proxmox_realm:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    realm: myldap
    type: ldap
    server1: ldap.example.com
    base_dn: dc=example,dc=com
    bind_dn: cn=admin,dc=example,dc=com
    secure: true
    state: present

- name: Create an OpenID Connect realm
  sfulmer.proxmox.proxmox_realm:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    realm: myoidc
    type: openid
    issuer_url: https://auth.example.com
    client_id: proxmox
    client_key: supersecret
    autocreate: true
    state: present

- name: Remove a realm
  sfulmer.proxmox.proxmox_realm:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    realm: myldap
    state: absent
'''

RETURN = r'''
realm:
  description: The realm identifier that was managed.
  type: str
  returned: always
  sample: myldap
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "Realm 'myldap' created successfully."
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


REALM_PARAMS = [
    'type', 'default', 'comment', 'base_dn', 'bind_dn',
    'server1', 'server2', 'port', 'secure', 'domain', 'tfa',
    'issuer_url', 'client_id', 'client_key', 'autocreate',
]

PARAM_API_MAP = {
    'base_dn': 'base-dn',
    'bind_dn': 'bind-dn',
    'issuer_url': 'issuer-url',
    'client_id': 'client-id',
    'client_key': 'client-key',
}


def _build_api_params(module):
    """Build API parameters from module params, skipping None values."""
    params = {}
    for key in REALM_PARAMS:
        value = module.params.get(key)
        if value is None:
            continue
        api_key = PARAM_API_MAP.get(key, key)
        if isinstance(value, bool):
            params[api_key] = int(value)
        else:
            params[api_key] = value
    return params


def _get_existing_realm(module, realm):
    """Retrieve an existing realm or return None."""
    try:
        return module.proxmox_request('GET', 'access/domains/{0}'.format(realm))
    except Exception:
        return None


def _needs_update(existing, desired):
    """Compare existing realm config with desired params."""
    for key, value in desired.items():
        existing_value = existing.get(key)
        if existing_value is None and value is not None:
            return True
        if str(existing_value) != str(value):
            return True
    return False


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            realm=dict(type='str', required=True),
            type=dict(
                type='str', required=True,
                choices=['pam', 'pve', 'ldap', 'ad', 'openid'],
            ),
            default=dict(type='bool'),
            comment=dict(type='str'),
            base_dn=dict(type='str'),
            bind_dn=dict(type='str'),
            server1=dict(type='str'),
            server2=dict(type='str'),
            port=dict(type='int'),
            secure=dict(type='bool'),
            domain=dict(type='str'),
            tfa=dict(type='str'),
            issuer_url=dict(type='str'),
            client_id=dict(type='str'),
            client_key=dict(type='str', no_log=True),
            autocreate=dict(type='bool'),
            state=dict(
                type='str', default='present',
                choices=['present', 'absent'],
            ),
        ),
        supports_check_mode=True,
    )

    realm = module.params['realm']
    state = module.params['state']

    existing = _get_existing_realm(module, realm)
    changed = False
    msg = ''

    if state == 'present':
        api_params = _build_api_params(module)
        if existing is None:
            changed = True
            msg = "Realm '{0}' created successfully.".format(realm)
            if not module.check_mode:
                api_params['realm'] = realm
                module.proxmox_request('POST', 'access/domains', data=api_params)
        else:
            if _needs_update(existing, api_params):
                changed = True
                msg = "Realm '{0}' updated successfully.".format(realm)
                if not module.check_mode:
                    module.proxmox_request(
                        'PUT',
                        'access/domains/{0}'.format(realm),
                        data=api_params,
                    )
            else:
                msg = "Realm '{0}' is already up to date.".format(realm)
    elif state == 'absent':
        if existing is not None:
            changed = True
            msg = "Realm '{0}' deleted successfully.".format(realm)
            if not module.check_mode:
                module.proxmox_request(
                    'DELETE', 'access/domains/{0}'.format(realm),
                )
        else:
            msg = "Realm '{0}' does not exist.".format(realm)

    module.exit_json(changed=changed, realm=realm, msg=msg)


if __name__ == '__main__':
    main()
