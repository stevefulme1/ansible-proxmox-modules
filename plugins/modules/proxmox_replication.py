#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_replication
short_description: Manage storage replication jobs in Proxmox VE
description:
  - Create, update, and delete storage replication jobs in a Proxmox VE cluster.
version_added: "1.0.0"
author:
  - sfulmer
options:
  rep_id:
    description:
      - The replication job ID in the format C(VMID-JOBNUM) (e.g. C(100-0)).
    type: str
    required: true
  target:
    description:
      - The target node for replication.
    type: str
    required: true
  schedule:
    description:
      - Replication schedule in cron-like format.
    type: str
    default: "*/15"
  rate:
    description:
      - Rate limit in MB/s for the replication job.
    type: float
  comment:
    description:
      - A description or comment for the replication job.
    type: str
  disable:
    description:
      - Whether to disable the replication job.
    type: bool
  remove_job:
    description:
      - How to handle the replicated data when removing the job.
      - C(local) keeps data on the target, C(full) removes it.
    type: str
    choices:
      - local
      - full
  state:
    description:
      - Whether the replication job should be present or absent.
    type: str
    default: present
    choices:
      - present
      - absent
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create a replication job
  stevefulme1.proxmox.proxmox_replication:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    rep_id: "100-0"
    target: pve2
    schedule: "*/15"
    rate: 10.0
    comment: "Replicate VM 100 to pve2"
    state: present

- name: Disable a replication job
  stevefulme1.proxmox.proxmox_replication:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    rep_id: "100-0"
    target: pve2
    disable: true
    state: present

- name: Remove a replication job
  stevefulme1.proxmox.proxmox_replication:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    rep_id: "100-0"
    target: pve2
    state: absent
'''

RETURN = r'''
rep_id:
  description: The replication job ID that was managed.
  type: str
  returned: always
  sample: "100-0"
msg:
  description: A human-readable result message.
  type: str
  returned: always
  sample: "Replication job '100-0' created successfully."
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import (
    ProxmoxModule,
)


REPL_PARAMS = ['target', 'schedule', 'rate', 'comment', 'disable']

PARAM_API_MAP = {
    'rep_id': 'id',
}


def _get_existing_job(module, rep_id):
    """Retrieve an existing replication job or return None."""
    try:
        return module.proxmox_request(
            'GET', 'cluster/replication/{0}'.format(rep_id),
        )
    except Exception:
        return None


def _build_api_params(module):
    """Build API parameters from module params, skipping None values."""
    params = {}
    for key in REPL_PARAMS:
        value = module.params.get(key)
        if value is None:
            continue
        api_key = PARAM_API_MAP.get(key, key)
        if isinstance(value, bool):
            params[api_key] = int(value)
        else:
            params[api_key] = value
    return params


def _needs_update(existing, desired):
    """Compare existing job config with desired params."""
    for key, value in desired.items():
        existing_value = existing.get(key)
        if existing_value is None and value is not None:
            return True
        if str(existing_value) != str(value):
            return True
    return False


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            rep_id=dict(type='str', required=True),
            target=dict(type='str', required=True),
            schedule=dict(type='str', default='*/15'),
            rate=dict(type='float'),
            comment=dict(type='str'),
            disable=dict(type='bool'),
            remove_job=dict(type='str', choices=['local', 'full']),
            state=dict(
                type='str', default='present',
                choices=['present', 'absent'],
            ),
        ),
        supports_check_mode=True,
    )

    rep_id = module.params['rep_id']
    state = module.params['state']
    remove_job = module.params.get('remove_job')

    existing = _get_existing_job(module, rep_id)
    changed = False

    if state == 'present':
        api_params = _build_api_params(module)
        if existing is None:
            changed = True
            msg = "Replication job '{0}' created successfully.".format(
                rep_id,
            )
            if not module.check_mode:
                api_params['id'] = rep_id
                api_params['type'] = 'local'
                module.proxmox_request(
                    'POST', 'cluster/replication', data=api_params,
                )
        else:
            if _needs_update(existing, api_params):
                changed = True
                msg = "Replication job '{0}' updated successfully.".format(
                    rep_id,
                )
                if not module.check_mode:
                    module.proxmox_request(
                        'PUT',
                        'cluster/replication/{0}'.format(rep_id),
                        data=api_params,
                    )
            else:
                msg = "Replication job '{0}' is already up to date.".format(
                    rep_id,
                )

    elif state == 'absent':
        if existing is not None:
            changed = True
            msg = "Replication job '{0}' deleted successfully.".format(
                rep_id,
            )
            if not module.check_mode:
                params = {}
                if remove_job:
                    params['keep'] = 1 if remove_job == 'local' else 0
                module.proxmox_request(
                    'DELETE',
                    'cluster/replication/{0}'.format(rep_id),
                    params=params,
                )
        else:
            msg = "Replication job '{0}' does not exist.".format(rep_id)

    module.exit_json(changed=changed, rep_id=rep_id, msg=msg)


if __name__ == '__main__':
    main()
