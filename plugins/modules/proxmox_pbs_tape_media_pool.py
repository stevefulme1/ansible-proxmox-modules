#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_tape_media_pool
short_description: Manage Proxmox Backup Server tape media pools
description:
  - Create, update, or remove tape media pool configurations on a Proxmox Backup Server.
  - Uses the C(/config/tape/media-pool) API endpoint.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  name:
    description: The media pool name.
    type: str
    required: true
  allocation:
    description: Media allocation policy for new media sets.
    type: str
    choices: ['continue', 'always']
  retention:
    description:
      - Retention policy for media sets (e.g. C(keep-last 3) or a time duration).
    type: str
  template:
    description: Whether the pool is a template pool.
    type: bool
  encrypt:
    description: Encryption key fingerprint to encrypt data written to tapes in this pool.
    type: str
  comment:
    description: Description for the media pool.
    type: str
  state:
    description: Whether the media pool should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create a tape media pool
  sfulmer.proxmox.proxmox_pbs_tape_media_pool:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: weekly-pool
    allocation: always
    retention: "4 weeks"
    comment: Weekly tape rotation pool
    state: present

- name: Remove a tape media pool
  sfulmer.proxmox.proxmox_pbs_tape_media_pool:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: weekly-pool
    state: absent
'''

RETURN = r'''
name:
  description: The media pool name that was managed.
  returned: always
  type: str
  sample: weekly-pool
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        allocation=dict(type='str', choices=['continue', 'always']),
        retention=dict(type='str'),
        template=dict(type='bool'),
        encrypt=dict(type='str'),
        comment=dict(type='str'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    name = params['name']
    state = params['state']

    try:
        pools = api.config.tape('media-pool').get()
    except Exception as e:
        module.fail_json(msg="Failed to list tape media pools: %s" % str(e))

    existing = None
    for pool in pools:
        if pool.get('name') == name:
            existing = pool
            break

    changed = False
    result = dict(name=name, changed=False)

    config_keys = ['allocation', 'retention', 'template', 'encrypt', 'comment']

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.config.tape('media-pool')(name).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete media pool '%s': %s" % (name, str(e)))
            changed = True
    else:
        config = {}
        for key in config_keys:
            if params.get(key) is not None:
                value = params[key]
                if isinstance(value, bool):
                    value = int(value)
                config[key] = value

        if existing:
            update_params = {}
            for api_key, value in config.items():
                if str(existing.get(api_key, '')) != str(value):
                    update_params[api_key] = value
            if update_params:
                if not module.check_mode:
                    try:
                        api.config.tape('media-pool')(name).put(**update_params)
                    except Exception as e:
                        module.fail_json(msg="Failed to update media pool '%s': %s" % (name, str(e)))
                changed = True
        else:
            config['name'] = name
            if not module.check_mode:
                try:
                    api.config.tape('media-pool').post(**config)
                except Exception as e:
                    module.fail_json(msg="Failed to create media pool '%s': %s" % (name, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
