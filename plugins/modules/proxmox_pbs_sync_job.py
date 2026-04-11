#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_sync_job
short_description: Manage Proxmox Backup Server sync jobs
description:
  - Create, update, or remove sync jobs on a Proxmox Backup Server.
  - Sync jobs pull backups from a remote PBS instance to the local datastore.
  - Uses the C(/config/sync) API endpoint.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  job_id:
    description: Unique identifier for the sync job.
    type: str
    required: true
  store:
    description: The local datastore to sync backups into.
    type: str
    required: true
  remote:
    description: Name of the configured remote PBS server.
    type: str
    required: true
  remote_store:
    description: The datastore name on the remote PBS server.
    type: str
    required: true
  schedule:
    description: Cron schedule for the sync job.
    type: str
  ns:
    description: Namespace to sync into or from.
    type: str
  remove_vanished:
    description: Whether to remove local backups that no longer exist on the remote.
    type: bool
  owner:
    description: Owner of the synced backup groups.
    type: str
  comment:
    description: Description for the sync job.
    type: str
  max_depth:
    description: Maximum namespace depth for recursive syncing.
    type: int
  group_filter:
    description: Filter expression to limit which backup groups are synced.
    type: str
  rate_limit:
    description: Bandwidth rate limit for the sync operation (e.g. C(10mbit)).
    type: str
  state:
    description: Whether the sync job should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
'''

EXAMPLES = r'''
- name: Create a sync job from a remote PBS
  sfulmer.proxmox.proxmox_pbs_sync_job:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    job_id: sync-from-remote
    store: local-backups
    remote: offsite-pbs
    remote_store: backups
    schedule: "daily"
    remove_vanished: true
    rate_limit: "50mbit"
    comment: Nightly sync from offsite PBS
    state: present

- name: Remove a sync job
  sfulmer.proxmox.proxmox_pbs_sync_job:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    job_id: sync-from-remote
    store: local-backups
    remote: offsite-pbs
    remote_store: backups
    state: absent
'''

RETURN = r'''
job_id:
  description: The sync job ID that was managed.
  returned: always
  type: str
  sample: sync-from-remote
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        job_id=dict(type='str', required=True),
        store=dict(type='str', required=True),
        remote=dict(type='str', required=True),
        remote_store=dict(type='str', required=True),
        schedule=dict(type='str'),
        ns=dict(type='str'),
        remove_vanished=dict(type='bool'),
        owner=dict(type='str'),
        comment=dict(type='str'),
        max_depth=dict(type='int'),
        group_filter=dict(type='str'),
        rate_limit=dict(type='str'),
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
        'remote_store': 'remote-store',
        'remove_vanished': 'remove-vanished',
        'max_depth': 'max-depth',
        'group_filter': 'group-filter',
        'rate_limit': 'rate-limit',
    }

    try:
        jobs = api.config.sync.get()
    except Exception as e:
        module.fail_json(msg="Failed to list sync jobs: %s" % str(e))

    existing = None
    for job in jobs:
        if job.get('id') == job_id:
            existing = job
            break

    changed = False
    result = dict(job_id=job_id, changed=False)

    config_keys = [
        'store', 'remote', 'remote_store', 'schedule', 'ns',
        'remove_vanished', 'owner', 'comment', 'max_depth',
        'group_filter', 'rate_limit',
    ]

    if state == 'absent':
        if existing:
            if not module.check_mode:
                try:
                    api.config.sync(job_id).delete()
                except Exception as e:
                    module.fail_json(msg="Failed to delete sync job '%s': %s" % (job_id, str(e)))
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
                        api.config.sync(job_id).put(**update_params)
                    except Exception as e:
                        module.fail_json(msg="Failed to update sync job '%s': %s" % (job_id, str(e)))
                changed = True
        else:
            config['id'] = job_id
            if not module.check_mode:
                try:
                    api.config.sync.post(**config)
                except Exception as e:
                    module.fail_json(msg="Failed to create sync job '%s': %s" % (job_id, str(e)))
            changed = True

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
