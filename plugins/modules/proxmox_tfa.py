#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_tfa
short_description: Manage two-factor authentication in Proxmox VE
description:
  - Add and remove two-factor authentication entries for users in Proxmox VE.
  - Supports TOTP, U2F, WebAuthn, Yubico, and recovery key types.
  - Creating a TOTP entry returns the secret and provisioning URL.
version_added: "1.0.0"
author:
  - sfulmer
options:
  userid:
    description:
      - The user ID to manage TFA for (e.g. C(user@pam)).
    type: str
    required: true
  tfa_type:
    description:
      - The type of TFA entry to manage.
    type: str
    required: true
    choices:
      - totp
      - u2f
      - webauthn
      - yubico
      - recovery
  description:
    description:
      - A description for the TFA entry.
    type: str
  password:
    description:
      - The user's current password, required for verification.
    type: str
    no_log: true
  tfa_id:
    description:
      - The TFA entry ID. Required when deleting a specific TFA entry.
    type: str
  state:
    description:
      - Whether the TFA entry should be present or absent.
    type: str
    default: present
    choices:
      - present
      - absent
extends_documentation_fragment:
  - sfulmer.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Add a TOTP entry for a user
  sfulmer.proxmox.proxmox_tfa:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    userid: admin@pve
    tfa_type: totp
    description: "Admin TOTP"
    password: userpassword
    state: present
  register: tfa_result

- name: Add recovery keys for a user
  sfulmer.proxmox.proxmox_tfa:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    userid: admin@pve
    tfa_type: recovery
    description: "Recovery keys"
    password: userpassword
    state: present

- name: Remove a specific TFA entry
  sfulmer.proxmox.proxmox_tfa:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    userid: admin@pve
    tfa_type: totp
    tfa_id: my-tfa-id
    state: absent
'''

RETURN = r'''
tfa_entry:
  description: The TFA entry data returned by the API (e.g. TOTP secret/URL).
  type: dict
  returned: when state is present and entry is created
  sample:
    secret: JBSWY3DPEHPK3PXP
    url: "otpauth://totp/proxmox:admin@pve?secret=JBSWY3DPEHPK3PXP&issuer=proxmox"
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "TFA entry created for user 'admin@pve'."
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


def _get_tfa_entries(module, userid):
    """Get existing TFA entries for a user."""
    try:
        return module.proxmox_request(
            'GET', 'access/tfa/{0}'.format(userid),
        )
    except Exception:
        return []


def _tfa_type_exists(entries, tfa_type, tfa_id=None):
    """Check if a TFA entry of the given type (and optionally ID) exists."""
    for entry in entries:
        if tfa_id and entry.get('id') == tfa_id:
            return True
        if not tfa_id and entry.get('type') == tfa_type:
            return True
    return False


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            userid=dict(type='str', required=True),
            tfa_type=dict(
                type='str', required=True,
                choices=['totp', 'u2f', 'webauthn', 'yubico', 'recovery'],
            ),
            description=dict(type='str'),
            password=dict(type='str', no_log=True),
            tfa_id=dict(type='str'),
            state=dict(
                type='str', default='present',
                choices=['present', 'absent'],
            ),
        ),
        required_if=[
            ('state', 'absent', ['tfa_id']),
        ],
        supports_check_mode=True,
    )

    userid = module.params['userid']
    tfa_type = module.params['tfa_type']
    description = module.params.get('description')
    password = module.params.get('password')
    tfa_id = module.params.get('tfa_id')
    state = module.params['state']

    entries = _get_tfa_entries(module, userid)
    changed = False
    tfa_entry = {}

    if state == 'present':
        # TFA entries are additive; always create a new one unless
        # an exact type+description match is found.
        already_exists = False
        for entry in entries:
            if (entry.get('type') == tfa_type
                    and description
                    and entry.get('description') == description):
                already_exists = True
                break

        if already_exists:
            msg = (
                "TFA entry of type '{0}' with description '{1}' "
                "already exists for user '{2}'."
            ).format(tfa_type, description, userid)
        else:
            changed = True
            if not module.check_mode:
                data = {'type': tfa_type}
                if description:
                    data['description'] = description
                if password:
                    data['password'] = password
                result = module.proxmox_request(
                    'POST',
                    'access/tfa/{0}'.format(userid),
                    data=data,
                )
                if result:
                    tfa_entry = result
            msg = "TFA entry created for user '{0}'.".format(userid)

    elif state == 'absent':
        if _tfa_type_exists(entries, tfa_type, tfa_id):
            changed = True
            if not module.check_mode:
                module.proxmox_request(
                    'DELETE',
                    'access/tfa/{0}/{1}'.format(userid, tfa_id),
                )
            msg = "TFA entry '{0}' removed for user '{1}'.".format(
                tfa_id, userid,
            )
        else:
            msg = "TFA entry '{0}' not found for user '{1}'.".format(
                tfa_id, userid,
            )

    result = dict(changed=changed, msg=msg)
    if tfa_entry:
        result['tfa_entry'] = tfa_entry
    module.exit_json(**result)


if __name__ == '__main__':
    main()
