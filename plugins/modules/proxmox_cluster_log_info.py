#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_cluster_log_info
short_description: Query cluster log entries from Proxmox VE
version_added: "1.0.0"
description:
  - Retrieve cluster log entries from the Proxmox VE cluster via the
    C(/cluster/log) API endpoint.
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
  max:
    description:
      - Maximum number of log entries to return.
    type: int
  since:
    description:
      - Only return entries since this UNIX timestamp.
    type: int
author:
  - sfulmer
'''

EXAMPLES = r'''
- name: Get recent cluster log entries
  sfulmer.proxmox.proxmox_cluster_log_info:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    max: 50
  register: cluster_logs

- name: Get cluster logs since a timestamp
  sfulmer.proxmox.proxmox_cluster_log_info:
    api_host: pve1.example.com
    api_user: root@pam
    api_password: secret
    since: 1704067200
  register: recent_logs
'''

RETURN = r'''
logs:
  description: List of cluster log entries.
  returned: success
  type: list
  elements: dict
  sample:
    - uid: "task-001"
      node: "pve1"
      msg: "VM 100 started"
      severity: "info"
      tag: "qmstart"
'''

from ansible_collections.sfulmer.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    argument_spec = dict(
        # Use 'max_entries' as param name since 'max' shadows the builtin
        max=dict(type='int'),
        since=dict(type='int'),
    )

    proxmox = ProxmoxModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    module = proxmox.module
    params = module.params

    api = proxmox.get_api()

    get_params = {}
    if params.get('max') is not None:
        get_params['max'] = params['max']
    if params.get('since') is not None:
        get_params['since'] = params['since']

    try:
        logs = api.cluster.log.get(**get_params)
    except Exception as e:
        module.fail_json(msg="Failed to query cluster log: %s" % str(e))

    module.exit_json(changed=False, logs=logs)


if __name__ == '__main__':
    main()
