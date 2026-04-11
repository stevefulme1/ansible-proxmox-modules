#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_remote
short_description: Manage Proxmox Backup Server remote connections
description:
  - Create, update, or remove remote PBS server configurations on a Proxmox Backup Server.
  - Remote connections are used by sync jobs to pull backups from other PBS instances.
  - Uses the C(/config/remote) API endpoint.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  name:
    description: Unique name for the remote PBS connection.
    type: str
    required: true
  host:
    description: Hostname or IP address of the remote PBS server.
    type: str
    required: true
  port:
    description: Port of the remote PBS API.
    type: int
    default: 8007
  auth_id:
    description:
      - Authentication ID for the remote PBS server in C(user@realm!token) format.
    type: str
    required: true
  password:
    description:
      - Password or API token secret for authenticating to the remote PBS server.
    type: str
    no_log: true
  fingerprint:
    description: TLS certificate fingerprint of the remote PBS server for verification.
    type: str
  comment:
    description: Description for the remote connection.
    type: str
  state:
    description: Whether the remote connection should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Configure a remote PBS connection
  sfulmer.proxmox.proxmox_pbs_remote:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: offsite-pbs
    host: offsite-pbs.example.com
    port: 8007
    auth_id: sync-user@pbs!sync-token
    password: remote-token-secret
    fingerprint: "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD"
    comment: Offsite backup server
    state: present

- name: Remove a remote PBS connection
  sfulmer.proxmox.proxmox_pbs_remote:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: offsite-pbs
    host: offsite-pbs.example.com
    auth_id: sync-user@pbs!sync-token
    state: absent
'''

RETURN = r'''
name:
  description: The remote connection name that was managed.
  returned: always
  type: str
  sample: offsite-pbs
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        host=dict(type='str', required=True),
        port=dict(type='int', default=8007),
        auth_id=dict(type='str', required=True),
        password=dict(type='str', no_log=True),
        fingerprint=dict(type='str'),
        comment=dict(type='str'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    name = params['name']
    state = params['state']

    api_key_map = {
        'auth_id': 'auth-id',
    }

    try:
        remotes = api.config.remote.get()
    except Exception as e:
        module.fail_json(msg="Failed to list remotes: %s" % str(e))

    existing = None
    for r in remotes:
        if r.get('name') == name:
            existing = r
            break

    changed = False
    result = dict(name=name, changed=False)

    config_keys = ['host', 'port', 'auth_id', 'fingerprint', 'comment']

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.config.remote(name).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete remote '%s': %s" % (name, str(e)))
            changed = True
    else:
        config = {}
        for key in config_keys:
            if params.get(key) is not None:
                api_key = api_key_map.get(key, key)
                config[api_key] = params[key]

        if existing:
            update_params = {}
            for api_key, value in config.items():
                if str(existing.get(api_key, '')) != str(value):
                    update_params[api_key] = value
            # Password cannot be compared, always include if provided
            if params.get('password'):
                update_params['password'] = params['password']
                changed = True
            if update_params:
                if not module.check_mode:
                    try:
                        api.config.remote(name).put(**update_params)
                    except Exception as e:
                        module.fail_json(msg="Failed to update remote '%s': %s" % (name, str(e)))
                changed = True
        else:
            config['name'] = name
            if params.get('password'):
                config['password'] = params['password']
            if not module.check_mode:
                try:
                    api.config.remote.post(**config)
                except Exception as e:
                    module.fail_json(msg="Failed to create remote '%s': %s" % (name, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
