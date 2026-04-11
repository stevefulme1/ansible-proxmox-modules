#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_datastore
short_description: Manage Proxmox Backup Server datastores
description:
  - Create, update, or remove datastores on a Proxmox Backup Server.
  - Uses the C(/config/datastore) API endpoint.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  name:
    description: The datastore name.
    type: str
    required: true
  path:
    description:
      - Filesystem path for the datastore backing directory.
      - Required when creating a new datastore.
    type: str
  comment:
    description: Description or comment for the datastore.
    type: str
  gc_schedule:
    description: Garbage collection schedule in cron format.
    type: str
  keep_last:
    description: Number of most recent backups to keep during pruning.
    type: int
  keep_hourly:
    description: Number of hourly backups to keep during pruning.
    type: int
  keep_daily:
    description: Number of daily backups to keep during pruning.
    type: int
  keep_weekly:
    description: Number of weekly backups to keep during pruning.
    type: int
  keep_monthly:
    description: Number of monthly backups to keep during pruning.
    type: int
  keep_yearly:
    description: Number of yearly backups to keep during pruning.
    type: int
  prune_schedule:
    description: Automatic prune schedule in cron format.
    type: str
  verify_new:
    description: Whether to automatically verify new backups after completion.
    type: bool
  notify:
    description: Notification setting for the datastore.
    type: str
  notify_user:
    description: User to notify for datastore events.
    type: str
  state:
    description: Whether the datastore should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create a PBS datastore
  sfulmer.proxmox.proxmox_pbs_datastore:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: backups
    path: /mnt/datastore/backups
    comment: Primary backup datastore
    gc_schedule: "daily"
    keep_daily: 7
    keep_weekly: 4
    keep_monthly: 6
    verify_new: true
    state: present

- name: Update retention policy on a datastore
  sfulmer.proxmox.proxmox_pbs_datastore:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: backups
    keep_daily: 14
    keep_weekly: 8
    state: present

- name: Remove a PBS datastore
  sfulmer.proxmox.proxmox_pbs_datastore:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    name: backups
    state: absent
'''

RETURN = r'''
name:
  description: The datastore name that was managed.
  returned: always
  type: str
  sample: backups
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        name=dict(type='str', required=True),
        path=dict(type='str'),
        comment=dict(type='str'),
        gc_schedule=dict(type='str'),
        keep_last=dict(type='int'),
        keep_hourly=dict(type='int'),
        keep_daily=dict(type='int'),
        keep_weekly=dict(type='int'),
        keep_monthly=dict(type='int'),
        keep_yearly=dict(type='int'),
        prune_schedule=dict(type='str'),
        verify_new=dict(type='bool'),
        notify=dict(type='str'),
        notify_user=dict(type='str'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    name = params['name']
    state = params['state']

    # Fetch existing datastores
    try:
        datastores = api.config.datastore.get()
    except Exception as e:
        module.fail_json(msg="Failed to list datastores: %s" % str(e))

    existing = None
    for ds in datastores:
        if ds.get('name') == name:
            existing = ds
            break

    changed = False
    result = dict(name=name, changed=False)

    optional_params = [
        'comment', 'gc_schedule', 'keep_last', 'keep_hourly', 'keep_daily',
        'keep_weekly', 'keep_monthly', 'keep_yearly', 'prune_schedule',
        'verify_new', 'notify', 'notify_user',
    ]
    api_key_map = {
        'gc_schedule': 'gc-schedule',
        'keep_last': 'keep-last',
        'keep_hourly': 'keep-hourly',
        'keep_daily': 'keep-daily',
        'keep_weekly': 'keep-weekly',
        'keep_monthly': 'keep-monthly',
        'keep_yearly': 'keep-yearly',
        'prune_schedule': 'prune-schedule',
        'verify_new': 'verify-new',
        'notify_user': 'notify-user',
    }

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.config.datastore(name).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete datastore '%s': %s" % (name, str(e)))
            changed = True
    else:
        config = {}
        for key in optional_params:
            if params.get(key) is not None:
                api_key = api_key_map.get(key, key)
                value = params[key]
                if isinstance(value, bool):
                    value = int(value)
                config[api_key] = value

        if existing:
            update_params = {}
            for api_key, value in config.items():
                if str(existing.get(api_key, '')) != str(value):
                    update_params[api_key] = value
            if update_params:
                if not module.check_mode:
                    try:
                        api.config.datastore(name).put(**update_params)
                    except Exception as e:
                        module.fail_json(msg="Failed to update datastore '%s': %s" % (name, str(e)))
                changed = True
        else:
            if not params.get('path'):
                module.fail_json(msg="'path' is required when creating a new datastore.")
            config['name'] = name
            config['path'] = params['path']
            if not module.check_mode:
                try:
                    api.config.datastore.post(**config)
                except Exception as e:
                    module.fail_json(msg="Failed to create datastore '%s': %s" % (name, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
