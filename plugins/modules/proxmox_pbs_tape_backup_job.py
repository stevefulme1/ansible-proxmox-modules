#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_tape_backup_job
short_description: Manage Proxmox Backup Server tape backup jobs
description:
  - Create, update, or remove tape backup jobs on a Proxmox Backup Server.
  - Tape backup jobs write datastore contents to tape media.
  - Uses the C(/config/tape-backup-job) API endpoint.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  job_id:
    description: Unique identifier for the tape backup job.
    type: str
    required: true
  store:
    description: The datastore to back up to tape.
    type: str
    required: true
  pool:
    description: The tape media pool to write to.
    type: str
    required: true
  drive:
    description: The tape drive to use.
    type: str
    required: true
  schedule:
    description: Cron schedule for the tape backup job.
    type: str
  eject_media:
    description: Whether to eject the tape after the backup completes.
    type: bool
  export_media_set:
    description: Whether to export the media set after the backup completes.
    type: bool
  ns:
    description: Namespace to restrict the tape backup to.
    type: str
  comment:
    description: Description for the tape backup job.
    type: str
  state:
    description: Whether the tape backup job should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create a tape backup job
  stevefulme1.proxmox.proxmox_pbs_tape_backup_job:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    job_id: nightly-tape
    store: backups
    pool: weekly-pool
    drive: drive0
    schedule: "daily"
    eject_media: true
    comment: Nightly tape backup
    state: present

- name: Remove a tape backup job
  stevefulme1.proxmox.proxmox_pbs_tape_backup_job:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    job_id: nightly-tape
    store: backups
    pool: weekly-pool
    drive: drive0
    state: absent
'''

RETURN = r'''
job_id:
  description: The tape backup job ID that was managed.
  returned: always
  type: str
  sample: nightly-tape
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        job_id=dict(type='str', required=True),
        store=dict(type='str', required=True),
        pool=dict(type='str', required=True),
        drive=dict(type='str', required=True),
        schedule=dict(type='str'),
        eject_media=dict(type='bool'),
        export_media_set=dict(type='bool'),
        ns=dict(type='str'),
        comment=dict(type='str'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    job_id = params['job_id']
    state = params['state']

    api_key_map = {
        'job_id': 'id',
        'eject_media': 'eject-media',
        'export_media_set': 'export-media-set',
    }

    try:
        jobs = api('config/tape-backup-job').get()
    except Exception as e:
        module.fail_json(msg="Failed to list tape backup jobs: %s" % str(e))

    existing = None
    for job in jobs:
        if job.get('id') == job_id:
            existing = job
            break

    changed = False
    result = dict(job_id=job_id, changed=False)

    config_keys = [
        'store', 'pool', 'drive', 'schedule', 'eject_media',
        'export_media_set', 'ns', 'comment',
    ]

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api('config/tape-backup-job/{0}'.format(job_id)).delete()
                except Exception as e:
                    module.fail_json(
                        msg="Failed to delete tape backup job '%s': %s" % (job_id, str(e))
                    )
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
                if str(existing.get(api_key, '')) != str(value):
                    update_params[api_key] = value
            if update_params:
                if not module.check_mode:
                    try:
                        api('config/tape-backup-job/{0}'.format(job_id)).put(**update_params)
                    except Exception as e:
                        module.fail_json(
                            msg="Failed to update tape backup job '%s': %s" % (job_id, str(e))
                        )
                changed = True
        else:
            config['id'] = job_id
            if not module.check_mode:
                try:
                    api('config/tape-backup-job').post(**config)
                except Exception as e:
                    module.fail_json(
                        msg="Failed to create tape backup job '%s': %s" % (job_id, str(e))
                    )
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
