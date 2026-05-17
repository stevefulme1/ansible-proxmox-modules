#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_node_syslog_info
short_description: Query Proxmox VE node syslog entries
description:
  - Retrieve syslog entries from a Proxmox VE node.
  - Uses the C(/nodes/{node}/syslog) API endpoint with optional filtering parameters.
  - This is an info module and does not make any changes.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The name of the Proxmox VE node to query.
    type: str
    required: true
  start:
    description:
      - The line number to start from.
    type: int
  limit:
    description:
      - Maximum number of log entries to return.
    type: int
    default: 50
  since:
    description:
      - Display log entries since this date-time string.
      - Format should be C(YYYY-MM-DD) or C(YYYY-MM-DD HH:MM:SS).
    type: str
  until:
    description:
      - Display log entries until this date-time string.
      - Format should be C(YYYY-MM-DD) or C(YYYY-MM-DD HH:MM:SS).
    type: str
  service:
    description:
      - Filter log entries by service name.
    type: str
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
- name: Get last 50 syslog entries
  stevefulme1.proxmox.proxmox_node_syslog_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
  register: syslog

- name: Get syslog entries for a specific service
  stevefulme1.proxmox.proxmox_node_syslog_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    service: pveproxy
    limit: 100

- name: Get syslog entries within a time range
  stevefulme1.proxmox.proxmox_node_syslog_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    since: "2026-01-01"
    until: "2026-01-02"
    limit: 200
'''

RETURN = r'''
syslog:
  description: List of syslog entries.
  type: list
  elements: dict
  returned: always
  sample:
    - n: 1
      t: "Jan  1 00:00:00 pve1 systemd[1]: Started foo.service."
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            limit=dict(type='int', default=100),
            offset=dict(type='int', default=0),
            max_results=dict(type='int', default=1000),
            node=dict(type='str', required=True),
            start=dict(type='int'),
            limit=dict(type='int', default=50),
            since=dict(type='str'),
            until=dict(type='str'),
            service=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']

    params = {}
    for key in ('start', 'limit', 'since', 'until', 'service'):
        value = module.params.get(key)
        if value is not None:
            params[key] = value

    try:
        result = module.proxmox_api.nodes(node).syslog.get(**params)
    except Exception as e:
        module.fail_json(msg="Failed to get syslog for node '{0}': {1}".format(node, e))

    module.exit_json(changed=False, syslog=result)


if __name__ == '__main__':
    main()
