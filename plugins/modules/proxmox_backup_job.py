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
  - sfulmer
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
  dow:
    description:
      - Days of the week to run the backup, comma-separated (e.g. C(mon,wed,fri)).
    type: str
  starttime:
    description:
      - Start time for the backup job in C(HH:MM) format.
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
    dow: mon,tue,wed,thu,fri
    starttime: "02:00"
    mode: snapshot
    compress: zstd
    mailnotification: failure
    mailto: admin@example.com
    maxfiles: 7
    enabled: true
    state: present

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
    module = ProxmoxModule(
        argument_spec=dict(
            job_id=dict(type='str', required=True),
            vmid=dict(type='str'),
            storage=dict(type='str'),
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
        supports_check_mode=True,
    )

    job_id = module.params['job_id']
    state = module.params['state']

    proxmox = module.proxmox_api()

    config_params = [
        'vmid', 'storage', 'dow', 'starttime', 'mode', 'compress',
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
        if module.check_mode:
            module.exit_json(changed=True, job_id=job_id)

        try:
            proxmox.cluster.backup.post(**job_params)
        except Exception as e:
            module.fail_json(msg="Failed to create backup job '{0}': {1}".format(job_id, str(e)))

        module.exit_json(changed=True, job_id=job_id, job=job_params)
    else:
        # Check if update is needed
        changes = {}
        for param in config_params:
            value = module.params[param]
            if value is None:
                continue
            current_value = existing_job.get(param)
            if isinstance(value, bool):
                api_value = 1 if value else 0
                if current_value != api_value:
                    changes[param] = api_value
            else:
                if str(current_value) != str(value):
                    changes[param] = value

        if not changes:
            module.exit_json(changed=False, job_id=job_id, job=existing_job)

        if module.check_mode:
            module.exit_json(changed=True, job_id=job_id, job=existing_job, changes=changes)

        try:
            proxmox.cluster.backup(job_id).put(**changes)
        except Exception as e:
            module.fail_json(msg="Failed to update backup job '{0}': {1}".format(job_id, str(e)))

        updated_job = existing_job.copy()
        updated_job.update(changes)
        module.exit_json(changed=True, job_id=job_id, job=updated_job)


if __name__ == '__main__':
    main()
