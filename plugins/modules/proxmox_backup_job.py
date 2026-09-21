#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_backup_job
short_description: Manage scheduled backup jobs on Proxmox VE
version_added: "1.0.0"
description:
  - Create, update, or delete scheduled backup jobs on Proxmox VE.
  - Uses the C(/cluster/backup) API endpoint.
  - Matches existing jobs by C(job_id) for idempotent operations.
author:
  - Steve Fulmer (@stevefulme1)
options:
  job_id:
    description:
      - The unique identifier for the backup job.
      - Used to match existing jobs for idempotent create/update/delete operations.
    type: str
    required: true
  vmid:
    description:
      - Comma-separated list of VM IDs to back up, or C(all) for all VMs.
    type: str
  storage:
    description:
      - The storage location for backups.
    type: str
  schedule:
    description:
      - Backup schedule using a subset of systemd calendar events, for example C(mon..fri 02:00).
      - Mutually exclusive with O(starttime) and O(dow).
      - Either O(schedule) or O(starttime) is required when creating a job.
      - Omit scheduling options to preserve an existing job's schedule.
    type: str
  dow:
    description:
      - Days of the week to run the backup, comma-separated (e.g. C(mon,wed,fri)).
      - Legacy option; prefer O(schedule). Requires O(starttime) and cannot be used with O(schedule).
      - If omitted with O(starttime), the backup runs every day.
    type: str
  starttime:
    description:
      - Start time for the backup job in C(HH:MM) format.
      - Legacy option; prefer O(schedule). Cannot be used with O(schedule).
    type: str
  mode:
    description:
      - Backup mode.
    type: str
    choices: ['snapshot', 'suspend', 'stop']
  compress:
    description:
      - Compression algorithm for the backup.
    type: str
    choices: ['0', 'gzip', 'lzo', 'zstd']
  mailnotification:
    description:
      - When to send email notifications.
    type: str
    choices: ['always', 'failure']
  mailto:
    description:
      - Comma-separated list of email addresses to notify.
    type: str
  maxfiles:
    description:
      - Maximum number of backup files to keep. Use 0 for unlimited.
    type: int
  enabled:
    description:
      - Whether the backup job is enabled.
    type: bool
  notes_template:
    description:
      - Template for backup notes.
    type: str
  state:
    description:
      - C(present) ensures the backup job exists with the specified configuration.
      - C(absent) ensures the backup job is removed.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create a daily backup job
  stevefulme1.proxmox.proxmox_backup_job:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    job_id: backup-daily
    vmid: "100,101,102"
    storage: nfs-backup
    schedule: "02:00"
    mode: snapshot
    compress: zstd
    mailnotification: failure
    mailto: admin@example.com
    maxfiles: 7
    enabled: true
    state: present

- name: Create a weekday backup job using legacy scheduling
  stevefulme1.proxmox.proxmox_backup_job:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    job_id: backup-weekdays
    vmid: "100,101,102"
    storage: nfs-backup
    dow: mon,tue,wed,thu,fri
    starttime: "02:00"

- name: Remove a backup job
  stevefulme1.proxmox.proxmox_backup_job:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    job_id: backup-daily
    state: absent
'''

RETURN = r'''
job_id:
  description: The backup job identifier.
  returned: always
  type: str
  sample: backup-daily
job:
  description: The backup job configuration after changes.
  returned: success and state is present
  type: dict
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    proxmox_module = ProxmoxModule(
        argument_spec=dict(
            job_id=dict(type='str', required=True),
            vmid=dict(type='str'),
            storage=dict(type='str'),
            schedule=dict(type='str'),
            dow=dict(type='str'),
            starttime=dict(type='str'),
            mode=dict(type='str', choices=['snapshot', 'suspend', 'stop']),
            compress=dict(type='str', choices=['0', 'gzip', 'lzo', 'zstd']),
            mailnotification=dict(type='str', choices=['always', 'failure']),
            mailto=dict(type='str'),
            maxfiles=dict(type='int'),
            enabled=dict(type='bool'),
            notes_template=dict(type='str'),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
        ),
        required_if=[
            ('state', 'present', ['storage']),
        ],
        mutually_exclusive=[
            ('schedule', 'starttime'),
            ('schedule', 'dow'),
        ],
        supports_check_mode=True,
    )

    module = proxmox_module.module
    job_id = module.params['job_id']
    state = module.params['state']

    if module.params['dow'] is not None and module.params['starttime'] is None:
        module.fail_json(msg="dow requires starttime; alternatively use schedule")
    for param in ('schedule', 'starttime', 'dow'):
        value = module.params[param]
        if value is not None and not value.strip():
            module.fail_json(msg="{0} must not be empty".format(param))

    proxmox = proxmox_module.get_api()

    config_params = [
        'vmid', 'storage', 'schedule', 'dow', 'starttime', 'mode', 'compress',
        'mailnotification', 'mailto', 'maxfiles', 'enabled', 'notes_template',
    ]

    # List existing backup jobs and find ours
    try:
        jobs = proxmox.cluster.backup.get()
    except Exception as e:
        module.fail_json(msg="Failed to list backup jobs: {0}".format(str(e)))

    existing_job = None
    for job in jobs:
        if job.get('id') == job_id:
            existing_job = job
            break

    if state == 'absent':
        if existing_job is None:
            module.exit_json(changed=False, job_id=job_id)

        if module.check_mode:
            module.exit_json(changed=True, job_id=job_id)

        try:
            proxmox.cluster.backup(job_id).delete()
        except Exception as e:
            module.fail_json(msg="Failed to delete backup job '{0}': {1}".format(job_id, str(e)))

        module.exit_json(changed=True, job_id=job_id)

    # state == 'present'
    job_params = dict(id=job_id)
    for param in config_params:
        value = module.params[param]
        if value is not None:
            if isinstance(value, bool):
                job_params[param] = 1 if value else 0
            else:
                job_params[param] = value

    if existing_job is None:
        # Create new job
        if module.params['schedule'] is None and module.params['starttime'] is None:
            module.fail_json(msg="Either schedule or starttime is required when creating a backup job")
        if module.check_mode:
            module.exit_json(changed=True, job_id=job_id)

        try:
            proxmox.cluster.backup.post(**job_params)
        except Exception as e:
            module.fail_json(msg="Failed to create backup job '{0}': {1}".format(job_id, str(e)))

        module.exit_json(changed=True, job_id=job_id, job=job_params)
    else:
        # Modern Proxmox returns schedule even when legacy inputs were used.
        desired = {key: value for key, value in job_params.items() if key != 'id'}
        legacy_schedule = 'starttime' in desired and 'schedule' in existing_job
        if legacy_schedule:
            starttime = desired.pop('starttime')
            dow = desired.pop('dow', 'mon,tue,wed,thu,fri,sat,sun')
            # Match PVE::Tools::split_list: null separators take precedence,
            # otherwise commas, semicolons and whitespace separate entries.
            # Perl's split also discards trailing empty entries.
            if '\0' in dow:
                days = dow.rstrip('\0').split('\0')
            else:
                days = dow.replace(',', ' ').replace(';', ' ').split()
            dow = ','.join(days)
            desired['schedule'] = starttime if dow == 'mon,tue,wed,thu,fri,sat,sun' else '{0} {1}'.format(dow, starttime)

        changes = {key: value for key, value in desired.items()
                   if existing_job.get(key) != value and str(existing_job.get(key)) != str(value)}
        if legacy_schedule and 'schedule' in changes:
            del changes['schedule']
            changes['starttime'] = job_params['starttime']
            if 'dow' in job_params:
                changes['dow'] = job_params['dow']
        elif 'dow' in changes:
            # The legacy API requires starttime whenever dow is supplied.
            changes['starttime'] = job_params['starttime']

        if not changes:
            module.exit_json(changed=False, job_id=job_id, job=existing_job)

        if module.check_mode:
            module.exit_json(changed=True, job_id=job_id, job=existing_job, changes=changes)

        try:
            proxmox.cluster.backup(job_id).put(**changes)
        except Exception as e:
            module.fail_json(msg="Failed to update backup job '{0}': {1}".format(job_id, str(e)))

        updated_job = existing_job.copy()
        updated_job.update(desired)
        module.exit_json(changed=True, job_id=job_id, job=updated_job)


if __name__ == '__main__':
    main()
