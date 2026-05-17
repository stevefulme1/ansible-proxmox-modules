#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_schedule
short_description: Manage PBS backup schedules
description:
  - Create, update, or remove backup schedules on a Proxmox Backup Server.
  - Uses the C(/config/datastore/{store}/backup-schedule) API endpoint.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  id:
    description: The schedule ID.
    type: str
    required: true
  store:
    description: The datastore name for the schedule.
    type: str
    required: true
  schedule:
    description:
      - Schedule expression in cron or systemd calendar format.
      - Required when creating a new schedule.
    type: str
  comment:
    description: Description or comment for the schedule.
    type: str
  ns:
    description: Backup namespace to use.
    type: str
  keep_last:
    description: Number of most recent backups to keep.
    type: int
  keep_hourly:
    description: Number of hourly backups to keep.
    type: int
  keep_daily:
    description: Number of daily backups to keep.
    type: int
  keep_weekly:
    description: Number of weekly backups to keep.
    type: int
  keep_monthly:
    description: Number of monthly backups to keep.
    type: int
  keep_yearly:
    description: Number of yearly backups to keep.
    type: int
  mail_notification:
    description: When to send email notifications.
    type: str
    choices: ['always', 'error', 'never']
  notification_mode:
    description: Notification delivery mode.
    type: str
    choices: ['legacy-sendmail', 'notification-system']
  state:
    description: Whether the schedule should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create a PBS backup schedule
  stevefulme1.proxmox.proxmox_pbs_schedule:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    id: daily-backup
    store: backups
    schedule: "daily"
    comment: "Daily backup at midnight"
    keep_daily: 7
    keep_weekly: 4
    state: present

- name: Remove a PBS backup schedule
  stevefulme1.proxmox.proxmox_pbs_schedule:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    id: daily-backup
    store: backups
    state: absent
'''

RETURN = r'''
id:
  description: The schedule ID that was managed.
  returned: always
  type: str
  sample: daily-backup
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        id=dict(type='str', required=True),
        store=dict(type='str', required=True),
        schedule=dict(type='str'),
        comment=dict(type='str'),
        ns=dict(type='str'),
        keep_last=dict(type='int'),
        keep_hourly=dict(type='int'),
        keep_daily=dict(type='int'),
        keep_weekly=dict(type='int'),
        keep_monthly=dict(type='int'),
        keep_yearly=dict(type='int'),
        mail_notification=dict(type='str', choices=['always', 'error', 'never']),
        notification_mode=dict(type='str', choices=['legacy-sendmail', 'notification-system']),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    schedule_id = params['id']
    store = params['store']
    state = params['state']

    # Fetch existing schedules
    try:
        schedules = api.config.datastore(store).get('backup-schedule')
    except Exception as e:
        module.fail_json(msg="Failed to list backup schedules: %s" % str(e))

    existing = None
    for s in schedules:
        if s.get('id') == schedule_id:
            existing = s
            break

    changed = False
    result = dict(id=schedule_id, changed=False)

    optional_params = [
        'schedule', 'comment', 'ns', 'keep_last', 'keep_hourly', 'keep_daily',
        'keep_weekly', 'keep_monthly', 'keep_yearly', 'mail_notification',
        'notification_mode',
    ]
    api_key_map = {
        'keep_last': 'keep-last',
        'keep_hourly': 'keep-hourly',
        'keep_daily': 'keep-daily',
        'keep_weekly': 'keep-weekly',
        'keep_monthly': 'keep-monthly',
        'keep_yearly': 'keep-yearly',
        'mail_notification': 'mail-notification',
        'notification_mode': 'notification-mode',
    }

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.config.datastore(store).delete('backup-schedule', schedule_id)
                except Exception as e:
                    module.fail_json(msg="Failed to delete schedule '%s': %s" % (schedule_id, str(e)))
            changed = True
    else:
        config = {}
        for key in optional_params:
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
                        api.config.datastore(store).put('backup-schedule', schedule_id, **update_params)
                    except Exception as e:
                        module.fail_json(msg="Failed to update schedule '%s': %s" % (schedule_id, str(e)))
                changed = True
        else:
            if not params.get('schedule'):
                module.fail_json(msg="'schedule' is required when creating a new backup schedule.")
            config['id'] = schedule_id
            if not module.check_mode:
                try:
                    api.config.datastore(store).post('backup-schedule', **config)
                except Exception as e:
                    module.fail_json(msg="Failed to create schedule '%s': %s" % (schedule_id, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
