#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_ha_group_info
short_description: List HA groups on Proxmox VE
version_added: "1.1.0"
description:
  - Retrieve the list of High Availability groups configured on a Proxmox VE cluster.
  - Returns group, nodes, restricted, nofailback, and type for each group.
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
- name: List all HA groups
  stevefulme1.proxmox.proxmox_ha_group_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
  register: ha_groups

- name: Display HA groups
  ansible.builtin.debug:
    var: ha_groups.resources
'''

RETURN = r'''
resources:
  description: List of HA groups.
  returned: always
  type: list
  elements: dict
  sample:
    - group: "ha-group1"
      nodes: "pve1:1,pve2:1,pve3:1"
      restricted: 0
      nofailback: 0
      type: "group"
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
        groups = proxmox.cluster.ha.groups.get()
    except Exception as e:
        module.fail_json(
            msg="Failed to list HA groups: {0}".format(str(e))
        )

    module.exit_json(changed=False, resources=groups)


if __name__ == '__main__':
    main()
