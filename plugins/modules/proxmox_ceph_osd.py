#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_ceph_osd
short_description: Manage Proxmox VE Ceph OSDs
description:
  - Create and destroy Ceph Object Storage Daemons (OSDs) on Proxmox VE nodes.
  - Uses the C(/nodes/{node}/ceph/osd) API endpoints.
  - Creation requires a device path. Deletion requires an OSD ID.
version_added: "1.0.0"
author:
  - sfulmer
options:
  node:
    description:
      - The name of the Proxmox VE node where the OSD runs.
    type: str
    required: true
  osdid:
    description:
      - The OSD ID number.
      - Required when I(state=absent).
    type: int
  dev:
    description:
      - The block device path to use for the OSD.
      - Required when I(state=present).
    type: str
  db_dev:
    description:
      - Block device path for the OSD database (BlueStore DB).
    type: str
  wal_dev:
    description:
      - Block device path for the OSD write-ahead log (BlueStore WAL).
    type: str
  encrypted:
    description:
      - Whether to encrypt the OSD using dm-crypt.
    type: bool
  crush_device_class:
    description:
      - CRUSH device class for the OSD (e.g., ssd, hdd, nvme).
    type: str
  state:
    description:
      - Whether the Ceph OSD should exist or not.
    type: str
    choices: ['present', 'absent']
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create a Ceph OSD on /dev/sdb
  stevefulme1.proxmox.proxmox_ceph_osd:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    dev: /dev/sdb

- name: Create an encrypted OSD with separate DB and WAL devices
  stevefulme1.proxmox.proxmox_ceph_osd:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    dev: /dev/sdb
    db_dev: /dev/nvme0n1p1
    wal_dev: /dev/nvme0n1p2
    encrypted: true
    crush_device_class: ssd

- name: Remove OSD 3
  stevefulme1.proxmox.proxmox_ceph_osd:
    api_host: proxmox.example.com
    api_user: root@pam
    api_token_id: mytoken
    api_token_secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    node: pve1
    osdid: 3
    state: absent
'''

RETURN = r'''
osdid:
  description: The OSD ID.
  type: int
  returned: always
osds:
  description: List of existing Ceph OSDs after the operation.
  type: list
  elements: dict
  returned: success
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            osdid=dict(type='int'),
            dev=dict(type='str'),
            db_dev=dict(type='str'),
            wal_dev=dict(type='str'),
            encrypted=dict(type='bool'),
            crush_device_class=dict(type='str'),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
        ),
        required_if=[
            ('state', 'present', ['dev']),
            ('state', 'absent', ['osdid']),
        ],
        supports_check_mode=True,
    )

    node = module.params['node']
    state = module.params['state']

    # Get list of existing OSDs
    try:
        osd_data = module.proxmox_api.nodes(node).ceph.osd.get()
    except Exception as e:
        module.fail_json(msg="Failed to list Ceph OSDs on node '{0}': {1}".format(node, e))

    osd_list = osd_data if isinstance(osd_data, list) else osd_data.get('root', {}).get('children', [])

    if state == 'present':
        dev = module.params['dev']

        # Check if an OSD already exists on this device
        for osd in osd_list:
            osd_devices = osd.get('devices', '')
            if dev in str(osd_devices):
                module.exit_json(
                    changed=False,
                    osdid=osd.get('id'),
                    osds=osd_list,
                )

        if module.check_mode:
            module.exit_json(changed=True, osdid=None, osds=osd_list)

        create_params = {'dev': dev}
        if module.params.get('db_dev'):
            create_params['db_dev'] = module.params['db_dev']
        if module.params.get('wal_dev'):
            create_params['wal_dev'] = module.params['wal_dev']
        if module.params.get('encrypted') is not None:
            create_params['encrypted'] = int(module.params['encrypted'])
        if module.params.get('crush_device_class'):
            create_params['crush-device-class'] = module.params['crush_device_class']

        try:
            result = module.proxmox_api.nodes(node).ceph.osd.post(**create_params)
        except Exception as e:
            module.fail_json(
                msg="Failed to create Ceph OSD on device '{0}' on node '{1}': {2}".format(
                    dev, node, e
                )
            )

        try:
            osd_data = module.proxmox_api.nodes(node).ceph.osd.get()
            osd_list = (
                osd_data if isinstance(osd_data, list)
                else osd_data.get('root', {}).get('children', [])
            )
        except Exception:
            pass

        module.exit_json(changed=True, osdid=result, osds=osd_list)

    # state == absent
    osdid = module.params['osdid']

    existing = None
    for osd in osd_list:
        if osd.get('id') == osdid:
            existing = osd
            break

    if existing is None:
        module.exit_json(changed=False, osdid=osdid, osds=osd_list)

    if module.check_mode:
        module.exit_json(changed=True, osdid=osdid, osds=osd_list)

    try:
        module.proxmox_api.nodes(node).ceph.osd(osdid).delete()
    except Exception as e:
        module.fail_json(
            msg="Failed to delete Ceph OSD '{0}' on node '{1}': {2}".format(osdid, node, e)
        )

    try:
        osd_data = module.proxmox_api.nodes(node).ceph.osd.get()
        osd_list = (
            osd_data if isinstance(osd_data, list)
            else osd_data.get('root', {}).get('children', [])
        )
    except Exception:
        osd_list = []

    module.exit_json(changed=True, osdid=osdid, osds=osd_list)


if __name__ == '__main__':
    main()
