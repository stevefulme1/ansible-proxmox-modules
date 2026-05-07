#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, sfulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: proxmox_lxc_snapshot
short_description: Manage LXC container snapshots on Proxmox VE
version_added: "1.0.0"
description:
  - Create, delete, or rollback snapshots of LXC containers on Proxmox VE.
author:
  - sfulmer
options:
  node:
    description:
      - The Proxmox VE node on which the container resides.
    type: str
    required: true
  vmid:
    description:
      - The unique ID of the container.
    type: int
    required: true
  snapname:
    description:
      - The name of the snapshot.
    type: str
    required: true
  description:
    description:
      - Description for the snapshot.
    type: str
  state:
    description:
      - C(present) creates the snapshot if it does not exist.
      - C(absent) deletes the snapshot if it exists.
      - C(rollback) rolls back the container to the named snapshot.
    type: str
    choices: ['present', 'absent', 'rollback']
    default: present
extends_documentation_fragment:
  - stevefulme1.proxmox.proxmox
'''

EXAMPLES = r'''
- name: Create a snapshot
  stevefulme1.proxmox.proxmox_lxc_snapshot:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    snapname: before_upgrade
    description: Snapshot before package upgrade

- name: Delete a snapshot
  stevefulme1.proxmox.proxmox_lxc_snapshot:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    snapname: before_upgrade
    state: absent

- name: Rollback to a snapshot
  stevefulme1.proxmox.proxmox_lxc_snapshot:
    api_host: proxmox.example.com
    api_user: root@pam
    api_password: secret
    node: pve1
    vmid: 100
    snapname: before_upgrade
    state: rollback
'''

RETURN = r'''
vmid:
  description: The container ID.
  returned: always
  type: int
  sample: 100
snapname:
  description: The snapshot name.
  returned: always
  type: str
  sample: before_upgrade
task_id:
  description: The Proxmox task ID for the operation.
  returned: on change
  type: str
'''

from ansible_collections.stevefulme1.proxmox.plugins.module_utils.proxmox import ProxmoxModule


def main():
    module = ProxmoxModule(
        argument_spec=dict(
            node=dict(type='str', required=True),
            vmid=dict(type='int', required=True),
            snapname=dict(type='str', required=True),
            description=dict(type='str'),
            state=dict(type='str', choices=['present', 'absent', 'rollback'], default='present'),
        ),
        supports_check_mode=True,
    )

    node = module.params['node']
    vmid = module.params['vmid']
    snapname = module.params['snapname']
    description = module.params['description']
    state = module.params['state']

    proxmox = module.proxmox_api()

    try:
        snapshots = proxmox.nodes(node).lxc(vmid).snapshot.get()
    except Exception as e:
        module.fail_json(msg="Failed to list snapshots for container {0}: {1}".format(vmid, str(e)))

    snap_exists = any(s.get('name') == snapname for s in snapshots)

    if state == 'present':
        if snap_exists:
            module.exit_json(changed=False, vmid=vmid, snapname=snapname)

        if module.check_mode:
            module.exit_json(changed=True, vmid=vmid, snapname=snapname)

        try:
            params = dict(snapname=snapname)
            if description is not None:
                params['description'] = description
            task_id = proxmox.nodes(node).lxc(vmid).snapshot.post(**params)
        except Exception as e:
            module.fail_json(msg="Failed to create snapshot '{0}': {1}".format(snapname, str(e)))

        module.exit_json(changed=True, vmid=vmid, snapname=snapname, task_id=task_id)

    elif state == 'absent':
        if not snap_exists:
            module.exit_json(changed=False, vmid=vmid, snapname=snapname)

        if module.check_mode:
            module.exit_json(changed=True, vmid=vmid, snapname=snapname)

        try:
            task_id = proxmox.nodes(node).lxc(vmid).snapshot(snapname).delete()
        except Exception as e:
            module.fail_json(msg="Failed to delete snapshot '{0}': {1}".format(snapname, str(e)))

        module.exit_json(changed=True, vmid=vmid, snapname=snapname, task_id=task_id)

    elif state == 'rollback':
        if not snap_exists:
            module.fail_json(msg="Snapshot '{0}' does not exist on container {1}".format(snapname, vmid))

        if module.check_mode:
            module.exit_json(changed=True, vmid=vmid, snapname=snapname)

        try:
            task_id = proxmox.nodes(node).lxc(vmid).snapshot(snapname).rollback.post()
        except Exception as e:
            module.fail_json(msg="Failed to rollback to snapshot '{0}': {1}".format(snapname, str(e)))

        module.exit_json(changed=True, vmid=vmid, snapname=snapname, task_id=task_id)


if __name__ == '__main__':
    main()
