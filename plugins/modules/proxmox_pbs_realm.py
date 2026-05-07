#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_realm
short_description: Manage Proxmox Backup Server authentication realms
description:
  - Create, update, or remove authentication realms on a Proxmox Backup Server.
  - Uses the C(/access/domains) API endpoint.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  realm:
    description: The realm name/ID.
    type: str
    required: true
  type:
    description:
      - The realm type.
      - Required when creating a new realm.
    type: str
    choices: ['pam', 'pbs', 'ldap', 'ad', 'openid']
  default:
    description: Whether this realm is the default authentication realm.
    type: bool
  comment:
    description: Description for the realm.
    type: str
  server1:
    description: Primary server address (for LDAP/AD realms).
    type: str
  server2:
    description: Fallback server address (for LDAP/AD realms).
    type: str
  port:
    description: Server port (for LDAP/AD realms).
    type: int
  base_dn:
    description: LDAP base DN for user searches.
    type: str
  bind_dn:
    description: LDAP bind DN for authentication.
    type: str
  domain:
    description: AD domain name.
    type: str
  client_id:
    description: OAuth2 client ID (for OpenID Connect realms).
    type: str
  issuer_url:
    description: OpenID Connect issuer URL.
    type: str
  state:
    description: Whether the realm should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create an LDAP realm
  stevefulme1.proxmox.proxmox_pbs_realm:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    realm: company-ldap
    type: ldap
    server1: ldap.example.com
    base_dn: "dc=example,dc=com"
    bind_dn: "cn=admin,dc=example,dc=com"
    comment: Company LDAP directory
    state: present

- name: Create an OpenID Connect realm
  stevefulme1.proxmox.proxmox_pbs_realm:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    realm: keycloak
    type: openid
    issuer_url: "https://keycloak.example.com/realms/pbs"
    client_id: pbs-client
    comment: Keycloak SSO
    state: present

- name: Remove a realm
  stevefulme1.proxmox.proxmox_pbs_realm:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    realm: company-ldap
    state: absent
'''

RETURN = r'''
realm:
  description: The realm name that was managed.
  returned: always
  type: str
  sample: company-ldap
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        realm=dict(type='str', required=True),
        type=dict(type='str', choices=['pam', 'pbs', 'ldap', 'ad', 'openid']),
        default=dict(type='bool'),
        comment=dict(type='str'),
        server1=dict(type='str'),
        server2=dict(type='str'),
        port=dict(type='int'),
        base_dn=dict(type='str'),
        bind_dn=dict(type='str'),
        domain=dict(type='str'),
        client_id=dict(type='str'),
        issuer_url=dict(type='str'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    realm = params['realm']
    state = params['state']

    api_key_map = {
        'base_dn': 'base-dn',
        'bind_dn': 'bind-dn',
        'client_id': 'client-id',
        'issuer_url': 'issuer-url',
    }

    try:
        domains = api.access.domains.get()
    except Exception as e:
        module.fail_json(msg="Failed to list realms: %s" % str(e))

    existing = None
    for d in domains:
        if d.get('realm') == realm:
            existing = d
            break

    changed = False
    result = dict(realm=realm, changed=False)

    config_keys = [
        'type', 'default', 'comment', 'server1', 'server2', 'port',
        'base_dn', 'bind_dn', 'domain', 'client_id', 'issuer_url',
    ]

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.access.domains(realm).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete realm '%s': %s" % (realm, str(e)))
            changed = True
    else:
        config = {}
        for key in config_keys:
            if params.get(key) is not None:
                api_key = api_key_map.get(key, key)
                value = params[key]
                if isinstance(value, bool):
                    value = int(value)
                config[api_key] = value

        if existing:
            update_params = {}
            for api_key, value in config.items():
                # Skip 'type' on updates as it cannot be changed
                if api_key == 'type':
                    continue
                if str(existing.get(api_key, '')) != str(value):
                    update_params[api_key] = value
            if update_params:
                if not module.check_mode:
                    try:
                        api.access.domains(realm).put(**update_params)
                    except Exception as e:
                        module.fail_json(msg="Failed to update realm '%s': %s" % (realm, str(e)))
                changed = True
        else:
            if not params.get('type'):
                module.fail_json(msg="'type' is required when creating a new realm.")
            config['realm'] = realm
            if not module.check_mode:
                try:
                    api.access.domains.post(**config)
                except Exception as e:
                    module.fail_json(msg="Failed to create realm '%s': %s" % (realm, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
