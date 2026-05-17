#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_backup_info
short_description: Query backup job configurations on Proxmox VE
version_added: "1.0.0"
description:
  - Retrieve information about scheduled backup jobs configured on a Proxmox VE cluster.
  - This is an info module and does not make any changes.
author:
  - sfulmer
options: {}
  limit:
    description:
      - Maximum number of results to return.
      - Applied client-side to truncate results.
    type: int
    default: 100
  offset:
    description:
      - Number of results to skip before returning.
      - Applied client-side for pagination.
    type: int
    default: 0
  max_results:
    description:
      - Maximum total number of results to return.
      - Set to 0 for no limit.
    type: int
    default: 1000
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: List all backup jobs
  stevefulme1.proxmox.proxmox_backup_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
  register: backup_jobs

- name: Display backup jobs
  ansible.builtin.debug:
    var: backup_jobs.backup_jobs
'''

RETURN = r'''
backup_jobs:
  description: List of backup job configurations.
  returned: always
  type: list
  elements: dict
  sample:
    - id: "backup-daily"
      storage: "nfs-backup"
      dow: "mon,tue,wed,thu,fri"
      starttime: "02:00"
      mode: "snapshot"
      enabled: 1
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            limit=dict(type='int', default=100),
            offset=dict(type='int', default=0),
            max_results=dict(type='int', default=1000),),
        supports_check_mode=True,
    )

    proxmox = module.proxmox_api()

    try:
        jobs = proxmox.cluster.backup.get()
    except Exception as e:
        module.fail_json(msg="Failed to list backup jobs: {0}".format(str(e)))

    module.exit_json(changed=False, backup_jobs=jobs)


if __name__ == '__main__':
    main()
