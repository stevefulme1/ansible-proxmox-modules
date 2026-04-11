#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_task_info
short_description: Query task information on Proxmox VE nodes
version_added: "1.0.0"
description:
  - Retrieve task status or list tasks on a Proxmox VE node via the
    C(/nodes/{node}/tasks) API endpoint.
  - When C(upid) is provided, returns the status of that specific task.
  - When C(upid) is omitted, lists tasks matching the given filter criteria.
  - This is an info module and does not make any changes.
options:
  api_host:
    description: Proxmox VE API host (hostname or IP).
    type: str
    required: true
  api_user:
    description: Proxmox VE API user (e.g. C(root@pam)).
    type: str
    required: true
  api_password:
    description: Password for API user.
    type: str
  api_token_id:
    description: API token ID.
    type: str
  api_token_secret:
    description: API token secret.
    type: str
  validate_certs:
    description: Whether to validate SSL certificates.
    type: bool
    default: true
  node:
    description: Target Proxmox VE node name.
    type: str
    required: true
  upid:
    description:
      - Unique process ID of a specific task to query.
      - When provided, returns detailed status for that task only.
    type: str
  source:
    description:
      - Filter tasks by source.
    type: str
    choices: ['active', 'archive']
  start:
    description:
      - Start index for task listing (pagination).
    type: int
  limit:
    description:
      - Maximum number of tasks to return.
    type: int
  vmid:
    description:
      - Filter tasks by VM ID.
    type: int
  typefilter:
    description:
      - Filter tasks by type string (e.g. C(qmstart), C(vzdump)).
    type: str
author:
  - sfulmer
'''

EXAMPLES = r'''
- name: Get status of a specific task
  sfulmer.proxmox.proxmox_task_info:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    upid: "UPID:pve1:00001234:5678ABCD:01234567:qmstart:100:root@pam:"
  register: task_status

- name: List active tasks
  sfulmer.proxmox.proxmox_task_info:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    source: active
  register: active_tasks

- name: List recent vzdump tasks for VM 100
  sfulmer.proxmox.proxmox_task_info:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    typefilter: vzdump
    limit: 10
  register: backup_tasks
'''

RETURN = r'''
task:
  description: Task status details (when upid is provided).
  returned: when upid is provided
  type: dict
  sample:
    status: "stopped"
    exitstatus: "OK"
    type: "qmstart"
tasks:
  description: List of tasks (when upid is not provided).
  returned: when upid is not provided
  type: list
  elements: dict
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    argument_spec = dict(
        node=dict(type='str', required=True),
        upid=dict(type='str'),
        source=dict(type='str', choices=['active', 'archive']),
        start=dict(type='int'),
        limit=dict(type='int'),
        vmid=dict(type='int'),
        typefilter=dict(type='str'),
    )

    proxmox = ProxmoxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module = proxmox.module
    params = module.params
    node = params['node']

    api = proxmox.get_api()

    if params.get('upid'):
        # Get specific task status
        try:
            task = api.nodes(node).tasks(params['upid']).status.get()
        except Exception as e:
            module.fail_json(
                msg="Failed to query task '%s' on node '%s': %s"
                % (params['upid'], node, str(e)))
        module.exit_json(changed=False, task=task)
    else:
        # List tasks with filters
        get_params = {}
        if params.get('source'):
            get_params['source'] = params['source']
        if params.get('start') is not None:
            get_params['start'] = params['start']
        if params.get('limit') is not None:
            get_params['limit'] = params['limit']
        if params.get('vmid') is not None:
            get_params['vmid'] = params['vmid']
        if params.get('typefilter'):
            get_params['typefilter'] = params['typefilter']

        try:
            tasks = api.nodes(node).tasks.get(**get_params)
        except Exception as e:
            module.fail_json(
                msg="Failed to list tasks on node '%s': %s" % (node, str(e)))

        module.exit_json(changed=False, tasks=tasks)


if __name__ == '__main__':
    main()
