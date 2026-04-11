#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_verify_job
short_description: Manage Proxmox Backup Server verification jobs
description:
  - Create, update, or remove backup verification jobs on a Proxmox Backup Server.
  - Verification jobs check the integrity of backup data.
  - Uses the C(/config/verify) API endpoint.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  job_id:
    description: Unique identifier for the verification job.
    type: str
    required: true
  store:
    description: The datastore to verify backups in.
    type: str
    required: true
  schedule:
    description: Cron schedule for the verification job.
    type: str
  ignore_verified:
    description: Whether to skip snapshots that have already been verified.
    type: bool
  outdated_after:
    description:
      - Number of days after which a previously verified snapshot is considered outdated
        and will be re-verified.
    type: int
  ns:
    description: Namespace to restrict verification to.
    type: str
  max_depth:
    description: Maximum namespace depth for recursive verification.
    type: int
  comment:
    description: Description for the verification job.
    type: str
  state:
    description: Whether the verification job should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create a weekly verification job
  sfulmer.proxmox.proxmox_pbs_verify_job:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    job_id: weekly-verify
    store: backups
    schedule: "weekly"
    ignore_verified: true
    outdated_after: 30
    comment: Weekly integrity verification
    state: present

- name: Remove a verification job
  sfulmer.proxmox.proxmox_pbs_verify_job:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    job_id: weekly-verify
    store: backups
    state: absent
'''

RETURN = r'''
job_id:
  description: The verification job ID that was managed.
  returned: always
  type: str
  sample: weekly-verify
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        job_id=dict(type='str', required=True),
        store=dict(type='str', required=True),
        schedule=dict(type='str'),
        ignore_verified=dict(type='bool'),
        outdated_after=dict(type='int'),
        ns=dict(type='str'),
        max_depth=dict(type='int'),
        comment=dict(type='str'),
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
        'ignore_verified': 'ignore-verified',
        'outdated_after': 'outdated-after',
        'max_depth': 'max-depth',
    }

    try:
        jobs = api.config.verify.get()
    except Exception as e:
        module.fail_json(msg="Failed to list verification jobs: %s" % str(e))

    existing = None
    for job in jobs:
        if job.get('id') == job_id:
            existing = job
            break

    changed = False
    result = dict(job_id=job_id, changed=False)

    config_keys = [
        'store', 'schedule', 'ignore_verified', 'outdated_after',
        'ns', 'max_depth', 'comment',
    ]

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.config.verify(job_id).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete verification job '%s': %s" % (job_id, str(e)))
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
                        api.config.verify(job_id).put(**update_params)
                    except Exception as e:
                        module.fail_json(
                            msg="Failed to update verification job '%s': %s" % (job_id, str(e))
                        )
                changed = True
        else:
            config['id'] = job_id
            if not module.check_mode:
                try:
                    api.config.verify.post(**config)
                except Exception as e:
                    module.fail_json(msg="Failed to create verification job '%s': %s" % (job_id, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
