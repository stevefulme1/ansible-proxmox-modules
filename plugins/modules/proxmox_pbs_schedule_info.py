#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_schedule_info
short_description: Get PBS backup schedule info
description:
  - Retrieve backup schedule configuration from a Proxmox Backup Server datastore.
  - Uses the C(/config/datastore/{store}/backup-schedule) API endpoint.
  - This is an info module that does not modify state.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
options:
  store:
    description: The datastore name to query schedules for.
    type: str
    required: true
  id:
    description:
      - Name of a specific schedule to query.
      - If not specified, all schedules for the datastore are returned.
    type: str
'''

EXAMPLES = r'''
- name: Get all backup schedules for a datastore
  stevefulme1.proxmox.proxmox_pbs_schedule_info:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    store: backups
  register: sched_info

- name: Get a specific schedule
  stevefulme1.proxmox.proxmox_pbs_schedule_info:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
    store: backups
    id: daily-backup
  register: sched_info

- name: Display schedule details
  ansible.builtin.debug:
    var: sched_info.schedules
'''

RETURN = r'''
schedules:
  description: List of backup schedule configurations.
  returned: always
  type: list
  elements: dict
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict(
        store=dict(type='str', required=True),
        id=dict(type='str'),
    )

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    params = module.params
    api = proxmox.get_api()

    store = params['store']
    schedule_id = params.get('id')
    result = dict(changed=False)

    try:
        schedules = api.config.datastore(store).get('backup-schedule')
    except Exception as e:
        module.fail_json(msg="Failed to list backup schedules: %s" % str(e))

    if schedule_id:
        filtered = [s for s in schedules if s.get('id') == schedule_id]
        if not filtered:
            module.fail_json(msg="Schedule '%s' not found in datastore '%s'." % (schedule_id, store))
        result['schedules'] = filtered
    else:
        result['schedules'] = schedules

    module.exit_json(**result)


if __name__ == '__main__':
    main()
