#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_acl_info
short_description: List access control entries on Proxmox VE
version_added: "1.1.0"
description:
  - Retrieve the list of Access Control List (ACL) entries from Proxmox VE.
  - Returns path, roleid, type, ugid, and propagate for each ACL entry.
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
- name: List all ACLs
  stevefulme1.proxmox.proxmox_acl_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
  register: acls

- name: Display ACL entries
  ansible.builtin.debug:
    var: acls.resources
'''

RETURN = r'''
resources:
  description: List of ACL entries.
  returned: always
  type: list
  elements: dict
  sample:
    - path: "/vms/100"
      roleid: "PVEVMAdmin"
      type: "user"
      ugid: "admin@pve"
      propagate: 1
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
        acls = proxmox.access.acl.get()
    except Exception as e:
        module.fail_json(
            msg="Failed to list ACLs: {0}".format(str(e))
        )

    module.exit_json(changed=False, resources=acls)


if __name__ == '__main__':
    main()
