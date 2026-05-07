#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_tape_drive
short_description: Manage Proxmox Backup Server tape drives
description:
  - Create, update, or remove tape drive configurations on a Proxmox Backup Server.
  - Uses the C(/config/tape/drive) API endpoint.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  name:
    description: The tape drive name.
    type: str
    required: true
  path:
    description:
      - Device path for the tape drive (e.g. C(/dev/nst0)).
      - Required when creating a new tape drive.
    type: str
  changer:
    description: Name of the associated tape changer/library.
    type: str
  changer_drivenum:
    description: Drive number within the tape changer.
    type: int
  state:
    description: Whether the tape drive should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Configure a tape drive
  stevefulme1.proxmox.proxmox_pbs_tape_drive:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: drive0
    path: /dev/nst0
    changer: library0
    changer_drivenum: 0
    state: present

- name: Remove a tape drive configuration
  stevefulme1.proxmox.proxmox_pbs_tape_drive:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: drive0
    state: absent
'''

RETURN = r'''
name:
  description: The tape drive name that was managed.
  returned: always
  type: str
  sample: drive0
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        path=dict(type='str'),
        changer=dict(type='str'),
        changer_drivenum=dict(type='int'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    name = params['name']
    state = params['state']

    api_key_map = {
        'changer_drivenum': 'changer-drivenum',
    }

    try:
        drives = api.config.tape.drive.get()
    except Exception as e:
        module.fail_json(msg="Failed to list tape drives: %s" % str(e))

    existing = None
    for drive in drives:
        if drive.get('name') == name:
            existing = drive
            break

    changed = False
    result = dict(name=name, changed=False)

    config_keys = ['path', 'changer', 'changer_drivenum']

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.config.tape.drive(name).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete tape drive '%s': %s" % (name, str(e)))
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
            if update_params:
                if not module.check_mode:
                    try:
                        api.config.tape.drive(name).put(**update_params)
                    except Exception as e:
                        module.fail_json(msg="Failed to update tape drive '%s': %s" % (name, str(e)))
                changed = True
        else:
            if not params.get('path'):
                module.fail_json(msg="'path' is required when creating a new tape drive.")
            config['name'] = name
            if not module.check_mode:
                try:
                    api.config.tape.drive.post(**config)
                except Exception as e:
                    module.fail_json(msg="Failed to create tape drive '%s': %s" % (name, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
