#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_ceph_osd_info
short_description: List Ceph OSDs on a Proxmox VE node
version_added: "1.1.0"
description:
  - Retrieve the list of Ceph Object Storage Daemons (OSDs) on a Proxmox VE node.
  - Returns osd_id, name, status, crush_weight, and device_class for each OSD.
  - This is an info module and does not make any changes.
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node to query Ceph OSDs from.
    type: str
    required: true
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: List Ceph OSDs on a node
  stevefulme1.proxmox.proxmox_ceph_osd_info:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
  register: ceph_osds

- name: Display Ceph OSDs
  ansible.builtin.debug:
    var: ceph_osds.resources
'''

RETURN = r'''
resources:
  description: List of Ceph OSDs.
  returned: always
  type: list
  elements: dict
  sample:
    - id: 0
      name: "osd.0"
      status: "up"
      crush_weight: 0.87329
      device_class: "ssd"
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']

    proxmox = module.proxmox_api()

    try:
        result = proxmox.nodes(node).ceph.osd.get()
        # The API returns a dict with 'root' containing OSD tree data.
        # Extract the individual OSD entries from the tree.
        osds = []
        if isinstance(result, dict) and 'root' in result:
            root = result['root']
            for child in root.get('children', []):
                if child.get('type') == 'host':
                    for osd in child.get('children', []):
                        osds.append(osd)
                elif child.get('type') == 'osd':
                    osds.append(child)
        elif isinstance(result, list):
            osds = result
    except Exception as e:
        module.fail_json(
            msg="Failed to list Ceph OSDs on node '{0}': {1}".format(
                node, str(e)
            )
        )

    module.exit_json(changed=False, resources=osds)


if __name__ == '__main__':
    main()
