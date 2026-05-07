#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_prune_job
short_description: Manage Proxmox Backup Server prune jobs
description:
  - Create, update, or remove prune jobs on a Proxmox Backup Server.
  - Uses the C(/config/prune-job) API endpoint.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  job_id:
    description: Unique identifier for the prune job.
    type: str
    required: true
  store:
    description: The datastore the prune job operates on.
    type: str
    required: true
  schedule:
    description: Cron schedule for the prune job.
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
  ns:
    description: Namespace to restrict pruning to.
    type: str
  max_depth:
    description: Maximum namespace depth for recursive pruning.
    type: int
  comment:
    description: Description for the prune job.
    type: str
  disable:
    description: Whether the prune job is disabled.
    type: bool
  state:
    description: Whether the prune job should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create a daily prune job
  stevefulme1.proxmox.proxmox_pbs_prune_job:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    job_id: daily-prune
    store: backups
    schedule: "daily"
    keep_last: 3
    keep_daily: 7
    keep_weekly: 4
    keep_monthly: 6
    comment: Daily pruning of old backups
    state: present

- name: Remove a prune job
  stevefulme1.proxmox.proxmox_pbs_prune_job:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    job_id: daily-prune
    store: backups
    state: absent
'''

RETURN = r'''
job_id:
  description: The prune job ID that was managed.
  returned: always
  type: str
  sample: daily-prune
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        job_id=dict(type='str', required=True),
        store=dict(type='str', required=True),
        schedule=dict(type='str'),
        keep_last=dict(type='int'),
        keep_hourly=dict(type='int'),
        keep_daily=dict(type='int'),
        keep_weekly=dict(type='int'),
        keep_monthly=dict(type='int'),
        keep_yearly=dict(type='int'),
        ns=dict(type='str'),
        max_depth=dict(type='int'),
        comment=dict(type='str'),
        disable=dict(type='bool'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    job_id = params['job_id']
    store = params['store']
    state = params['state']

    api_key_map = {
        'job_id': 'id',
        'keep_last': 'keep-last',
        'keep_hourly': 'keep-hourly',
        'keep_daily': 'keep-daily',
        'keep_weekly': 'keep-weekly',
        'keep_monthly': 'keep-monthly',
        'keep_yearly': 'keep-yearly',
        'max_depth': 'max-depth',
    }

    # Fetch existing prune jobs
    try:
        jobs = api('config/prune-job').get()
    except Exception as e:
        module.fail_json(msg="Failed to list prune jobs: %s" % str(e))

    existing = None
    for job in jobs:
        if job.get('id') == job_id:
            existing = job
            break

    changed = False
    result = dict(job_id=job_id, changed=False)

    optional_keys = [
        'schedule', 'keep_last', 'keep_hourly', 'keep_daily', 'keep_weekly',
        'keep_monthly', 'keep_yearly', 'ns', 'max_depth', 'comment', 'disable',
    ]

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api('config/prune-job/{0}'.format(job_id)).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete prune job '%s': %s" % (job_id, str(e)))
            changed = True
    else:
        config = dict(store=store)
        for key in optional_keys:
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
                        api('config/prune-job/{0}'.format(job_id)).put(**update_params)
                    except Exception as e:
                        module.fail_json(msg="Failed to update prune job '%s': %s" % (job_id, str(e)))
                changed = True
        else:
            config['id'] = job_id
            if not module.check_mode:
                try:
                    api('config/prune-job').post(**config)
                except Exception as e:
                    module.fail_json(msg="Failed to create prune job '%s': %s" % (job_id, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
