#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_ha_resource_info
short_description: List HA resources on Proxmox VE
version_added: "1.1.0"
description:
  - Retrieve the list of High Availability resources configured on a Proxmox VE cluster.
  - Returns sid, state, group, max_relocate, and max_restart for each resource.
  - This is an info module and does not make any changes.
author:
  - sfulmer
options: {}
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: List all HA resources
  stevefulme1.proxmox.proxmox_ha_resource_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
  register: ha_resources

- name: Display HA resources
  ansible.builtin.debug:
    var: ha_resources.resources
'''

RETURN = r'''
resources:
  description: List of HA resources.
  returned: always
  type: list
  elements: dict
  sample:
    - sid: "vm:100"
      state: "started"
      group: "ha-group1"
      max_relocate: 1
      max_restart: 1
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(),
        supports_check_mode=True,
    )

    proxmox = module.proxmox_api()

    try:
        resources = proxmox.cluster.ha.resources.get()
    except Exception as e:
        module.fail_json(
            msg="Failed to list HA resources: {0}".format(str(e))
        )

    module.exit_json(changed=False, resources=resources)


if __name__ == '__main__':
    main()
