#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_pbs_node_info
short_description: Query Proxmox Backup Server node status
description:
  - Retrieve node status information from a Proxmox Backup Server.
  - Returns CPU usage, memory usage, uptime, and other system metrics.
  - PBS is a single-node system so this queries the local node.
  - Uses the C(/nodes/localhost/status) API endpoint.
  - This is an info module that does not modify state.
  - Requires the proxmoxer Python library.
version_added: "1.0.0"
author:
  - sfulmer
'''

EXAMPLES = r'''
- name: Get PBS node status
  stevefulme1.proxmox.proxmox_pbs_node_info:
    api_host: pbs.example.com
    api_user: root@pam
    api_password: secret
  register: node_info

- name: Display CPU usage
  ansible.builtin.debug:
    msg: "CPU usage: {{ node_info.cpu }}"

- name: Display memory usage
  ansible.builtin.debug:
    msg: "Memory: {{ node_info.memory }}"
'''

RETURN = r'''
cpu:
  description: Current CPU usage as a fraction (0.0 to 1.0).
  returned: always
  type: float
  sample: 0.15
memory:
  description: Memory usage information.
  returned: always
  type: dict
uptime:
  description: System uptime in seconds.
  returned: always
  type: int
  sample: 86400
info:
  description: Full node status information from the API.
  returned: always
  type: dict
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module_args = dict()

    proxmox = ProxmoxModule(argument_spec=module_args)
    module = proxmox.module
    api = proxmox.get_api()

    result = dict(changed=False)

    try:
        status = api.nodes('localhost').status.get()
    except Exception as e:
        module.fail_json(msg="Failed to get node status: %s" % str(e))

    result['info'] = status
    result['cpu'] = status.get('cpu', 0)
    result['uptime'] = status.get('uptime', 0)
    result['memory'] = status.get('memory', {})

    module.exit_json(**result)


if __name__ == '__main__':
    main()
