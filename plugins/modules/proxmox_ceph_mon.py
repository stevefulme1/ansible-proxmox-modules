#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_ceph_mon
short_description: Manage Proxmox VE Ceph monitors
description:
  - Create and destroy Ceph monitor daemons on Proxmox VE nodes.
  - Uses the C(/nodes/{node}/ceph/mon) API endpoints.
  - Checks existing monitors before making changes to ensure idempotency.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The name of the Proxmox VE node where the monitor runs.
    type: str
    required: true
  monid:
    description:
      - The monitor ID.
      - Defaults to the node name if not specified.
    type: str
  mon_address:
    description:
      - The IP address for the Ceph monitor to bind to.
    type: str
  state:
    description:
      - Whether the Ceph monitor should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create a Ceph monitor on pve1
  stevefulme1.proxmox.proxmox_ceph_mon:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1

- name: Create a Ceph monitor with a custom ID and address
  stevefulme1.proxmox.proxmox_ceph_mon:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    monid: mon0
    mon_address: 10.0.0.10

- name: Remove a Ceph monitor
  stevefulme1.proxmox.proxmox_ceph_mon:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    monid: mon0
    state: absent
'''

RETURN = r'''
monid:
  description: The monitor ID.
  type: str
  returned: always
monitors:
  description: List of existing Ceph monitors after the operation.
  type: list
  elements: dict
  returned: success
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            monid=dict(type='str'),
            mon_address=dict(type='str'),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    monid = module.params.get('monid') or node
    state = module.params['state']

    # Get list of existing monitors
    try:
        monitors = module.proxmox_api.nodes(node).ceph.mon.get()
    except Exception as e:
        module.fail_json(msg="Failed to list Ceph monitors on node '{0}': {1}".format(node, e))

    existing = None
    for mon in monitors:
        if mon.get('name') == monid:
            existing = mon
            break

    if state == 'present':
        if existing is not None:
            module.exit_json(changed=False, monid=monid, monitors=monitors)

        if module.check_mode:
            module.exit_json(changed=True, monid=monid, monitors=monitors)

        create_params = {}
        if module.params.get('monid'):
            create_params['monid'] = monid
        if module.params.get('mon_address'):
            create_params['mon-address'] = module.params['mon_address']

        try:
            module.proxmox_api.nodes(node).ceph.mon.post(**create_params)
        except Exception as e:
            module.fail_json(
                msg="Failed to create Ceph monitor '{0}' on node '{1}': {2}".format(monid, node, e)
            )

        try:
            monitors = module.proxmox_api.nodes(node).ceph.mon.get()
        except Exception:
            pass

        module.exit_json(changed=True, monid=monid, monitors=monitors)

    # state == absent
    if existing is None:
        module.exit_json(changed=False, monid=monid, monitors=monitors)

    if module.check_mode:
        module.exit_json(changed=True, monid=monid, monitors=monitors)

    try:
        module.proxmox_api.nodes(node).ceph.mon(monid).delete()
    except Exception as e:
        module.fail_json(
            msg="Failed to delete Ceph monitor '{0}' on node '{1}': {2}".format(monid, node, e)
        )

    try:
        monitors = module.proxmox_api.nodes(node).ceph.mon.get()
    except Exception:
        monitors = []

    module.exit_json(changed=True, monid=monid, monitors=monitors)


if __name__ == '__main__':
    main()
