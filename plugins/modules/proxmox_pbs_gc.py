#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_gc
short_description: Run or schedule garbage collection on a Proxmox Backup Server datastore
description:
  - Trigger an immediate garbage collection run or configure a GC schedule
    on a Proxmox Backup Server datastore.
  - Uses the C(/admin/datastore/{store}/gc) API endpoint for immediate runs
    and the datastore config for schedule updates.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  store:
    description: The datastore name to manage garbage collection for.
    type: str
    required: true
  schedule:
    description:
      - Cron schedule for automatic garbage collection.
      - Updates the datastore GC schedule configuration.
    type: str
  run_now:
    description:
      - Whether to trigger an immediate garbage collection run.
      - This is an action that always reports changed when executed.
    type: bool
    default: false
'''

EXAMPLES = r'''
- name: Set GC schedule on a datastore
  stevefulme1.proxmox.proxmox_pbs_gc:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    store: backups
    schedule: "daily"

- name: Run garbage collection immediately
  stevefulme1.proxmox.proxmox_pbs_gc:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    store: backups
    run_now: true

- name: Set schedule and run immediately
  stevefulme1.proxmox.proxmox_pbs_gc:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    store: backups
    schedule: "weekly"
    run_now: true
'''

RETURN = r'''
store:
  description: The datastore name.
  returned: always
  type: str
  sample: backups
task_id:
  description: The UPID of the garbage collection task when run_now is true.
  returned: when run_now is true and not in check mode
  type: str
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        store=dict(type='str', required=True),
        schedule=dict(type='str'),
        run_now=dict(type='bool', default=False),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    store = params['store']
    schedule = params.get('schedule')
    run_now = params['run_now']

    changed = False
    result = dict(store=store, changed=False)

    # Update schedule if provided
    if schedule is not None:
        try:
            ds_config = api.config.datastore(store).get()
        except Exception as e:
            module.fail_json(msg="Failed to get datastore '%s' config: %s" % (store, str(e)))

        current_schedule = ds_config.get('gc-schedule', '')
        if str(current_schedule) != schedule:
            if not module.check_mode:
                try:
                    api.config.datastore(store).put(**{'gc-schedule': schedule})
                except Exception as e:
                    module.fail_json(
                        msg="Failed to update GC schedule for datastore '%s': %s" % (store, str(e))
                    )
            changed = True

    # Trigger immediate GC if requested
    if run_now:
        changed = True
        if not module.check_mode:
            try:
                task_id = api.admin.datastore(store).gc.post()
                result['task_id'] = task_id
            except Exception as e:
                module.fail_json(
                    msg="Failed to start garbage collection on datastore '%s': %s" % (store, str(e))
                )

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
